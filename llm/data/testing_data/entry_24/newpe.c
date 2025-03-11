

static int tda1004x_read_byte(struct tda1004x_state *state, int reg)
{
	int ret;
	u8 b0[] = { reg };
	u8 b1[] = { 0 };
	struct i2c_msg msg[] = {{ .flags = 0, .buf = b0, .len = 1 },
				{ .flags = I2C_M_RD, .buf = b1, .len = 1 }};

	dprintk("%s: reg=0x%x\n", __func__, reg);

	msg[0].addr = state->config->demod_address;
	msg[1].addr = state->config->demod_address;
	ret = i2c_transfer(state->i2c, msg, 2);

	if (ret != 2) {
		dprintk("%s: error reg=0x%x, ret=%i\n", __func__, reg,
			ret);
		return -EINVAL;
	}

	dprintk("%s: success reg=0x%x, data=0x%x, ret=%i\n", __func__,
		reg, b1[0], ret);
	return b1[0];
}

static int tda1004x_set_fe(struct dvb_frontend* fe,
			   struct dvb_frontend_parameters *fe_params)
{
	struct tda1004x_state* state = fe->demodulator_priv;
	int tmp;
	int inversion;

	dprintk("%s\n", __func__);

	if (state->demod_type == TDA1004X_DEMOD_TDA10046) {
		// setup auto offset
		tda1004x_write_mask(state, TDA1004X_AUTO, 0x10, 0x10);
		tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x80, 0);
		tda1004x_write_mask(state, TDA1004X_IN_CONF2, 0xC0, 0);

