

static unsigned bdw_limit_period(struct perf_event *event, unsigned left)
{
	if ((event->hw.config & INTEL_ARCH_EVENT_MASK) ==
			X86_CONFIG(.event=0xc0, .umask=0x01)) {
		if (left < 128)
			left = 128;
		left &= ~0x3fu;
	}
	return left;
}