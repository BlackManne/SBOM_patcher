

static int bq24190_set_mode_host(struct bq24190_dev_info *bdi)
{
	int ret;
	u8 v;

	ret = bq24190_read(bdi, BQ24190_REG_CTTC, &v);
	if (ret < 0)
		return ret;

	bdi->watchdog = ((v & BQ24190_REG_CTTC_WATCHDOG_MASK) >>
					BQ24190_REG_CTTC_WATCHDOG_SHIFT);
	v &= ~BQ24190_REG_CTTC_WATCHDOG_MASK;

	return bq24190_write(bdi, BQ24190_REG_CTTC, v);
}