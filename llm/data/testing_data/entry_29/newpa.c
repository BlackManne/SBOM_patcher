

static int faraday_pci_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	const struct faraday_pci_variant *variant =
		of_device_get_match_data(dev);
	struct resource *regs;
	resource_size_t io_base;
	struct resource_entry *win;
	struct faraday_pci *p;
	struct resource *mem;
	struct resource *io;
	struct pci_host_bridge *host;
	struct clk *clk;
	unsigned char max_bus_speed = PCI_SPEED_33MHz;
	unsigned char cur_bus_speed = PCI_SPEED_33MHz;
	int ret;
	u32 val;
	LIST_HEAD(res);

	host = devm_pci_alloc_host_bridge(dev, sizeof(*p));
	if (!host)
		return -ENOMEM;

	host->dev.parent = dev;
	host->ops = &faraday_pci_ops;
	host->busnr = 0;
	host->msi = NULL;
	host->map_irq = of_irq_parse_and_map_pci;
	host->swizzle_irq = pci_common_swizzle;
	p = pci_host_bridge_priv(host);
	host->sysdata = p;
	p->dev = dev;

	/* Retrieve and enable optional clocks */
	clk = devm_clk_get(dev, "PCLK");
	if (IS_ERR(clk))
		return PTR_ERR(clk);
	ret = clk_prepare_enable(clk);
	if (ret) {
		dev_err(dev, "could not prepare PCLK\n");
		return ret;
	}
	p->bus_clk = devm_clk_get(dev, "PCICLK");
	if (IS_ERR(p->bus_clk))
		return PTR_ERR(p->bus_clk);
	ret = clk_prepare_enable(p->bus_clk);
	if (ret) {
		dev_err(dev, "could not prepare PCICLK\n");
		return ret;
	}

	regs = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	p->base = devm_ioremap_resource(dev, regs);
	if (IS_ERR(p->base))
		return PTR_ERR(p->base);

	ret = devm_of_pci_get_host_bridge_resources(dev, 0, 0xff,
						    &res, &io_base);
	if (ret)
		return ret;

	ret = devm_request_pci_bus_resources(dev, &res);
	if (ret)
		return ret;

	/* Get the I/O and memory ranges from DT */
	resource_list_for_each_entry(win, &res) {
		switch (resource_type(win->res)) {
		case IORESOURCE_IO:
			io = win->res;
			io->name = "Gemini PCI I/O";
			if (!faraday_res_to_memcfg(io->start - win->offset,
						   resource_size(io), &val)) {
				/* setup I/O space size */
				writel(val, p->base + PCI_IOSIZE);
			} else {
				dev_err(dev, "illegal IO mem size\n");
				return -EINVAL;
			}
			ret = pci_remap_iospace(io, io_base);
			if (ret) {
				dev_warn(dev, "error %d: failed to map resource %pR\n",
					 ret, io);
				continue;
			}
			break;
		case IORESOURCE_MEM:
			mem = win->res;
			mem->name = "Gemini PCI MEM";
			break;
		case IORESOURCE_BUS:
			break;
		default:
			break;
		}
	}

	/* Setup hostbridge */
	val = readl(p->base + PCI_CTRL);
	val |= PCI_COMMAND_IO;
	val |= PCI_COMMAND_MEMORY;
	val |= PCI_COMMAND_MASTER;
	writel(val, p->base + PCI_CTRL);
	/* Mask and clear all interrupts */
	faraday_raw_pci_write_config(p, 0, 0, FARADAY_PCI_CTRL2 + 2, 2, 0xF000);
	if (variant->cascaded_irq) {
		ret = faraday_pci_setup_cascaded_irq(p);
		if (ret) {
			dev_err(dev, "failed to setup cascaded IRQ\n");
			return ret;
		}
	}

	/* Check bus clock if we can gear up to 66 MHz */
	if (!IS_ERR(p->bus_clk)) {
		unsigned long rate;
		u32 val;

		faraday_raw_pci_read_config(p, 0, 0,
					    FARADAY_PCI_STATUS_CMD, 4, &val);
		rate = clk_get_rate(p->bus_clk);

		if ((rate == 33000000) && (val & PCI_STATUS_66MHZ_CAPABLE)) {
			dev_info(dev, "33MHz bus is 66MHz capable\n");
			max_bus_speed = PCI_SPEED_66MHz;
			ret = clk_set_rate(p->bus_clk, 66000000);
			if (ret)
				dev_err(dev, "failed to set bus clock\n");
		} else {
			dev_info(dev, "33MHz only bus\n");
			max_bus_speed = PCI_SPEED_33MHz;
		}

		/* Bumping the clock may fail so read back the rate */
		rate = clk_get_rate(p->bus_clk);
		if (rate == 33000000)
			cur_bus_speed = PCI_SPEED_33MHz;
		if (rate == 66000000)
			cur_bus_speed = PCI_SPEED_66MHz;
	}

	ret = faraday_pci_parse_map_dma_ranges(p, dev->of_node);
	if (ret)
		return ret;

	list_splice_init(&res, &host->windows);
	ret = pci_scan_root_bus_bridge(host);
	if (ret) {
		dev_err(dev, "failed to scan host: %d\n", ret);
		return ret;
	}
	p->bus = host->bus;
	p->bus->max_bus_speed = max_bus_speed;
	p->bus->cur_bus_speed = cur_bus_speed;

	pci_bus_assign_resources(p->bus);
	pci_bus_add_devices(p->bus);
	pci_free_resource_list(&res);

	return 0;
}