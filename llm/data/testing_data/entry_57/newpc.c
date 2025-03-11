

static int sg_start_req(Sg_request *srp, unsigned char *cmd)
{
	int res;
	struct request *rq;
	Sg_fd *sfp = srp->parentfp;
	sg_io_hdr_t *hp = &srp->header;
	int dxfer_len = (int) hp->dxfer_len;
	int dxfer_dir = hp->dxfer_direction;
	unsigned int iov_count = hp->iovec_count;
	Sg_scatter_hold *req_schp = &srp->data;
	Sg_scatter_hold *rsv_schp = &sfp->reserve;
	struct request_queue *q = sfp->parentdp->device->request_queue;
	struct rq_map_data *md, map_data;
	int rw = hp->dxfer_direction == SG_DXFER_TO_DEV ? WRITE : READ;

	SCSI_LOG_TIMEOUT(4, printk(KERN_INFO "sg_start_req: dxfer_len=%d\n",
				   dxfer_len));

	rq = blk_get_request(q, rw, GFP_ATOMIC);
	if (!rq)
		return -ENOMEM;

	memcpy(rq->cmd, cmd, hp->cmd_len);

	rq->cmd_len = hp->cmd_len;
	rq->cmd_type = REQ_TYPE_BLOCK_PC;

	srp->rq = rq;
	rq->end_io_data = srp;
	rq->sense = srp->sense_b;
	rq->retries = SG_DEFAULT_RETRIES;

	if ((dxfer_len <= 0) || (dxfer_dir == SG_DXFER_NONE))
		return 0;

	if (sg_allow_dio && hp->flags & SG_FLAG_DIRECT_IO &&
	    dxfer_dir != SG_DXFER_UNKNOWN && !iov_count &&
	    !sfp->parentdp->device->host->unchecked_isa_dma &&
	    blk_rq_aligned(q, (unsigned long)hp->dxferp, dxfer_len))
		md = NULL;
	else
		md = &map_data;

	if (md) {
		if (!sg_res_in_use(sfp) && dxfer_len <= rsv_schp->bufflen)
			sg_link_reserve(sfp, srp, dxfer_len);
		else {
			res = sg_build_indirect(req_schp, sfp, dxfer_len);
			if (res)
				return res;
		}

		md->pages = req_schp->pages;
		md->page_order = req_schp->page_order;
		md->nr_entries = req_schp->k_use_sg;
		md->offset = 0;
		md->null_mapped = hp->dxferp ? 0 : 1;
		if (dxfer_dir == SG_DXFER_TO_FROM_DEV)
			md->from_user = 1;
		else
			md->from_user = 0;
	}

	if (unlikely(iov_count > UIO_MAXIOV))
		return -EINVAL;

	if (iov_count) {
		int len, size = sizeof(struct sg_iovec) * iov_count;
		struct iovec *iov;

		iov = memdup_user(hp->dxferp, size);
		if (IS_ERR(iov))
			return PTR_ERR(iov);

		len = iov_length(iov, iov_count);
		if (hp->dxfer_len < len) {
			iov_count = iov_shorten(iov, iov_count, hp->dxfer_len);
			len = hp->dxfer_len;
		}

		res = blk_rq_map_user_iov(q, rq, md, (struct sg_iovec *)iov,
					  iov_count,
					  len, GFP_ATOMIC);
		kfree(iov);
	} else
		res = blk_rq_map_user(q, rq, md, hp->dxferp,
				      hp->dxfer_len, GFP_ATOMIC);

	if (!res) {
		srp->bio = rq->bio;

		if (!md) {
			req_schp->dio_in_use = 1;
			hp->info |= SG_INFO_DIRECT_IO;
		}
	}
	return res;
}