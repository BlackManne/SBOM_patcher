

static int tda1004x_get_fe(struct dvb_frontend *fe)
{
	struct dtv_frontend_properties *fe_params = &fe->dtv_property_cache;
	struct tda1004x_state* state = fe->demodulator_priv;

	dprintk("%s\n", __func__);

	// inversion status
	fe_params->inversion = INVERSION_OFF;
	if (tda1004x_read_byte(state, TDA1004X_CONFC1) & 0x20)
		fe_params->inversion = INVERSION_ON;
	if (state->config->invert)
		fe_params->inversion = fe_params->inversion ? INVERSION_OFF : INVERSION_ON;

	// bandwidth
	switch (state->demod_type) {
	case TDA1004X_DEMOD_TDA10045:
		switch (tda1004x_read_byte(state, TDA10045H_WREF_LSB)) {
		case 0x14:
			fe_params->bandwidth_hz = 8000000;
			break;
		case 0xdb:
			fe_params->bandwidth_hz = 7000000;
			break;
		case 0x4f:
			fe_params->bandwidth_hz = 6000000;
			break;
		}
		break;
	case TDA1004X_DEMOD_TDA10046:
		switch (tda1004x_read_byte(state, TDA10046H_TIME_WREF1)) {
		case 0x5c:
		case 0x54:
			fe_params->bandwidth_hz = 8000000;
			break;
		case 0x6a:
		case 0x60:
			fe_params->bandwidth_hz = 7000000;
			break;
		case 0x7b:
		case 0x70:
			fe_params->bandwidth_hz = 6000000;
			break;
		}
		break;
	}

	// FEC
	fe_params->code_rate_HP =
	    tda1004x_decode_fec(tda1004x_read_byte(state, TDA1004X_OUT_CONF2) & 7);
	fe_params->code_rate_LP =
	    tda1004x_decode_fec((tda1004x_read_byte(state, TDA1004X_OUT_CONF2) >> 3) & 7);

	/* modulation */
	switch (tda1004x_read_byte(state, TDA1004X_OUT_CONF1) & 3) {
	case 0:
		fe_params->modulation = QPSK;
		break;
	case 1:
		fe_params->modulation = QAM_16;
		break;
	case 2:
		fe_params->modulation = QAM_64;
		break;
	}

	// transmission mode
	fe_params->transmission_mode = TRANSMISSION_MODE_2K;
	if (tda1004x_read_byte(state, TDA1004X_OUT_CONF1) & 0x10)
		fe_params->transmission_mode = TRANSMISSION_MODE_8K;

	// guard interval
	switch ((tda1004x_read_byte(state, TDA1004X_OUT_CONF1) & 0x0c) >> 2) {
	case 0:
		fe_params->guard_interval = GUARD_INTERVAL_1_32;
		break;
	case 1:
		fe_params->guard_interval = GUARD_INTERVAL_1_16;
		break;
	case 2:
		fe_params->guard_interval = GUARD_INTERVAL_1_8;
		break;
	case 3:
		fe_params->guard_interval = GUARD_INTERVAL_1_4;
		break;
	}

	// hierarchy
	switch ((tda1004x_read_byte(state, TDA1004X_OUT_CONF1) & 0x60) >> 5) {
	case 0:
		fe_params->hierarchy = HIERARCHY_NONE;
		break;
	case 1:
		fe_params->hierarchy = HIERARCHY_1;
		break;
	case 2:
		fe_params->hierarchy = HIERARCHY_2;
		break;
	case 3:
		fe_params->hierarchy = HIERARCHY_4;
		break;
	}

	return 0;
}