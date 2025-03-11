

static void iwl_mvm_mac_tx(struct ieee80211_hw *hw,
			   struct ieee80211_tx_control *control,
			   struct sk_buff *skb)
{
	struct iwl_mvm *mvm = IWL_MAC80211_GET_MVM(hw);
	struct ieee80211_sta *sta = control->sta;
	struct ieee80211_tx_info *info = IEEE80211_SKB_CB(skb);
	struct ieee80211_hdr *hdr = (void *)skb->data;

	if (iwl_mvm_is_radio_killed(mvm)) {
		IWL_DEBUG_DROP(mvm, "Dropping - RF/CT KILL\n");
		goto drop;
	}

	if (IEEE80211_SKB_CB(skb)->hw_queue == IWL_MVM_OFFCHANNEL_QUEUE &&
	    !test_bit(IWL_MVM_STATUS_ROC_RUNNING, &mvm->status))
		goto drop;

	/* treat non-bufferable MMPDUs as broadcast if sta is sleeping */
	if (unlikely(info->flags & IEEE80211_TX_CTL_NO_PS_BUFFER &&
		     ieee80211_is_mgmt(hdr->frame_control) &&
		     !ieee80211_is_bufferable_mmpdu(hdr->frame_control)))
		sta = NULL;

	if (sta) {
		if (iwl_mvm_defer_tx(mvm, sta, skb))
			return;
		if (iwl_mvm_tx_skb(mvm, skb, sta))
			goto drop;
		return;
	}

	if (iwl_mvm_tx_skb_non_sta(mvm, skb))
		goto drop;
	return;
 drop:
	ieee80211_free_txskb(hw, skb);
}