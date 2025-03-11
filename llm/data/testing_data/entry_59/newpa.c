

static int ip6_route_multipath_add(struct fib6_config *cfg,
				   struct netlink_ext_ack *extack)
{
	struct fib6_info *rt_notif = NULL, *rt_last = NULL;
	struct nl_info *info = &cfg->fc_nlinfo;
	struct fib6_config r_cfg;
	struct rtnexthop *rtnh;
	struct fib6_info *rt;
	struct rt6_nh *err_nh;
	struct rt6_nh *nh, *nh_safe;
	__u16 nlflags;
	int remaining;
	int attrlen;
	int err = 1;
	int nhn = 0;
	int replace = (cfg->fc_nlinfo.nlh &&
		       (cfg->fc_nlinfo.nlh->nlmsg_flags & NLM_F_REPLACE));
	LIST_HEAD(rt6_nh_list);

	nlflags = replace ? NLM_F_REPLACE : NLM_F_CREATE;
	if (info->nlh && info->nlh->nlmsg_flags & NLM_F_APPEND)
		nlflags |= NLM_F_APPEND;

	remaining = cfg->fc_mp_len;
	rtnh = (struct rtnexthop *)cfg->fc_mp;

	/* Parse a Multipath Entry and build a list (rt6_nh_list) of
	 * fib6_info structs per nexthop
	 */
	while (rtnh_ok(rtnh, remaining)) {
		memcpy(&r_cfg, cfg, sizeof(*cfg));
		if (rtnh->rtnh_ifindex)
			r_cfg.fc_ifindex = rtnh->rtnh_ifindex;

		attrlen = rtnh_attrlen(rtnh);
		if (attrlen > 0) {
			struct nlattr *nla, *attrs = rtnh_attrs(rtnh);

			nla = nla_find(attrs, attrlen, RTA_GATEWAY);
			if (nla) {
				r_cfg.fc_gateway = nla_get_in6_addr(nla);
				r_cfg.fc_flags |= RTF_GATEWAY;
			}
			r_cfg.fc_encap = nla_find(attrs, attrlen, RTA_ENCAP);
			nla = nla_find(attrs, attrlen, RTA_ENCAP_TYPE);
			if (nla)
				r_cfg.fc_encap_type = nla_get_u16(nla);
		}

		r_cfg.fc_flags |= (rtnh->rtnh_flags & RTNH_F_ONLINK);
		rt = ip6_route_info_create(&r_cfg, GFP_KERNEL, extack);
		if (IS_ERR(rt)) {
			err = PTR_ERR(rt);
			rt = NULL;
			goto cleanup;
		}

		rt->fib6_nh.nh_weight = rtnh->rtnh_hops + 1;

		err = ip6_route_info_append(info->nl_net, &rt6_nh_list,
					    rt, &r_cfg);
		if (err) {
			fib6_info_release(rt);
			goto cleanup;
		}

		rtnh = rtnh_next(rtnh, &remaining);
	}

	/* for add and replace send one notification with all nexthops.
	 * Skip the notification in fib6_add_rt2node and send one with
	 * the full route when done
	 */
	info->skip_notify = 1;

	err_nh = NULL;
	list_for_each_entry(nh, &rt6_nh_list, next) {
		err = __ip6_ins_rt(nh->fib6_info, info, extack);
		fib6_info_release(nh->fib6_info);

		if (!err) {
			/* save reference to last route successfully inserted */
			rt_last = nh->fib6_info;

			/* save reference to first route for notification */
			if (!rt_notif)
				rt_notif = nh->fib6_info;
		}

		/* nh->fib6_info is used or freed at this point, reset to NULL*/
		nh->fib6_info = NULL;
		if (err) {
			if (replace && nhn)
				ip6_print_replace_route_err(&rt6_nh_list);
			err_nh = nh;
			goto add_errout;
		}

		/* Because each route is added like a single route we remove
		 * these flags after the first nexthop: if there is a collision,
		 * we have already failed to add the first nexthop:
		 * fib6_add_rt2node() has rejected it; when replacing, old
		 * nexthops have been replaced by first new, the rest should
		 * be added to it.
		 */
		cfg->fc_nlinfo.nlh->nlmsg_flags &= ~(NLM_F_EXCL |
						     NLM_F_REPLACE);
		nhn++;
	}

	/* success ... tell user about new route */
	ip6_route_mpath_notify(rt_notif, rt_last, info, nlflags);
	goto cleanup;

add_errout:
	/* send notification for routes that were added so that
	 * the delete notifications sent by ip6_route_del are
	 * coherent
	 */
	if (rt_notif)
		ip6_route_mpath_notify(rt_notif, rt_last, info, nlflags);

	/* Delete routes that were already added */
	list_for_each_entry(nh, &rt6_nh_list, next) {
		if (err_nh == nh)
			break;
		ip6_route_del(&nh->r_cfg, extack);
	}

cleanup:
	list_for_each_entry_safe(nh, nh_safe, &rt6_nh_list, next) {
		if (nh->fib6_info)
			fib6_info_release(nh->fib6_info);
		list_del(&nh->next);
		kfree(nh);
	}

	return err;
}