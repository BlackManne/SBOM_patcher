

int fscrypt_process_policy(struct file *filp,
				const struct fscrypt_policy *policy)
{
	struct inode *inode = file_inode(filp);
	int ret;

	if (!inode_owner_or_capable(inode))
		return -EACCES;

	if (policy->version != 0)
		return -EINVAL;

	ret = mnt_want_write_file(filp);
	if (ret)
		return ret;

	inode_lock(inode);

	if (!inode_has_encryption_context(inode)) {
		if (!S_ISDIR(inode->i_mode))
			ret = -EINVAL;
		else if (!inode->i_sb->s_cop->empty_dir)
			ret = -EOPNOTSUPP;
		else if (!inode->i_sb->s_cop->empty_dir(inode))
			ret = -ENOTEMPTY;
		else
			ret = create_encryption_context_from_policy(inode,
								    policy);
	} else if (!is_encryption_context_consistent_with_policy(inode,
								 policy)) {
		printk(KERN_WARNING
		       "%s: Policy inconsistent with encryption context\n",
		       __func__);
		ret = -EINVAL;
	}

	inode_unlock(inode);

	mnt_drop_write_file(filp);
	return ret;
}