

int bcmgenet_mii_probe(struct net_device *dev)
{
	struct bcmgenet_priv *priv = netdev_priv(dev);
	struct device_node *dn = priv->pdev->dev.of_node;
	struct phy_device *phydev;
	u32 phy_flags;
	int ret;

	/* Communicate the integrated PHY revision */
	phy_flags = priv->gphy_rev;

	/* Initialize link state variables that bcmgenet_mii_setup() uses */
	priv->old_link = -1;
	priv->old_speed = -1;
	priv->old_duplex = -1;
	priv->old_pause = -1;

	if (dn) {
		phydev = of_phy_connect(dev, priv->phy_dn, bcmgenet_mii_setup,
					phy_flags, priv->phy_interface);
		if (!phydev) {
			pr_err("could not attach to PHY\n");
			return -ENODEV;
		}
	} else {
		phydev = priv->phydev;
		phydev->dev_flags = phy_flags;

		ret = phy_connect_direct(dev, phydev, bcmgenet_mii_setup,
					 priv->phy_interface);
		if (ret) {
			pr_err("could not attach to PHY\n");
			return -ENODEV;
		}
	}

	priv->phydev = phydev;

	/* Configure port multiplexer based on what the probed PHY device since
	 * reading the 'max-speed' property determines the maximum supported
	 * PHY speed which is needed for bcmgenet_mii_config() to configure
	 * things appropriately.
	 */
	ret = bcmgenet_mii_config(dev, true);
	if (ret) {
		phy_disconnect(priv->phydev);
		return ret;
	}

	phydev->advertising = phydev->supported;

	/* The internal PHY has its link interrupts routed to the
	 * Ethernet MAC ISRs
	 */
	if (priv->internal_phy)
		priv->phydev->irq = PHY_IGNORE_INTERRUPT;

	return 0;
}