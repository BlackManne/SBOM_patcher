

static void vmd_detach_resources(struct vmd_dev *vmd)
{
	vmd->dev->resource[VMD_MEMBAR1].child = NULL;
	vmd->dev->resource[VMD_MEMBAR2].child = NULL;
}

static void vmd_remove(struct pci_dev *dev)
{
	struct vmd_dev *vmd = pci_get_drvdata(dev);

	sysfs_remove_link(&vmd->dev->dev.kobj, "domain");
	pci_stop_root_bus(vmd->bus);
	pci_remove_root_bus(vmd->bus);
	vmd_cleanup_srcu(vmd);
	vmd_teardown_dma_ops(vmd);
	vmd_detach_resources(vmd);
	irq_domain_remove(vmd->irq_domain);
}