		// disable agc_conf[2]
		tda1004x_write_mask(state, TDA10046H_AGC_CONF, 4, 0);
	}

	// set frequency
	if (fe->ops.tuner_ops.set_params) {
		fe->ops.tuner_ops.set_params(fe, fe_params);
		if (fe->ops.i2c_gate_ctrl)
			fe->ops.i2c_gate_ctrl(fe, 0);
	}

	// Hardcoded to use auto as much as possible on the TDA10045 as it
	// is very unreliable if AUTO mode is _not_ used.
	if (state->demod_type == TDA1004X_DEMOD_TDA10045) {
		fe_params->u.ofdm.code_rate_HP = FEC_AUTO;
		fe_params->u.ofdm.guard_interval = GUARD_INTERVAL_AUTO;
		fe_params->u.ofdm.transmission_mode = TRANSMISSION_MODE_AUTO;
	}

	// Set standard params.. or put them to auto
	if ((fe_params->u.ofdm.code_rate_HP == FEC_AUTO) ||
		(fe_params->u.ofdm.code_rate_LP == FEC_AUTO) ||
		(fe_params->u.ofdm.constellation == QAM_AUTO) ||
		(fe_params->u.ofdm.hierarchy_information == HIERARCHY_AUTO)) {
		tda1004x_write_mask(state, TDA1004X_AUTO, 1, 1);	// enable auto
		tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x03, 0);	// turn off constellation bits
		tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x60, 0);	// turn off hierarchy bits
		tda1004x_write_mask(state, TDA1004X_IN_CONF2, 0x3f, 0);	// turn off FEC bits
	} else {
		tda1004x_write_mask(state, TDA1004X_AUTO, 1, 0);	// disable auto

		// set HP FEC
		tmp = tda1004x_encode_fec(fe_params->u.ofdm.code_rate_HP);
		if (tmp < 0)
			return tmp;
		tda1004x_write_mask(state, TDA1004X_IN_CONF2, 7, tmp);

		// set LP FEC
		tmp = tda1004x_encode_fec(fe_params->u.ofdm.code_rate_LP);
		if (tmp < 0)
			return tmp;
		tda1004x_write_mask(state, TDA1004X_IN_CONF2, 0x38, tmp << 3);

		// set constellation
		switch (fe_params->u.ofdm.constellation) {
		case QPSK:
			tda1004x_write_mask(state, TDA1004X_IN_CONF1, 3, 0);
			break;

		case QAM_16:
			tda1004x_write_mask(state, TDA1004X_IN_CONF1, 3, 1);
			break;

		case QAM_64:
			tda1004x_write_mask(state, TDA1004X_IN_CONF1, 3, 2);
			break;

		default:
			return -EINVAL;
		}

		// set hierarchy
		switch (fe_params->u.ofdm.hierarchy_information) {
		case HIERARCHY_NONE:
			tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x60, 0 << 5);
			break;

		case HIERARCHY_1:
			tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x60, 1 << 5);
			break;

		case HIERARCHY_2:
			tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x60, 2 << 5);
			break;

		case HIERARCHY_4:
			tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x60, 3 << 5);
			break;

		default:
			return -EINVAL;
		}
	}

	// set bandwidth
	switch (state->demod_type) {
	case TDA1004X_DEMOD_TDA10045:
		tda10045h_set_bandwidth(state, fe_params->u.ofdm.bandwidth);
		break;

	case TDA1004X_DEMOD_TDA10046:
		tda10046h_set_bandwidth(state, fe_params->u.ofdm.bandwidth);
		break;
	}

	// set inversion
	inversion = fe_params->inversion;
	if (state->config->invert)
		inversion = inversion ? INVERSION_OFF : INVERSION_ON;
	switch (inversion) {
	case INVERSION_OFF:
		tda1004x_write_mask(state, TDA1004X_CONFC1, 0x20, 0);
		break;

	case INVERSION_ON:
		tda1004x_write_mask(state, TDA1004X_CONFC1, 0x20, 0x20);
		break;

	default:
		return -EINVAL;
	}

	// set guard interval
	switch (fe_params->u.ofdm.guard_interval) {
	case GUARD_INTERVAL_1_32:
		tda1004x_write_mask(state, TDA1004X_AUTO, 2, 0);
		tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x0c, 0 << 2);
		break;

	case GUARD_INTERVAL_1_16:
		tda1004x_write_mask(state, TDA1004X_AUTO, 2, 0);
		tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x0c, 1 << 2);
		break;

	case GUARD_INTERVAL_1_8:
		tda1004x_write_mask(state, TDA1004X_AUTO, 2, 0);
		tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x0c, 2 << 2);
		break;

	case GUARD_INTERVAL_1_4:
		tda1004x_write_mask(state, TDA1004X_AUTO, 2, 0);
		tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x0c, 3 << 2);
		break;

	case GUARD_INTERVAL_AUTO:
		tda1004x_write_mask(state, TDA1004X_AUTO, 2, 2);
		tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x0c, 0 << 2);
		break;

	default:
		return -EINVAL;
	}

	// set transmission mode
	switch (fe_params->u.ofdm.transmission_mode) {
	case TRANSMISSION_MODE_2K:
		tda1004x_write_mask(state, TDA1004X_AUTO, 4, 0);
		tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x10, 0 << 4);
		break;

	case TRANSMISSION_MODE_8K:
		tda1004x_write_mask(state, TDA1004X_AUTO, 4, 0);
		tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x10, 1 << 4);
		break;

	case TRANSMISSION_MODE_AUTO:
		tda1004x_write_mask(state, TDA1004X_AUTO, 4, 4);
		tda1004x_write_mask(state, TDA1004X_IN_CONF1, 0x10, 0);
		break;

	default:
		return -EINVAL;
	}

	// start the lock
	switch (state->demod_type) {
	case TDA1004X_DEMOD_TDA10045:
		tda1004x_write_mask(state, TDA1004X_CONFC4, 8, 8);
		tda1004x_write_mask(state, TDA1004X_CONFC4, 8, 0);
		break;

	case TDA1004X_DEMOD_TDA10046:
		tda1004x_write_mask(state, TDA1004X_AUTO, 0x40, 0x40);
		msleep(1);
		tda1004x_write_mask(state, TDA10046H_AGC_CONF, 4, 1);
		break;
	}

	msleep(10);

	return 0;
}