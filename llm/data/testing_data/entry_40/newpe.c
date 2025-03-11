

static int crypt_alloc_tfms(struct crypt_config *cc, char *ciphermode)
{
	unsigned i;
	int err;

	cc->tfms = kzalloc(cc->tfms_count * sizeof(struct crypto_ablkcipher *),
			   GFP_KERNEL);
	if (!cc->tfms)
		return -ENOMEM;

	for (i = 0; i < cc->tfms_count; i++) {
		cc->tfms[i] = crypto_alloc_ablkcipher(ciphermode, 0, 0);
		if (IS_ERR(cc->tfms[i])) {
			err = PTR_ERR(cc->tfms[i]);
			crypt_free_tfms(cc);
			return err;
		}
	}

	return 0;
}