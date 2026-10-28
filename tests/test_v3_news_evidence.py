"""Actual release clocks, vintage limits, rate units and fail-closed provenance."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import v3_news_evidence as f


def receipt():return json.loads((ROOT/'knowledge_base/11_NEWS_TRADING/news_events_20261028.json').read_text())


class V3NewsTests(unittest.TestCase):
    def test_winter_summer_release_clocks_and_economic_reference_months_differ(self):
        p=receipt();f.check_receipt(p);a,b,c=p['scheduled_release_cases']
        self.assertEqual(a['release']['stated_release_utc'],'2024-01-05T13:30:00+00:00')
        self.assertEqual(b['release']['stated_release_utc'],'2022-10-13T12:30:00+00:00')
        self.assertEqual(a['release']['reference_period'],'2023-12')
        self.assertEqual(c['release']['reported_fields']['target_change_basis_points'],-50)

    def test_known_policy_cut_is_not_a_forced_long_yield_decline(self):
        d=receipt()['scheduled_release_cases'][2]['diagnostic']
        self.assertEqual(d['rates']['DGS10']['change_basis_points'],8)
        self.assertFalse(d['daily_observations_are_causal_announcement_effect'])
        self.assertIsNone(d['bond_price_return'])

    def test_missing_consensus_arrival_and_intraday_response_are_not_zero_surprises(self):
        p=receipt();f.check_receipt(p)
        for e in p['scheduled_release_cases']:
            d=e['diagnostic']
            for key in ('consensus_snapshot','surprise','original_network_arrival_time','synchronized_intraday_reaction','win_probability'):
                self.assertIsNone(d[key])
            self.assertEqual(d['decision'],'WAIT');self.assertFalse(d['orders_enabled'])

    def test_rehashed_missing_rate_endpoint_stays_missing_not_forward_filled(self):
        e=deepcopy(receipt()['scheduled_release_cases'][0]);c=e['captures']['DGS2']
        lines=c['response_body'].splitlines();lines[-1]=lines[-1].split(',')[0]+','
        c['response_body']='\n'.join(lines)+'\n';c['source_sha256']=sha256(c['response_body'].encode()).hexdigest()
        d=f.event_context(e['release'],e['captures'])
        self.assertIsNone(d['rates']['DGS2']['change_basis_points']);self.assertEqual(d['decision'],'WAIT')

    def test_clock_value_source_hash_and_rate_alias_forgery_rejected(self):
        for kind in ('utc','offset','field','url','hash','alias','summary','omission'):
            p=receipt();e=p['scheduled_release_cases'][0]
            if kind=='utc':e['release']['stated_release_utc']='2024-01-05T12:30:00+00:00'
            elif kind=='offset':e['release']['stated_release_local']='2024-01-05T08:30:00-04:00'
            elif kind=='field':e['release']['reported_fields']['nonfarm_payroll_change_persons_sa']=999999
            elif kind=='url':e['release']['source_url']='https://example.org/rumor'
            elif kind=='hash':e['captures']['DGS2']['source_sha256']='0'*64
            elif kind=='alias':e['captures']['DGS2']=deepcopy(e['captures']['DGS10'])
            elif kind=='summary':e['diagnostic']['surprise']=0
            else:p['scheduled_release_cases'].pop()
            with self.assertRaises(AssertionError):f.check_receipt(p)


class V3ShockTests(unittest.TestCase):
    def test_later_certification_or_register_text_is_not_an_earlier_feature(self):
        p=receipt();f.check_receipt(p)
        a,b,c=p['shock_cases']
        self.assertFalse(a['diagnostic']['source_document_postdates_observation_window'])
        self.assertTrue(b['diagnostic']['source_document_postdates_observation_window'])
        self.assertTrue(c['diagnostic']['source_document_postdates_observation_window'])
        self.assertEqual(b['event']['document_date'],'2018-01-09')
        self.assertEqual(b['event']['event_date'],'2016-11-08')

    def test_actual_event_windows_have_different_descriptive_yield_directions(self):
        p=receipt();f.check_receipt(p);a,b,c=p['shock_cases']
        self.assertEqual(a['diagnostic']['rates']['DGS2']['change_basis_points'],-27)
        self.assertEqual(b['diagnostic']['rates']['DGS10']['change_basis_points'],32)
        self.assertEqual(c['diagnostic']['rates']['DGS10']['change_basis_points'],-16)

    def test_unknown_first_news_clock_and_unestimated_causality_cannot_create_signal(self):
        p=receipt();f.check_receipt(p)
        for e in p['shock_cases']:
            d=e['diagnostic']
            for key in ('first_news_time_and_network_arrival','pre_event_probability_or_consensus','causal_return_or_instantaneous_price_response','win_probability'):
                self.assertIsNone(d[key])
            self.assertFalse(d['later_document_is_point_in_time_feature'])
            self.assertEqual(d['decision'],'WAIT');self.assertFalse(d['orders_enabled'])

    def test_relabelled_event_late_source_and_forged_action_rejected(self):
        for kind in ('date','document','source','summary','duplicate'):
            p=receipt();e=p['shock_cases'][1]
            if kind=='date':e['event']['event_date']='2016-11-09'
            elif kind=='document':e['event']['document_date']='2016-11-08'
            elif kind=='source':e['event']['source_url']='https://example.org/certification'
            elif kind=='summary':e['diagnostic']['decision']='SHORT'
            else:p['shock_cases'][1]=deepcopy(p['shock_cases'][0])
            with self.assertRaises(AssertionError):f.check_receipt(p)


if __name__=='__main__':unittest.main()
