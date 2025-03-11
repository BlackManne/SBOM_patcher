

static void fuse_file_put(struct fuse_file *ff, bool sync)
{
	if (atomic_dec_and_test(&ff->count)) {
		struct fuse_req *req = ff->reserved_req;

		if (sync) {
			fuse_request_send(ff->fc, req);
			path_put(&req->misc.release.path);
			fuse_put_request(ff->fc, req);
		} else {
			req->end = fuse_release_end;
			fuse_request_send_background(ff->fc, req);
		}
		kfree(ff);
	}
}