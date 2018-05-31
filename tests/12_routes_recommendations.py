""" recommendations """
from collections import Counter
from datetime import datetime
from dateutil.parser import parse as parse_date

from utils.config import BLOB_SIZE
from utils.human_ids import dehumanize
from utils.test_utils import API_URL, req, req_with_auth

RECOMMENDATION_URL = API_URL + '/recommendations'


def test_10_put_recommendations_should_work_only_when_logged_in():
    r = req.put(RECOMMENDATION_URL)
    assert r.status_code == 401


def check_recos(recos):
    # ensure we have no duplicates
    ids = list(map(lambda reco: reco['id'], recos))
    assert len(list(filter(lambda v: v>1, Counter(ids).values()))) == 0

    # ensure we have no mediations for which all offers are past their bookingLimitDatetime
    for reco in recos:
        if 'mediatedOccurences' in reco:
            for oc in reco['mediatedOccurences']:
                print("RECO", reco['id'])
                for offer in oc['offers']:
                    print(offer['id'], offer['bookingLimitDatetime'])
                assert not all(offer['bookingLimitDatetime'] is not None and
                               parse_date(offer['bookingLimitDatetime']) <= datetime.now()
                               for offer in oc['offers'])
                # TODO: ensure we have no offers with available slots left
                # TODO: ensure I never see offers I have already booked... unless the booking is canceled
                # TODO: ensure I only see recos for the relevant departementCode
                # TODO: ensure I only see recos for my userId


def subtest_initial_recos():
    r = req_with_auth().put(RECOMMENDATION_URL, json={})
    assert r.status_code == 200
    recos = r.json()
    assert len(recos) <= BLOB_SIZE

    assert recos[0]['mediation']['tutoIndex'] == 0
    assert recos[1]['mediation']['tutoIndex'] == 1

    assert len(list(filter(lambda reco: 'mediation' in reco and
                                        reco['mediation']['tutoIndex'] is not None,
                           recos))) == 2
    check_recos(recos)
    return recos


def subtest_recos_with_params(params,
                              expected_status=200,
                              expected_mediation_id=None,
                              expected_occasion_type=None,
                              expected_occasion_id=None):
    r = req_with_auth().put(RECOMMENDATION_URL+'?'+params, json={})
    assert r.status_code == expected_status
    if expected_status == 200:
        recos = r.json()
        assert len(recos) <= BLOB_SIZE
        assert recos[1]['mediation']['tutoIndex'] is not None
        check_recos(recos)
        return recos


def test_11_put_recommendations_should_return_a_list_of_recos():
    recos1 = subtest_initial_recos()
    recos2 = subtest_initial_recos()
    assert len(recos1) == len(recos2)
    assert range(2, len(recos1)).any(lambda i: recos1[i]['id'] != recos2[i]['id'])


def test_12_if_i_request_a_specific_reco_it_should_be_first():
    # Full request
    subtest_recos_with_params('occasionType=event&occasionId=AE&mediationId=AM',
                           expected_status=200,
                           expected_mediation_id=dehumanize('AM'),
                           expected_occasion_type='event',
                           expected_occasion_id=dehumanize('AE'))
    # No mediationId but occasionId
    subtest_recos_with_params('occasionType=event&occasionId=AE',
                           expected_status=200,
                           expected_mediation_id=dehumanize('AM'),
                           expected_occasion_type='event',
                           expected_occasion_id=dehumanize('AE'))
    # No occasionId but mediationId and occasionType
    subtest_recos_with_params('occasionType=event&mediationId=AE',
                           expected_status=200,
                           expected_mediation_id=dehumanize('AM'),
                           expected_occasion_type='event',
                           expected_occasion_id=dehumanize('AE'))
    # No occasionId, no occasionType, but mediationId
    subtest_recos_with_params('mediationId=AE',
                           expected_status=200,
                           expected_mediation_id=dehumanize('AM'),
                           expected_occasion_type='event',
                           expected_occasion_id=dehumanize('AE'))
    # no occasionType but mediationId and occasionId
    subtest_recos_with_params('occasionId=AE&mediationId=AM',
                           expected_status=200,
                           expected_mediation_id=dehumanize('AM'),
                           expected_occasion_type='event',
                           expected_occasion_id=dehumanize('AE'))


