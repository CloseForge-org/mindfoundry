#!/usr/bin/env python3
from hotel_sim.live_ops import TYPE_OWNER, render_summary
from hotel_sim.replicants import retrieve


def test_owner_mapping_core_incident_types():
    assert TYPE_OWNER['billing'].startswith('Annie Chang')
    assert TYPE_OWNER['noise'].startswith('Kevin Huang')
    assert TYPE_OWNER['safety'].startswith('Maya Chen')
    assert 'Leo Wang' in TYPE_OWNER['access']


def test_live_summary_renders():
    s = render_summary()
    assert 'NeMo Lodge live ops summary' in s
    assert 'Owner queues' in s


def test_retrieve_billing_routes_finance():
    r = retrieve('guest says they were double charged, who handles billing?', 4)
    roles = [x['role'] for x in r['recommended_route']]
    assert 'Finance/Admin' in roles


if __name__ == '__main__':
    test_owner_mapping_core_incident_types(); test_live_summary_renders(); test_retrieve_billing_routes_finance(); print('ok')
