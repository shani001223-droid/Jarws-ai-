"""Original synthetic risk arithmetic, never historical trades or calibration.

No market requests, orders, leverage or runtime integration. Probabilities and
return paths below are invented mathematical fixtures, not estimated evidence.
"""
import math


def _number(x,lower,upper):
    assert type(x) in (int,float) and math.isfinite(x) and lower<=x<=upper
    return float(x)


def binary_kelly(p,net_win):
    p=_number(p,0,1);b=_number(net_win,1e-9,1000)
    assert 0<p<1
    return max(0.0,(p*b-(1-p))/b)


def expected_log_growth(p,net_win,fraction):
    p=_number(p,0,1);b=_number(net_win,1e-9,1000);f=_number(fraction,0,1)
    assert 0<p<1 and f<1
    return p*math.log1p(b*f)+(1-p)*math.log1p(-f)


def loss_run_probability(p,trials,length):
    """P(at least one loss run), finite iid Bernoulli fixture, exact DP not MC."""
    p=_number(p,0,1)
    assert type(trials) is int and 0<=trials<=1000
    assert type(length) is int and 1<=length<=100
    state=[1.0]+[0.0]*(length-1)
    for _ in range(trials):
        nxt=[math.fsum(state)*p]+[0.0]*(length-1)
        for j in range(length-1):nxt[j+1]=state[j]*(1-p)
        state=nxt
    return min(1.0,max(0.0,1-math.fsum(state)))


def wealth_path(initial,net_returns):
    initial=_number(initial,1e-9,1e9)
    assert isinstance(net_returns,list) and 0<len(net_returns)<=2000
    wealth=peak=initial;maximum=0.0;marks=[]
    for r in net_returns:
        r=_number(r,-1,100)
        wealth*=1+r;assert math.isfinite(wealth)
        peak=max(peak,wealth);dd=1-wealth/peak;maximum=max(maximum,dd)
        marks.append({'equity':wealth,'drawdown_fraction':dd})
    return {'ending_equity':wealth,'maximum_drawdown_fraction':maximum,'marks':marks,
            'returns_are_synthetic_net_assumptions':True,'observed_trade_fills':None}


def two_asset_variance(weights,cov):
    """Original cash-constrained two-asset algebra, not an optimizer."""
    assert isinstance(weights,list) and len(weights)==2
    assert isinstance(cov,list) and len(cov)==2 and all(isinstance(r,list) and len(r)==2 for r in cov)
    a,b=(_number(x,0,1) for x in weights);assert a+b<=1
    v1,v2=_number(cov[0][0],0,100),_number(cov[1][1],0,100)
    c=_number(cov[0][1],-100,100);assert _number(cov[1][0],-100,100)==c
    assert v1*v2>=c*c-1e-14
    return a*a*v1+2*a*b*c+b*b*v2


def illustrations():
    p=.55;b=1;k=binary_kelly(p,b)
    return {'method':'hoshi-synthetic-log-growth-streak-and-portfolio-1',
            'kelly':{'assumed_p':p,'assumed_net_win_per_unit_risk':b,'unconstrained_binary_fraction':k,
                     'log_growth_at_fraction':expected_log_growth(p,b,k),
                     'log_growth_at_double_fraction':expected_log_growth(p,b,2*k),
                     'log_growth_if_true_p_were_0_51':expected_log_growth(.51,b,k)},
            'streak':{'assumed_p':p,'trials':100,'loss_run_length':10,
                      'one_specified_ten_loss_block_probability':(1-p)**10,
                      'at_least_one_run_probability':loss_run_probability(p,100,10)},
            'ten_losses':{'fraction_0_1':wealth_path(100,[-.1]*10),
                          'fraction_0_05':wealth_path(100,[-.05]*10)},
            'portfolio':{'weights':[.5,.5],'individual_variance_assumption':.04,
                         'zero_correlation_variance':two_asset_variance([.5,.5],[[.04,0],[0,.04]]),
                         'perfect_positive_correlation_variance':two_asset_variance([.5,.5],[[.04,.04],[.04,.04]])},
            'historical_price_or_trade_inputs':None,'win_probability':None,
            'decision':'WAIT','orders_enabled':False,'production_calibration':None}


def check_receipt(payload,root=None):
    assert payload['schema_version']=='hoshi-v3-synthetic-risk-1'
    assert payload['use']=='synthetic-mathematical-education-not-market-evaluation-or-runtime'
    assert payload['diagnostic']==illustrations()
    return payload['diagnostic']
