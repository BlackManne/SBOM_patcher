

int hns_nic_init_phy(struct net_device *ndev, struct hnae_handle *h)
{
	struct phy_device *phy_dev = h->phy_dev;
	int ret;

	if (!h->phy_dev)
		return 0;

	if (h->phy_if != PHY_INTERFACE_MODE_XGMII) {
		phy_dev->dev_flags = 0;

		ret = phy_connect_direct(ndev, phy_dev, hns_nic_adjust_link,
					 h->phy_if);
	} else {
		ret = phy_attach_direct(ndev, phy_dev, 0, h->phy_if);
	}
	if (unlikely(ret))
		return -ENODEV;

	phy_dev->supported &= h->if_support;
	phy_dev->advertising = phy_dev->supported;

	if (h->phy_if == PHY_INTERFACE_MODE_XGMII)
		phy_dev->autoneg = false;

	if (h->phy_if == PHY_INTERFACE_MODE_SGMII)
		phy_stop(phy_dev);

	return 0;
}