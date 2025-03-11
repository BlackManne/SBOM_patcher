

int sctp_transport_lookup_process(int (*cb)(struct sctp_transport *, void *),
				  struct net *net,
				  const union sctp_addr *laddr,
				  const union sctp_addr *paddr, void *p)
{
	struct sctp_transport *transport;
	int err = -ENOENT;

	rcu_read_lock();
	transport = sctp_addrs_lookup_transport(net, laddr, paddr);
	if (!transport || !sctp_transport_hold(transport))
		goto out;

	rcu_read_unlock();
	err = cb(transport, p);
	sctp_transport_put(transport);

out:
	return err;
}