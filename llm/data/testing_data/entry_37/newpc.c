

int
snd_seq_oss_open(struct file *file, int level)
{
	int i, rc;
	struct seq_oss_devinfo *dp;

	dp = kzalloc(sizeof(*dp), GFP_KERNEL);
	if (!dp) {
		snd_printk(KERN_ERR "can't malloc device info\n");
		return -ENOMEM;
	}
	debug_printk(("oss_open: dp = %p\n", dp));

	dp->cseq = system_client;
	dp->port = -1;
	dp->queue = -1;

	for (i = 0; i < SNDRV_SEQ_OSS_MAX_CLIENTS; i++) {
		if (client_table[i] == NULL)
			break;
	}

	dp->index = i;
	if (i >= SNDRV_SEQ_OSS_MAX_CLIENTS) {
		snd_printk(KERN_ERR "too many applications\n");
		rc = -ENOMEM;
		goto _error;
	}

	/* look up synth and midi devices */
	snd_seq_oss_synth_setup(dp);
	snd_seq_oss_midi_setup(dp);

	if (dp->synth_opened == 0 && dp->max_mididev == 0) {
		/* snd_printk(KERN_ERR "no device found\n"); */
		rc = -ENODEV;
		goto _error;
	}

	/* create port */
	debug_printk(("create new port\n"));
	rc = create_port(dp);
	if (rc < 0) {
		snd_printk(KERN_ERR "can't create port\n");
		goto _error;
	}

	/* allocate queue */
	debug_printk(("allocate queue\n"));
	rc = alloc_seq_queue(dp);
	if (rc < 0)
		goto _error;

	/* set address */
	dp->addr.client = dp->cseq;
	dp->addr.port = dp->port;
	/*dp->addr.queue = dp->queue;*/
	/*dp->addr.channel = 0;*/

	dp->seq_mode = level;

	/* set up file mode */
	dp->file_mode = translate_mode(file);

	/* initialize read queue */
	debug_printk(("initialize read queue\n"));
	if (is_read_mode(dp->file_mode)) {
		dp->readq = snd_seq_oss_readq_new(dp, maxqlen);
		if (!dp->readq) {
			rc = -ENOMEM;
			goto _error;
		}
	}

	/* initialize write queue */
	debug_printk(("initialize write queue\n"));
	if (is_write_mode(dp->file_mode)) {
		dp->writeq = snd_seq_oss_writeq_new(dp, maxqlen);
		if (!dp->writeq) {
			rc = -ENOMEM;
			goto _error;
		}
	}

	/* initialize timer */
	debug_printk(("initialize timer\n"));
	dp->timer = snd_seq_oss_timer_new(dp);
	if (!dp->timer) {
		snd_printk(KERN_ERR "can't alloc timer\n");
		rc = -ENOMEM;
		goto _error;
	}
	debug_printk(("timer initialized\n"));

	/* set private data pointer */
	file->private_data = dp;

	/* set up for mode2 */
	if (level == SNDRV_SEQ_OSS_MODE_MUSIC)
		snd_seq_oss_synth_setup_midi(dp);
	else if (is_read_mode(dp->file_mode))
		snd_seq_oss_midi_open_all(dp, SNDRV_SEQ_OSS_FILE_READ);

	client_table[dp->index] = dp;
	num_clients++;

	debug_printk(("open done\n"));
	return 0;

 _error:
	snd_seq_oss_synth_cleanup(dp);
	snd_seq_oss_midi_cleanup(dp);
	delete_seq_queue(dp->queue);
	delete_port(dp);

	return rc;
}