

static int
atmel_hsmc_nand_controller_legacy_init(struct atmel_hsmc_nand_controller *nc)
{
	struct regmap_config regmap_conf = {
		.reg_bits = 32,
		.val_bits = 32,
		.reg_stride = 4,
	};

	struct device *dev = nc->base.dev;
	struct device_node *nand_np, *nfc_np;
	void __iomem *iomem;
	struct resource res;
	int ret;

	nand_np = dev->of_node;
	nfc_np = of_find_compatible_node(dev->of_node, NULL,
					 "atmel,sama5d3-nfc");
	if (!nfc_np) {
		dev_err(dev, "Could not find device node for sama5d3-nfc\n");
		return -ENODEV;
	}

	nc->clk = of_clk_get(nfc_np, 0);
	if (IS_ERR(nc->clk)) {
		ret = PTR_ERR(nc->clk);
		dev_err(dev, "Failed to retrieve HSMC clock (err = %d)\n",
			ret);
		goto out;
	}

	ret = clk_prepare_enable(nc->clk);
	if (ret) {
		dev_err(dev, "Failed to enable the HSMC clock (err = %d)\n",
			ret);
		goto out;
	}

	nc->irq = of_irq_get(nand_np, 0);
	if (nc->irq <= 0) {
		ret = nc->irq ?: -ENXIO;
		if (ret != -EPROBE_DEFER)
			dev_err(dev, "Failed to get IRQ number (err = %d)\n",
				ret);
		goto out;
	}

	ret = of_address_to_resource(nfc_np, 0, &res);
	if (ret) {
		dev_err(dev, "Invalid or missing NFC IO resource (err = %d)\n",
			ret);
		goto out;
	}

	iomem = devm_ioremap_resource(dev, &res);
	if (IS_ERR(iomem)) {
		ret = PTR_ERR(iomem);
		goto out;
	}

	regmap_conf.name = "nfc-io";
	regmap_conf.max_register = resource_size(&res) - 4;
	nc->io = devm_regmap_init_mmio(dev, iomem, &regmap_conf);
	if (IS_ERR(nc->io)) {
		ret = PTR_ERR(nc->io);
		dev_err(dev, "Could not create NFC IO regmap (err = %d)\n",
			ret);
		goto out;
	}

	ret = of_address_to_resource(nfc_np, 1, &res);
	if (ret) {
		dev_err(dev, "Invalid or missing HSMC resource (err = %d)\n",
			ret);
		goto out;
	}

	iomem = devm_ioremap_resource(dev, &res);
	if (IS_ERR(iomem)) {
		ret = PTR_ERR(iomem);
		goto out;
	}

	regmap_conf.name = "smc";
	regmap_conf.max_register = resource_size(&res) - 4;
	nc->base.smc = devm_regmap_init_mmio(dev, iomem, &regmap_conf);
	if (IS_ERR(nc->base.smc)) {
		ret = PTR_ERR(nc->base.smc);
		dev_err(dev, "Could not create NFC IO regmap (err = %d)\n",
			ret);
		goto out;
	}

	ret = of_address_to_resource(nfc_np, 2, &res);
	if (ret) {
		dev_err(dev, "Invalid or missing SRAM resource (err = %d)\n",
			ret);
		goto out;
	}

	nc->sram.virt = devm_ioremap_resource(dev, &res);
	if (IS_ERR(nc->sram.virt)) {
		ret = PTR_ERR(nc->sram.virt);
		goto out;
	}

	nc->sram.dma = res.start;

out:
	of_node_put(nfc_np);

	return ret;
}