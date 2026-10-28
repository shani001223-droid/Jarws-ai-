"""Historical release metadata and bounded daily yield context, not causal signals."""
from datetime import datetime
from zoneinfo import ZoneInfo
from v3_macro_evidence import rate_endpoint

RELEASES={
 'employment_2024':{'kind':'employment','reference_period':'2023-12',
  'source_url':'https://www.bls.gov/news.release/archives/empsit_01052024.htm',
  'stated_release_local':'2024-01-05T08:30:00-05:00','stated_release_utc':'2024-01-05T13:30:00+00:00',
  'reported_fields':{'nonfarm_payroll_change_persons_sa':216000,'unemployment_percent':3.7}},
 'cpi_2022':{'kind':'cpi','reference_period':'2022-09',
  'source_url':'https://www.bls.gov/news.release/archives/cpi_10132022.htm',
  'stated_release_local':'2022-10-13T08:30:00-04:00','stated_release_utc':'2022-10-13T12:30:00+00:00',
  'reported_fields':{'headline_monthly_percent_sa':.4,'headline_yearly_percent_nsa':8.2,
                     'ex_food_energy_monthly_percent_sa':.6,'ex_food_energy_yearly_percent_nsa':6.6}},
 'fomc_2024':{'kind':'fomc','reference_period':'2024-09-18 decision',
  'source_url':'https://www.federalreserve.gov/newsevents/pressreleases/monetary20240918a.htm',
  'stated_release_local':'2024-09-18T14:00:00-04:00','stated_release_utc':'2024-09-18T18:00:00+00:00',
  'reported_fields':{'target_lower_percent':4.75,'target_upper_percent':5.0,'target_change_basis_points':-50}},
}
WINDOWS={'employment_2024':('2024-01-04','2024-01-08'),
         'cpi_2022':('2022-10-12','2022-10-14'),'fomc_2024':('2024-09-17','2024-09-20')}


def event_context(release,captures):
    assert set(captures)=={'DGS2','DGS10'}
    assert all(v['series']==k for k,v in captures.items())
    starts={v['requested_start'] for v in captures.values()};ends={v['requested_end'] for v in captures.values()}
    assert len(starts)==len(ends)==1
    local=datetime.fromisoformat(release['stated_release_local'])
    utc=datetime.fromisoformat(release['stated_release_utc'])
    assert local.utcoffset() is not None and utc.utcoffset() is not None
    assert local==utc and local.isoformat()==local.astimezone(ZoneInfo('America/New_York')).isoformat()
    assert next(iter(starts))<local.date().isoformat()<next(iter(ends))
    rates={k:rate_endpoint(v) for k,v in captures.items()}
    return {'method':'hoshi-stated-release-versus-retrospective-daily-yield-context-1',
            'release':release,'rates':rates,'original_network_arrival_time':None,
            'consensus_snapshot':None,'surprise':None,'synchronized_intraday_reaction':None,
            'daily_observations_are_causal_announcement_effect':False,
            'original_rate_vintage_verified':False,'bond_price_return':None,
            'decision':'WAIT','win_probability':None,'orders_enabled':False}


def check_receipt(payload,root=None):
    assert payload['schema_version']=='hoshi-v3-news-events-1'
    assert payload['use']=='historical-release-research-not-runtime-feed-or-causal-trading-evaluation'
    cases=payload['scheduled_release_cases'];assert len(cases)==3
    assert {e['id'] for e in cases}==set(RELEASES)
    for e in cases:
        assert e['release']==RELEASES[e['id']]
        start,end=WINDOWS[e['id']]
        assert all(v['requested_start']==start and v['requested_end']==end for v in e['captures'].values())
        assert event_context(e['release'],e['captures'])==e['diagnostic']
    return cases
