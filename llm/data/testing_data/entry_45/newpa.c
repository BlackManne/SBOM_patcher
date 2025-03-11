

static int rtc_timer_enqueue(struct rtc_device *rtc, struct rtc_timer *timer)
{
	struct timerqueue_node *next = timerqueue_getnext(&rtc->timerqueue);
	struct rtc_time tm;
	ktime_t now;

	timer->enabled = 1;
	__rtc_read_time(rtc, &tm);
	now = rtc_tm_to_ktime(tm);

	/* Skip over expired timers */
	while (next) {
		if (next->expires >= now)
			break;
		next = timerqueue_iterate_next(next);
	}

	timerqueue_add(&rtc->timerqueue, &timer->node);
	if (!next) {
		struct rtc_wkalrm alarm;
		int err;
		alarm.time = rtc_ktime_to_tm(timer->node.expires);
		alarm.enabled = 1;
		err = __rtc_set_alarm(rtc, &alarm);
		if (err == -ETIME) {
			pm_stay_awake(rtc->dev.parent);
			schedule_work(&rtc->irqwork);
		} else if (err) {
			timerqueue_del(&rtc->timerqueue, &timer->node);
			timer->enabled = 0;
			return err;
		}
	}
	return 0;
}