

static ssize_t ffs_epfile_io(struct file *file, struct ffs_io_data *io_data)
{
	struct ffs_epfile *epfile = file->private_data;
	struct ffs_ep *ep;
	char *data = NULL;
	ssize_t ret, data_len = -EINVAL;
	int halt;

	/* Are we still active? */
	if (WARN_ON(epfile->ffs->state != FFS_ACTIVE)) {
		ret = -ENODEV;
		goto error;
	}

	/* Wait for endpoint to be enabled */
	ep = epfile->ep;
	if (!ep) {
		if (file->f_flags & O_NONBLOCK) {
			ret = -EAGAIN;
			goto error;
		}

		ret = wait_event_interruptible(epfile->wait, (ep = epfile->ep));
		if (ret) {
			ret = -EINTR;
			goto error;
		}
	}

	/* Do we halt? */
	halt = (!io_data->read == !epfile->in);
	if (halt && epfile->isoc) {
		ret = -EINVAL;
		goto error;
	}

	/* Allocate & copy */
	if (!halt) {
		/*
		 * if we _do_ wait above, the epfile->ffs->gadget might be NULL
		 * before the waiting completes, so do not assign to 'gadget' earlier
		 */
		struct usb_gadget *gadget = epfile->ffs->gadget;

		spin_lock_irq(&epfile->ffs->eps_lock);
		/* In the meantime, endpoint got disabled or changed. */
		if (epfile->ep != ep) {
			spin_unlock_irq(&epfile->ffs->eps_lock);
			return -ESHUTDOWN;
		}
		/*
		 * Controller may require buffer size to be aligned to
		 * maxpacketsize of an out endpoint.
		 */
		data_len = io_data->read ?
			   usb_ep_align_maybe(gadget, ep->ep, io_data->len) :
			   io_data->len;
		spin_unlock_irq(&epfile->ffs->eps_lock);

		data = kmalloc(data_len, GFP_KERNEL);
		if (unlikely(!data))
			return -ENOMEM;
		if (io_data->aio && !io_data->read) {
			int i;
			size_t pos = 0;
			for (i = 0; i < io_data->nr_segs; i++) {
				if (unlikely(copy_from_user(&data[pos],
					     io_data->iovec[i].iov_base,
					     io_data->iovec[i].iov_len))) {
					ret = -EFAULT;
					goto error;
				}
				pos += io_data->iovec[i].iov_len;
			}
		} else {
			if (!io_data->read &&
			    unlikely(__copy_from_user(data, io_data->buf,
						      io_data->len))) {
				ret = -EFAULT;
				goto error;
			}
		}
	}

	/* We will be using request */
	ret = ffs_mutex_lock(&epfile->mutex, file->f_flags & O_NONBLOCK);
	if (unlikely(ret))
		goto error;

	spin_lock_irq(&epfile->ffs->eps_lock);

	if (epfile->ep != ep) {
		/* In the meantime, endpoint got disabled or changed. */
		ret = -ESHUTDOWN;
		spin_unlock_irq(&epfile->ffs->eps_lock);
	} else if (halt) {
		/* Halt */
		if (likely(epfile->ep == ep) && !WARN_ON(!ep->ep))
			usb_ep_set_halt(ep->ep);
		spin_unlock_irq(&epfile->ffs->eps_lock);
		ret = -EBADMSG;
	} else {
		/* Fire the request */
		struct usb_request *req;

		/*
		 * Sanity Check: even though data_len can't be used
		 * uninitialized at the time I write this comment, some
		 * compilers complain about this situation.
		 * In order to keep the code clean from warnings, data_len is
		 * being initialized to -EINVAL during its declaration, which
		 * means we can't rely on compiler anymore to warn no future
		 * changes won't result in data_len being used uninitialized.
		 * For such reason, we're adding this redundant sanity check
		 * here.
		 */
		if (unlikely(data_len == -EINVAL)) {
			WARN(1, "%s: data_len == -EINVAL\n", __func__);
			ret = -EINVAL;
			goto error_lock;
		}

		if (io_data->aio) {
			req = usb_ep_alloc_request(ep->ep, GFP_KERNEL);
			if (unlikely(!req))
				goto error_lock;

			req->buf      = data;
			req->length   = data_len;

			io_data->buf = data;
			io_data->ep = ep->ep;
			io_data->req = req;

			req->context  = io_data;
			req->complete = ffs_epfile_async_io_complete;

			ret = usb_ep_queue(ep->ep, req, GFP_ATOMIC);
			if (unlikely(ret)) {
				usb_ep_free_request(ep->ep, req);
				goto error_lock;
			}
			ret = -EIOCBQUEUED;

			spin_unlock_irq(&epfile->ffs->eps_lock);
		} else {
			DECLARE_COMPLETION_ONSTACK(done);

			req = ep->req;
			req->buf      = data;
			req->length   = data_len;

			req->context  = &done;
			req->complete = ffs_epfile_io_complete;

			ret = usb_ep_queue(ep->ep, req, GFP_ATOMIC);

			spin_unlock_irq(&epfile->ffs->eps_lock);

			if (unlikely(ret < 0)) {
				/* nop */
			} else if (unlikely(
				   wait_for_completion_interruptible(&done))) {
				ret = -EINTR;
				usb_ep_dequeue(ep->ep, req);
			} else {
				/*
				 * XXX We may end up silently droping data
				 * here.  Since data_len (i.e. req->length) may
				 * be bigger than len (after being rounded up
				 * to maxpacketsize), we may end up with more
				 * data then user space has space for.
				 */
				ret = ep->status;
				if (io_data->read && ret > 0) {
					ret = min_t(size_t, ret, io_data->len);

					if (unlikely(copy_to_user(io_data->buf,
						data, ret)))
						ret = -EFAULT;
				}
			}
			kfree(data);
		}
	}

	mutex_unlock(&epfile->mutex);
	return ret;

error_lock:
	spin_unlock_irq(&epfile->ffs->eps_lock);
	mutex_unlock(&epfile->mutex);
error:
	kfree(data);
	return ret;
}