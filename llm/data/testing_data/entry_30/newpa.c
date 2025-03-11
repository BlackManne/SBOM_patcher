

static int flctl_dma_fifo0_transfer(struct sh_flctl *flctl, unsigned long *buf,
					int len, enum dma_data_direction dir)
{
	struct dma_async_tx_descriptor *desc = NULL;
	struct dma_chan *chan;
	enum dma_transfer_direction tr_dir;
	dma_addr_t dma_addr;
	dma_cookie_t cookie;
	uint32_t reg;
	int ret;

	if (dir == DMA_FROM_DEVICE) {
		chan = flctl->chan_fifo0_rx;
		tr_dir = DMA_DEV_TO_MEM;
	} else {
		chan = flctl->chan_fifo0_tx;
		tr_dir = DMA_MEM_TO_DEV;
	}

	dma_addr = dma_map_single(chan->device->dev, buf, len, dir);

	if (!dma_mapping_error(chan->device->dev, dma_addr))
		desc = dmaengine_prep_slave_single(chan, dma_addr, len,
			tr_dir, DMA_PREP_INTERRUPT | DMA_CTRL_ACK);

	if (desc) {
		reg = readl(FLINTDMACR(flctl));
		reg |= DREQ0EN;
		writel(reg, FLINTDMACR(flctl));

		desc->callback = flctl_dma_complete;
		desc->callback_param = flctl;
		cookie = dmaengine_submit(desc);
		if (dma_submit_error(cookie)) {
			ret = dma_submit_error(cookie);
			dev_warn(&flctl->pdev->dev,
				 "DMA submit failed, falling back to PIO\n");
			goto out;
		}

		dma_async_issue_pending(chan);
	} else {
		/* DMA failed, fall back to PIO */
		flctl_release_dma(flctl);
		dev_warn(&flctl->pdev->dev,
			 "DMA failed, falling back to PIO\n");
		ret = -EIO;
		goto out;
	}

	ret =
	wait_for_completion_timeout(&flctl->dma_complete,
				msecs_to_jiffies(3000));

	if (ret <= 0) {
		dmaengine_terminate_all(chan);
		dev_err(&flctl->pdev->dev, "wait_for_completion_timeout\n");
	}

out:
	reg = readl(FLINTDMACR(flctl));
	reg &= ~DREQ0EN;
	writel(reg, FLINTDMACR(flctl));

	dma_unmap_single(chan->device->dev, dma_addr, len, dir);

	/* ret > 0 is success */
	return ret;
}

static void read_fiforeg(struct sh_flctl *flctl, int rlen, int offset)
{
	int i, len_4align;
	unsigned long *buf = (unsigned long *)&flctl->done_buff[offset];

	len_4align = (rlen + 3) / 4;

	/* initiate DMA transfer */
	if (flctl->chan_fifo0_rx && rlen >= 32 &&
		flctl_dma_fifo0_transfer(flctl, buf, rlen, DMA_DEV_TO_MEM) > 0)
			goto convert;	/* DMA success */

	/* do polling transfer */
	for (i = 0; i < len_4align; i++) {
		wait_rfifo_ready(flctl);
		buf[i] = readl(FLDTFIFO(flctl));
	}

convert:
	for (i = 0; i < len_4align; i++)
		buf[i] = be32_to_cpu(buf[i]);
}

static void write_ec_fiforeg(struct sh_flctl *flctl, int rlen,
						unsigned int offset)
{
	int i, len_4align;
	unsigned long *buf = (unsigned long *)&flctl->done_buff[offset];

	len_4align = (rlen + 3) / 4;

	for (i = 0; i < len_4align; i++)
		buf[i] = cpu_to_be32(buf[i]);

	/* initiate DMA transfer */
	if (flctl->chan_fifo0_tx && rlen >= 32 &&
		flctl_dma_fifo0_transfer(flctl, buf, rlen, DMA_MEM_TO_DEV) > 0)
			return;	/* DMA success */

	/* do polling transfer */
	for (i = 0; i < len_4align; i++) {
		wait_wecfifo_ready(flctl);
		writel(buf[i], FLECFIFO(flctl));
	}
}