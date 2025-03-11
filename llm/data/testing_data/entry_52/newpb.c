

int sctp_transport_lookup_process(int (*cb)(struct sctp_transport *, void *),
				  struct net *net,
				  const union sctp_addr *laddr,
				  const union sctp_addr *paddr, void *p)
{
	struct sctp_transport *transport;
	int err;

	rcu_read_lock();
	transport = sctp_addrs_lookup_transport(net, laddr, paddr);
	rcu_read_unlock();
	if (!transport)
		return -ENOENT;

	err = cb(transport, p);
	sctp_transport_put(transport);

	return err;
}