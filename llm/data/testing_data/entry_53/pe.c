/*
 * Cryptographic API.
 *
 * Glue code for the SHA1 Secure Hash Algorithm assembler implementation using
 * Supplemental SSE3 instructions.
 *
 * This file is based on sha1_generic.c
 *
 * Copyright (c) Alan Smithee.
 * Copyright (c) Andrew McDonald <andrew@mcdonald.org.uk>
 * Copyright (c) Jean-Francois Dive <jef@linuxbe.org>
 * Copyright (c) Mathias Krause <minipli@googlemail.com>
 * Copyright (c) Chandramouli Narayanan <mouli@linux.intel.com>
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the Free
 * Software Foundation; either version 2 of the License, or (at your option)
 * any later version.
 *
 */

#define pr_fmt(fmt)	KBUILD_MODNAME ": " fmt

#include <crypto/internal/hash.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/mm.h>
#include <linux/cryptohash.h>
#include <linux/types.h>
#include <crypto/sha.h>
#include <asm/byteorder.h>
#include <asm/i387.h>
#include <asm/xcr.h>
#include <asm/xsave.h>


asmlinkage void sha1_transform_ssse3(u32 *digest, const char *data,
				     unsigned int rounds);
#ifdef CONFIG_AS_AVX
asmlinkage void sha1_transform_avx(u32 *digest, const char *data,
				   unsigned int rounds);
#endif
#ifdef CONFIG_AS_AVX2
#define SHA1_AVX2_BLOCK_OPTSIZE	4	/* optimal 4*64 bytes of SHA1 blocks */

asmlinkage void sha1_transform_avx2(u32 *digest, const char *data,
				unsigned int rounds);
#endif

static asmlinkage void (*sha1_transform_asm)(u32 *, const char *, unsigned int);


static int sha1_ssse3_init(struct shash_desc *desc)
{
	struct sha1_state *sctx = shash_desc_ctx(desc);

	*sctx = (struct sha1_state){
		.state = { SHA1_H0, SHA1_H1, SHA1_H2, SHA1_H3, SHA1_H4 },
	};

	return 0;
}

static int __sha1_ssse3_update(struct shash_desc *desc, const u8 *data,
			       unsigned int len, unsigned int partial)
{
	struct sha1_state *sctx = shash_desc_ctx(desc);
	unsigned int done = 0;

	sctx->count += len;

	if (partial) {
		done = SHA1_BLOCK_SIZE - partial;
		memcpy(sctx->buffer + partial, data, done);
		sha1_transform_asm(sctx->state, sctx->buffer, 1);
	}

	if (len - done >= SHA1_BLOCK_SIZE) {
		const unsigned int rounds = (len - done) / SHA1_BLOCK_SIZE;

		sha1_transform_asm(sctx->state, data + done, rounds);
		done += rounds * SHA1_BLOCK_SIZE;
	}

	memcpy(sctx->buffer, data + done, len - done);

	return 0;
}

static int sha1_ssse3_update(struct shash_desc *desc, const u8 *data,
			     unsigned int len)
{
	struct sha1_state *sctx = shash_desc_ctx(desc);
	unsigned int partial = sctx->count % SHA1_BLOCK_SIZE;
	int res;

	/* Handle the fast case right here */
	if (partial + len < SHA1_BLOCK_SIZE) {
		sctx->count += len;
		memcpy(sctx->buffer + partial, data, len);

		return 0;
	}

	if (!irq_fpu_usable()) {
		res = crypto_sha1_update(desc, data, len);
	} else {
		kernel_fpu_begin();
		res = __sha1_ssse3_update(desc, data, len, partial);
		kernel_fpu_end();
	}

	return res;
}


/* Add padding and return the message digest. */
static int sha1_ssse3_final(struct shash_desc *desc, u8 *out)
{
	struct sha1_state *sctx = shash_desc_ctx(desc);
	unsigned int i, index, padlen;
	__be32 *dst = (__be32 *)out;
	__be64 bits;
	static const u8 padding[SHA1_BLOCK_SIZE] = { 0x80, };

	bits = cpu_to_be64(sctx->count << 3);

	/* Pad out to 56 mod 64 and append length */
	index = sctx->count % SHA1_BLOCK_SIZE;
	padlen = (index < 56) ? (56 - index) : ((SHA1_BLOCK_SIZE+56) - index);
	if (!irq_fpu_usable()) {
		crypto_sha1_update(desc, padding, padlen);
		crypto_sha1_update(desc, (const u8 *)&bits, sizeof(bits));
	} else {
		kernel_fpu_begin();
		/* We need to fill a whole block for __sha1_ssse3_update() */
		if (padlen <= 56) {
			sctx->count += padlen;
			memcpy(sctx->buffer + index, padding, padlen);
		} else {
			__sha1_ssse3_update(desc, padding, padlen, index);
		}
		__sha1_ssse3_update(desc, (const u8 *)&bits, sizeof(bits), 56);
		kernel_fpu_end();
	}

	/* Store state in digest */
	for (i = 0; i < 5; i++)
		dst[i] = cpu_to_be32(sctx->state[i]);

	/* Wipe context */
	memset(sctx, 0, sizeof(*sctx));

	return 0;
}

