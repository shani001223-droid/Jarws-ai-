"use strict";
// Synthetic fixtures only; never historical market observations.
const expected={symbol:"BTCUSDT",equity_usdt:100,risk_pct:.5,fee_bps:10,slippage_bps:5};
const NOW=1800000000000;
function fixture(){
  const frames=Object.fromEntries(["15m","1h","4h"].map(tf=>[tf,{last_closed_at:NOW-1000,last_close:1000,support:990,resistance:1020,rsi14:60,ema20:980,ema50:970,atr14:10}]));
  const keys=["htf_trend","liquidity_target","location_order_block","fvg_retest","killzone_time"],families=["confirmed_structure","ema_trend","rsi_momentum","volume_participation","session_vwap","atr_volatility_guard"];
  const times=Object.fromEntries(Object.keys(frames).map(tf=>[tf,NOW-1000]));
  return {version:"hoshi-trading-desk-v1",symbol:"BTCUSDT",market:"spot",mode:"paper-assistant-only",orders_enabled:false,win_probability:null,independently_cross_checked:false,direction:"long_study_only",price_kind:"last_closed_candle_not_live_quote",knowledge_version:"hoshi-trading-knowledge-v2",v3_runtime_integration:"pending",as_of_ms:NOW,fetched_at:NOW/1000,expires_at_ms:NOW+60000,source:"synthetic test fixture",assumptions:{equity_usdt:100,risk_pct:.5,fee_bps_each_side:10,adverse_slippage_bps_each_side:5},timeframes:frames,decision:"wait",paper_plan:null,confluence:{version:"hoshi-confluence-v2",symbol:"BTCUSDT",market:"spot",orders_enabled:false,win_probability:null,direction:"long",as_of:NOW,score_semantics:"weighted_rule_coverage_not_win_probability",score:0,score_max:100,decision:"wait",last_closed_at:times,evidence:Object.fromEntries(keys.map(k=>[k,{passed:false,weight:20,points:0}]))},setup:{version:"spot-setup-assessment-v1",symbol:"BTCUSDT",orders_enabled:false,families_checked:6,positive_families:0,decision:"wait",last_closed_at:times,evidence:Object.fromEntries(families.map(k=>[k,{status:"does_not_support"}]))}};
}

module.exports={fixture,expected,NOW};