def test_13_requesting_a_reco_with_bad_params_should_return_reponse_anyway():
    # occasionId correct and mediationId correct but not the same event
    subtest_recos_with_params('occasionType=event&occasionId=AQ&mediationId=AE',
                           expected_status=200,
                           expected_mediation_id=dehumanize('AE')) # FIRST TUTO MEDIATION
    # occasionId correct and mediationId correct but not the same occasion type
    subtest_recos_with_params('occasionType=event&occasionId=A9&mediationId=AM',
                           expected_status=200,
                           expected_mediation_id=dehumanize('AE'))
    # invalid (not matching an object) occasionId with valid mediationId
    subtest_recos_with_params('occasionType=event&occasionId=ABCDE&mediationId=AM',
                           expected_status=200,
                           expected_mediation_id=dehumanize('AE'))
    # invalid (not matching an object) mediationId with valid occasionId
    subtest_recos_with_params('occasionType=event&occasionId=AE&mediationId=ABCDE',
                           expected_status=200,
                           expected_mediation_id=dehumanize('AE'))
    # invalid (not matching an object) mediationId with invalid (not matching an object) occasionId
    subtest_recos_with_params('occasionType=event&occasionId=ABCDE&mediationId=ABCDE',
                           expected_status=200,
                           expected_mediation_id=dehumanize('AE'))


def test_14_actual_errors_should_generate_a_400():
    # wrong occasionType
    subtest_recos_with_params('occasionType=invalid',
                           expected_status=400)
    # invalid (not dehumanizable) occasionId with valid mediationId
    subtest_recos_with_params('occasionType=event&occasionId=00&mediationId=AE',
                           expected_status=400)
    # invalid (not dehumanizable) mediationId with valid occasionId
    subtest_recos_with_params('occasionType=event&occasionId=AE&mediationId=00',
                           expected_status=400)
    # invalid (not dehumanizable) mediationId with invalid (not dehumanizable) occasionId
    subtest_recos_with_params('occasionType=event&occasionId=00&mediationId=00',
                           expected_status=400)


def test_15_if_i_request_a_non_existant_reco_it_should_be_created_with_shared_by_userId():
    recos = subtest_recos_with_params('occasionId=AE&mediationId=AM&sharedByUserId=AE',
                                   expected_status=200)
    assert 'tutoIndex' not in recos[0]['mediationId']
    assert recos[0]['sharedByUserId'] == 'AE'
    subtest_recos_with_params('occasionId=AE&mediationId=AM&sharedByUserId=ABCDE',
                           expected_status=400)


def test_16_once_marked_as_read_tutos_should_not_come_back():
    r = req_with_auth().put(RECOMMENDATION_URL, json={})
    assert r.status_code == 200
    recos_before = r.json()
    assert recos_before[0]['mediation']['tutoIndex'] == 0
    assert recos_before[1]['mediation']['tutoIndex'] == 1
    r_update = req_with_auth().patch(API_URL + '/recommendations/' + recos_before[0]['id'],
                                     json={'isClicked': True})
    assert r_update.status_code == 200
    assert r_update.json()['isClicked']

    r = req_with_auth().put(RECOMMENDATION_URL, json={})
    assert r.status_code == 200
    recos_after = r.json()
    assert recos_after[0]['mediation']['tutoIndex'] == 1
    assert 'tutoIndex' not in recos_after[1]['mediation']


def test_17_put_recommendations_should_return_more_recos():
    r = req_with_auth().put(RECOMMENDATION_URL, json={})
    assert r.status_code == 200
    recos = r.json()
    # ensure we still have no duplicates
    ids = list(map(lambda reco: reco['id'], recos))
    assert len(list(filter(lambda v: v > 1, Counter(ids).values()))) == 0

    assert len(list(filter(
        lambda reco:
        'mediatedOccurences' in reco and reco['mediatedOccurences'] is not None and
        len(reco['mediatedOccurences']) > 1,
    recos))) > 0


def test_18_patch_recommendations_should_return_is_clicked_true():
    r = req_with_auth().put(RECOMMENDATION_URL, json={})
    assert r.status_code == 200
    recos = r.json()
    recoId = recos[0]['id']
    r_update = req_with_auth().patch(API_URL + '/recommendations/' + recoId,
                                     json={'isClicked': True})
    assert r_update.status_code == 200
    assert r_update.json()['isClicked']