static int sha1_ssse3_export(struct shash_desc *desc, void *out)
{
	struct sha1_state *sctx = shash_desc_ctx(desc);

	memcpy(out, sctx, sizeof(*sctx));

	return 0;
}

static int sha1_ssse3_import(struct shash_desc *desc, const void *in)
{
	struct sha1_state *sctx = shash_desc_ctx(desc);

	memcpy(sctx, in, sizeof(*sctx));

	return 0;
}

#ifdef CONFIG_AS_AVX2
static void sha1_apply_transform_avx2(u32 *digest, const char *data,
				unsigned int rounds)
{
	/* Select the optimal transform based on data block size */
	if (rounds >= SHA1_AVX2_BLOCK_OPTSIZE)
		sha1_transform_avx2(digest, data, rounds);
	else
		sha1_transform_avx(digest, data, rounds);
}
#endif

static struct shash_alg alg = {
	.digestsize	=	SHA1_DIGEST_SIZE,
	.init		=	sha1_ssse3_init,
	.update		=	sha1_ssse3_update,
	.final		=	sha1_ssse3_final,
	.export		=	sha1_ssse3_export,
	.import		=	sha1_ssse3_import,
	.descsize	=	sizeof(struct sha1_state),
	.statesize	=	sizeof(struct sha1_state),
	.base		=	{
		.cra_name	=	"sha1",
		.cra_driver_name=	"sha1-ssse3",
		.cra_priority	=	150,
		.cra_flags	=	CRYPTO_ALG_TYPE_SHASH,
		.cra_blocksize	=	SHA1_BLOCK_SIZE,
		.cra_module	=	THIS_MODULE,
	}
};

#ifdef CONFIG_AS_AVX
static bool __init avx_usable(void)
{
	u64 xcr0;

	if (!cpu_has_avx || !cpu_has_osxsave)
		return false;

	xcr0 = xgetbv(XCR_XFEATURE_ENABLED_MASK);
	if ((xcr0 & (XSTATE_SSE | XSTATE_YMM)) != (XSTATE_SSE | XSTATE_YMM)) {
		pr_info("AVX detected but unusable.\n");

		return false;
	}

	return true;
}

#ifdef CONFIG_AS_AVX2
static bool __init avx2_usable(void)
{
	if (false && avx_usable() && cpu_has_avx2 &&
	    boot_cpu_has(X86_FEATURE_BMI1) &&
	    boot_cpu_has(X86_FEATURE_BMI2))
		return true;

	return false;
}
#endif
#endif

static int __init sha1_ssse3_mod_init(void)
{
	char *algo_name;

	/* test for SSSE3 first */
	if (cpu_has_ssse3) {
		sha1_transform_asm = sha1_transform_ssse3;
		algo_name = "SSSE3";
	}

#ifdef CONFIG_AS_AVX
	/* allow AVX to override SSSE3, it's a little faster */
	if (avx_usable()) {
		sha1_transform_asm = sha1_transform_avx;
		algo_name = "AVX";
#ifdef CONFIG_AS_AVX2
		/* allow AVX2 to override AVX, it's a little faster */
		if (avx2_usable()) {
			sha1_transform_asm = sha1_apply_transform_avx2;
			algo_name = "AVX2";
		}
#endif
	}
#endif

	if (sha1_transform_asm) {
		pr_info("Using %s optimized SHA-1 implementation\n", algo_name);
		return crypto_register_shash(&alg);
	}
	pr_info("Neither AVX nor AVX2 nor SSSE3 is available/usable.\n");

	return -ENODEV;
}

static void __exit sha1_ssse3_mod_fini(void)
{
	crypto_unregister_shash(&alg);
}

module_init(sha1_ssse3_mod_init);
module_exit(sha1_ssse3_mod_fini);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("SHA1 Secure Hash Algorithm, Supplemental SSE3 accelerated");

MODULE_ALIAS_CRYPTO("sha1");
