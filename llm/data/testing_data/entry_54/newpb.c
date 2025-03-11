

static void fuse_file_put(struct fuse_file *ff, bool sync)
{
	if (atomic_dec_and_test(&ff->count)) {
		struct fuse_req *req = ff->reserved_req;

		if (ff->fc->no_open) {
			/*
			 * Drop the release request when client does not
			 * implement 'open'
			 */
			__clear_bit(FR_BACKGROUND, &req->flags);
			iput(req->misc.release.inode);
			fuse_put_request(ff->fc, req);
		} else if (sync) {
			__set_bit(FR_FORCE, &req->flags);
			__clear_bit(FR_BACKGROUND, &req->flags);
			fuse_request_send(ff->fc, req);
			iput(req->misc.release.inode);
			fuse_put_request(ff->fc, req);
		} else {
			req->end = fuse_release_end;
			__set_bit(FR_BACKGROUND, &req->flags);
			fuse_request_send_background(ff->fc, req);
		}
		kfree(ff);
	}
}