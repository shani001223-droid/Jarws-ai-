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

function makePaperPlan(){
  // Synthetic, internally consistent paper arithmetic; NOT market evidence.
  const reference=1000,support=990,atr=10,fee=.001,slip=.0005;
  const stop=support-Math.max(.25*atr,.001*reference),distance=reference-stop;
  const entry=reference*(1+slip),stopFill=stop*(1-slip);
  const lossUnit=entry-stopFill+fee*(entry+stopFill),budget=.5;
  const quantity=Math.floor(Math.min(budget/lossUnit,100/(entry*(1+fee)))*1e8)/1e8;
  const targets=[1,2].map(multiple=>{
    const target=reference+multiple*distance,exit=target*(1-slip);
    const gain=exit-entry-fee*(entry+exit);
    return {multiple_before_costs:multiple,reference_price:target,estimated_net_pnl_usdt:quantity*gain,estimated_net_reward_risk:gain/lossUnit};
  });
  return {side:"long",fills_simulated:false,exchange_order_validated:false,
    reference_entry_close:reference,confirmed_support:support,reference_stop:stop,
    stop_method:"confirmed_15m_support_minus_max_quarter_atr_or_0_1pct",
    estimated_entry_with_slippage:entry,estimated_stop_fill_with_slippage:stopFill,
    stop_distance_pct:distance/reference*100,estimated_quantity_base:quantity,
    estimated_notional_usdt:quantity*entry,risk_budget_usdt:budget,
    estimated_stop_loss_including_costs_usdt:quantity*lossUnit,
    equity_usdt:100,risk_pct:.5,assumed_fee_bps_each_side:10,
    assumed_adverse_slippage_bps_each_side:5,targets};
}
module.exports={fixture,expected,NOW,makePaperPlan};
