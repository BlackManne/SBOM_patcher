

static int zr364xx_read_video_callback(struct zr364xx_camera *cam,
					struct zr364xx_pipeinfo *pipe_info,
					struct urb *purb)
{
	unsigned char *pdest;
	unsigned char *psrc;
	s32 idx = -1;
	struct zr364xx_framei *frm;
	int i = 0;
	unsigned char *ptr = NULL;

	_DBG("buffer to user\n");
	idx = cam->cur_frame;
	frm = &cam->buffer.frame[idx];

	/* swap bytes if camera needs it */
	if (cam->method == METHOD0) {
		u16 *buf = (u16 *)pipe_info->transfer_buffer;
		for (i = 0; i < purb->actual_length/2; i++)
			swab16s(buf + i);
	}

	/* search done.  now find out if should be acquiring */
	if (!cam->b_acquire) {
		/* we found a frame, but this channel is turned off */
		frm->ulState = ZR364XX_READ_IDLE;
		return -EINVAL;
	}

	psrc = (u8 *)pipe_info->transfer_buffer;
	ptr = pdest = frm->lpvbits;

	if (frm->ulState == ZR364XX_READ_IDLE) {
		if (purb->actual_length < 128) {
			/* header incomplete */
			dev_info(&cam->udev->dev,
				 "%s: buffer (%d bytes) too small to hold jpeg header. Discarding.\n",
				 __func__, purb->actual_length);
			return -EINVAL;
		}

		frm->ulState = ZR364XX_READ_FRAME;
		frm->cur_size = 0;

		_DBG("jpeg header, ");
		memcpy(ptr, header1, sizeof(header1));
		ptr += sizeof(header1);
		header3 = 0;
		memcpy(ptr, &header3, 1);
		ptr++;
		memcpy(ptr, psrc, 64);
		ptr += 64;
		header3 = 1;
		memcpy(ptr, &header3, 1);
		ptr++;
		memcpy(ptr, psrc + 64, 64);
		ptr += 64;
		memcpy(ptr, header2, sizeof(header2));
		ptr += sizeof(header2);
		memcpy(ptr, psrc + 128,
		       purb->actual_length - 128);
		ptr += purb->actual_length - 128;
		_DBG("header : %d %d %d %d %d %d %d %d %d\n",
		    psrc[0], psrc[1], psrc[2],
		    psrc[3], psrc[4], psrc[5],
		    psrc[6], psrc[7], psrc[8]);
		frm->cur_size = ptr - pdest;
	} else {
		if (frm->cur_size + purb->actual_length > MAX_FRAME_SIZE) {
			dev_info(&cam->udev->dev,
				 "%s: buffer (%d bytes) too small to hold frame data. Discarding frame data.\n",
				 __func__, MAX_FRAME_SIZE);
		} else {
			pdest += frm->cur_size;
			memcpy(pdest, psrc, purb->actual_length);
			frm->cur_size += purb->actual_length;
		}
	}
	/*_DBG("cur_size %lu urb size %d\n", frm->cur_size,
		purb->actual_length);*/

	if (purb->actual_length < pipe_info->transfer_size) {
		_DBG("****************Buffer[%d]full*************\n", idx);
		cam->last_frame = cam->cur_frame;
		cam->cur_frame++;
		/* end of system frame ring buffer, start at zero */
		if (cam->cur_frame == cam->buffer.dwFrames)
			cam->cur_frame = 0;

		/* frame ready */
		/* go back to find the JPEG EOI marker */
		ptr = pdest = frm->lpvbits;
		ptr += frm->cur_size - 2;
		while (ptr > pdest) {
			if (*ptr == 0xFF && *(ptr + 1) == 0xD9
			    && *(ptr + 2) == 0xFF)
				break;
			ptr--;
		}
		if (ptr == pdest)
			DBG("No EOI marker\n");

		/* Sometimes there is junk data in the middle of the picture,
		 * we want to skip this bogus frames */
		while (ptr > pdest) {
			if (*ptr == 0xFF && *(ptr + 1) == 0xFF
			    && *(ptr + 2) == 0xFF)
				break;
			ptr--;
		}
		if (ptr != pdest) {
			DBG("Bogus frame ? %d\n", ++(cam->nb));
		} else if (cam->b_acquire) {
			/* we skip the 2 first frames which are usually buggy */
			if (cam->skip)
				cam->skip--;
			else {
				_DBG("jpeg(%lu): %d %d %d %d %d %d %d %d\n",
				    frm->cur_size,
				    pdest[0], pdest[1], pdest[2], pdest[3],
				    pdest[4], pdest[5], pdest[6], pdest[7]);

				zr364xx_got_frame(cam, frm->cur_size);
			}
		}
		cam->frame_count++;
		frm->ulState = ZR364XX_READ_IDLE;
		frm->cur_size = 0;
	}
	/* done successfully */
	return 0;
}