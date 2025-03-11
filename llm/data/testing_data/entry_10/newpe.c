

static int zx_dma_probe(struct platform_device *op)
{
	struct zx_dma_dev *d;
	struct resource *iores;
	int i, ret = 0;

	iores = platform_get_resource(op, IORESOURCE_MEM, 0);
	if (!iores)
		return -EINVAL;

	d = devm_kzalloc(&op->dev, sizeof(*d), GFP_KERNEL);
	if (!d)
		return -ENOMEM;

	d->base = devm_ioremap_resource(&op->dev, iores);
	if (IS_ERR(d->base))
		return PTR_ERR(d->base);

	of_property_read_u32((&op->dev)->of_node,
			     "dma-channels", &d->dma_channels);
	of_property_read_u32((&op->dev)->of_node,
			     "dma-requests", &d->dma_requests);
	if (!d->dma_requests || !d->dma_channels)
		return -EINVAL;

	d->clk = devm_clk_get(&op->dev, NULL);
	if (IS_ERR(d->clk)) {
		dev_err(&op->dev, "no dma clk\n");
		return PTR_ERR(d->clk);
	}

	d->irq = platform_get_irq(op, 0);
	ret = devm_request_irq(&op->dev, d->irq, zx_dma_int_handler,
			       0, DRIVER_NAME, d);
	if (ret)
		return ret;

	/* A DMA memory pool for LLIs, align on 32-byte boundary */
	d->pool = dmam_pool_create(DRIVER_NAME, &op->dev,
			LLI_BLOCK_SIZE, 32, 0);
	if (!d->pool)
		return -ENOMEM;

	/* init phy channel */
	d->phy = devm_kzalloc(&op->dev,
		d->dma_channels * sizeof(struct zx_dma_phy), GFP_KERNEL);
	if (!d->phy)
		return -ENOMEM;

	for (i = 0; i < d->dma_channels; i++) {
		struct zx_dma_phy *p = &d->phy[i];

		p->idx = i;
		p->base = d->base + i * 0x40;
	}

	INIT_LIST_HEAD(&d->slave.channels);
	dma_cap_set(DMA_SLAVE, d->slave.cap_mask);
	dma_cap_set(DMA_MEMCPY, d->slave.cap_mask);
	dma_cap_set(DMA_CYCLIC, d->slave.cap_mask);
	dma_cap_set(DMA_PRIVATE, d->slave.cap_mask);
	d->slave.dev = &op->dev;
	d->slave.device_free_chan_resources = zx_dma_free_chan_resources;
	d->slave.device_tx_status = zx_dma_tx_status;
	d->slave.device_prep_dma_memcpy = zx_dma_prep_memcpy;
	d->slave.device_prep_slave_sg = zx_dma_prep_slave_sg;
	d->slave.device_prep_dma_cyclic = zx_dma_prep_dma_cyclic;
	d->slave.device_issue_pending = zx_dma_issue_pending;
	d->slave.device_config = zx_dma_config;
	d->slave.device_terminate_all = zx_dma_terminate_all;
	d->slave.device_pause = zx_dma_transfer_pause;
	d->slave.device_resume = zx_dma_transfer_resume;
	d->slave.copy_align = DMA_ALIGN;
	d->slave.src_addr_widths = ZX_DMA_BUSWIDTHS;
	d->slave.dst_addr_widths = ZX_DMA_BUSWIDTHS;
	d->slave.directions = BIT(DMA_MEM_TO_MEM) | BIT(DMA_MEM_TO_DEV)
			| BIT(DMA_DEV_TO_MEM);
	d->slave.residue_granularity = DMA_RESIDUE_GRANULARITY_SEGMENT;

	/* init virtual channel */
	d->chans = devm_kzalloc(&op->dev,
		d->dma_requests * sizeof(struct zx_dma_chan), GFP_KERNEL);
	if (!d->chans)
		return -ENOMEM;

	for (i = 0; i < d->dma_requests; i++) {
		struct zx_dma_chan *c = &d->chans[i];

		c->status = DMA_IN_PROGRESS;
		INIT_LIST_HEAD(&c->node);
		c->vc.desc_free = zx_dma_free_desc;
		vchan_init(&c->vc, &d->slave);
	}

	/* Enable clock before accessing registers */
	ret = clk_prepare_enable(d->clk);
	if (ret < 0) {
		dev_err(&op->dev, "clk_prepare_enable failed: %d\n", ret);
		goto zx_dma_out;
	}

	zx_dma_init_state(d);

	spin_lock_init(&d->lock);
	INIT_LIST_HEAD(&d->chan_pending);
	platform_set_drvdata(op, d);

	ret = dma_async_device_register(&d->slave);
	if (ret)
		goto clk_dis;

	ret = of_dma_controller_register((&op->dev)->of_node,
					 zx_of_dma_simple_xlate, d);
	if (ret)
		goto of_dma_register_fail;

	dev_info(&op->dev, "initialized\n");
	return 0;

of_dma_register_fail:
	dma_async_device_unregister(&d->slave);
clk_dis:
	clk_disable_unprepare(d->clk);
zx_dma_out:
	return ret;
}