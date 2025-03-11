

int iwl_mvm_tx_skb_non_sta(struct iwl_mvm *mvm, struct sk_buff *skb)
{
	struct ieee80211_hdr *hdr = (struct ieee80211_hdr *)skb->data;
	struct ieee80211_tx_info *info = IEEE80211_SKB_CB(skb);
	struct iwl_device_cmd *dev_cmd;
	struct iwl_tx_cmd *tx_cmd;
	u8 sta_id;
	int hdrlen = ieee80211_hdrlen(hdr->frame_control);

	if (WARN_ON_ONCE(info->flags & IEEE80211_TX_CTL_AMPDU))
		return -1;

	if (WARN_ON_ONCE(info->flags & IEEE80211_TX_CTL_SEND_AFTER_DTIM &&
			 (!info->control.vif ||
			  info->hw_queue != info->control.vif->cab_queue)))
		return -1;

	/*
	 * IWL_MVM_OFFCHANNEL_QUEUE is used for ROC packets that can be used
	 * in 2 different types of vifs, P2P & STATION. P2P uses the offchannel
	 * queue. STATION (HS2.0) uses the auxiliary context of the FW,
	 * and hence needs to be sent on the aux queue
	 */
	if (IEEE80211_SKB_CB(skb)->hw_queue == IWL_MVM_OFFCHANNEL_QUEUE &&
	    info->control.vif->type == NL80211_IFTYPE_STATION)
		IEEE80211_SKB_CB(skb)->hw_queue = mvm->aux_queue;

	/*
	 * If the interface on which the frame is sent is the P2P_DEVICE
	 * or an AP/GO interface use the broadcast station associated
	 * with it; otherwise if the interface is a managed interface
	 * use the AP station associated with it for multicast traffic
	 * (this is not possible for unicast packets as a TLDS discovery
	 * response are sent without a station entry); otherwise use the
	 * AUX station.
	 */
	sta_id = mvm->aux_sta.sta_id;
	if (info->control.vif) {
		struct iwl_mvm_vif *mvmvif =
			iwl_mvm_vif_from_mac80211(info->control.vif);

		if (info->control.vif->type == NL80211_IFTYPE_P2P_DEVICE ||
		    info->control.vif->type == NL80211_IFTYPE_AP)
			sta_id = mvmvif->bcast_sta.sta_id;
		else if (info->control.vif->type == NL80211_IFTYPE_STATION &&
			 is_multicast_ether_addr(hdr->addr1)) {
			u8 ap_sta_id = ACCESS_ONCE(mvmvif->ap_sta_id);

			if (ap_sta_id != IWL_MVM_STATION_COUNT)
				sta_id = ap_sta_id;
		}
	}

	IWL_DEBUG_TX(mvm, "station Id %d, queue=%d\n", sta_id, info->hw_queue);

	dev_cmd = iwl_mvm_set_tx_params(mvm, skb, hdrlen, NULL, sta_id);
	if (!dev_cmd)
		return -1;

	/* From now on, we cannot access info->control */
	tx_cmd = (struct iwl_tx_cmd *)dev_cmd->payload;

	/* Copy MAC header from skb into command buffer */
	memcpy(tx_cmd->hdr, hdr, hdrlen);

	if (iwl_trans_tx(mvm->trans, skb, dev_cmd, info->hw_queue)) {
		iwl_trans_free_tx_cmd(mvm->trans, dev_cmd);
		return -1;
	}

	/*
	 * Increase the pending frames counter, so that later when a reply comes
	 * in and the counter is decreased - we don't start getting negative
	 * values.
	 * Note that we don't need to make sure it isn't agg'd, since we're
	 * TXing non-sta
	 */
	atomic_inc(&mvm->pending_frames[sta_id]);

	return 0;
}