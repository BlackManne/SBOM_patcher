

int ccp_dmaengine_register(struct ccp_device *ccp)
{
	struct ccp_dma_chan *chan;
	struct dma_device *dma_dev = &ccp->dma_dev;
	struct dma_chan *dma_chan;
	char *dma_cmd_cache_name;
	char *dma_desc_cache_name;
	unsigned int i;
	int ret;

	ccp->ccp_dma_chan = devm_kcalloc(ccp->dev, ccp->cmd_q_count,
					 sizeof(*(ccp->ccp_dma_chan)),
					 GFP_KERNEL);
	if (!ccp->ccp_dma_chan)
		return -ENOMEM;

	dma_cmd_cache_name = devm_kasprintf(ccp->dev, GFP_KERNEL,
					    "%s-dmaengine-cmd-cache",
					    ccp->name);
	if (!dma_cmd_cache_name)
		return -ENOMEM;

	ccp->dma_cmd_cache = kmem_cache_create(dma_cmd_cache_name,
					       sizeof(struct ccp_dma_cmd),
					       sizeof(void *),
					       SLAB_HWCACHE_ALIGN, NULL);
	if (!ccp->dma_cmd_cache)
		return -ENOMEM;

	dma_desc_cache_name = devm_kasprintf(ccp->dev, GFP_KERNEL,
					     "%s-dmaengine-desc-cache",
					     ccp->name);
	if (!dma_cmd_cache_name) {
		ret = -ENOMEM;
		goto err_cache;
	}

	ccp->dma_desc_cache = kmem_cache_create(dma_desc_cache_name,
						sizeof(struct ccp_dma_desc),
						sizeof(void *),
						SLAB_HWCACHE_ALIGN, NULL);
	if (!ccp->dma_desc_cache) {
		ret = -ENOMEM;
		goto err_cache;
	}

	dma_dev->dev = ccp->dev;
	dma_dev->src_addr_widths = CCP_DMA_WIDTH(dma_get_mask(ccp->dev));
	dma_dev->dst_addr_widths = CCP_DMA_WIDTH(dma_get_mask(ccp->dev));
	dma_dev->directions = DMA_MEM_TO_MEM;
	dma_dev->residue_granularity = DMA_RESIDUE_GRANULARITY_DESCRIPTOR;
	dma_cap_set(DMA_MEMCPY, dma_dev->cap_mask);
	dma_cap_set(DMA_SG, dma_dev->cap_mask);
	dma_cap_set(DMA_INTERRUPT, dma_dev->cap_mask);

	INIT_LIST_HEAD(&dma_dev->channels);
	for (i = 0; i < ccp->cmd_q_count; i++) {
		chan = ccp->ccp_dma_chan + i;
		dma_chan = &chan->dma_chan;

		chan->ccp = ccp;

		spin_lock_init(&chan->lock);
		INIT_LIST_HEAD(&chan->pending);
		INIT_LIST_HEAD(&chan->active);
		INIT_LIST_HEAD(&chan->complete);

		tasklet_init(&chan->cleanup_tasklet, ccp_do_cleanup,
			     (unsigned long)chan);

		dma_chan->device = dma_dev;
		dma_cookie_init(dma_chan);

		list_add_tail(&dma_chan->device_node, &dma_dev->channels);
	}

	dma_dev->device_free_chan_resources = ccp_free_chan_resources;
	dma_dev->device_prep_dma_memcpy = ccp_prep_dma_memcpy;
	dma_dev->device_prep_dma_sg = ccp_prep_dma_sg;
	dma_dev->device_prep_dma_interrupt = ccp_prep_dma_interrupt;
	dma_dev->device_issue_pending = ccp_issue_pending;
	dma_dev->device_tx_status = ccp_tx_status;
	dma_dev->device_pause = ccp_pause;
	dma_dev->device_resume = ccp_resume;
	dma_dev->device_terminate_all = ccp_terminate_all;

	ret = dma_async_device_register(dma_dev);
	if (ret)
		goto err_reg;

	return 0;

err_reg:
	kmem_cache_destroy(ccp->dma_desc_cache);

err_cache:
	kmem_cache_destroy(ccp->dma_cmd_cache);

	return ret;
}