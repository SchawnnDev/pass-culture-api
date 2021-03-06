from flask import Flask
from flask_script import Manager
from time import sleep

from utils.human_ids import humanize
from utils.test_utils import API_URL, req_with_auth


app = Flask(__name__)


def create_app(env=None):
    app.env = env
    return app


app.manager = Manager(create_app)

with app.app_context():
    import models
    import local_providers


def test_10_delete_venue_provider():
    r_get1 = req_with_auth().get(API_URL + '/venueProviders/AE')
    assert r_get1.status_code == 200
    r_get2 = req_with_auth().get(API_URL + '/venueProviders/AEBC')
    assert r_get2.status_code == 404


def test_11_create_venue_provider():
    with app.app_context():
        openagenda_provider = app.model.Provider.getByClassName('OpenAgendaEvents')
    vp_data = {'providerId': humanize(openagenda_provider.id),
               'venueId': 'AE',
               'venueIdAtOfferProvider': '49050769'}
    r_create = req_with_auth().post(API_URL + '/venueProviders',
                                    json=vp_data)
    assert r_create.status_code == 201
    create_json = r_create.json()
    assert 'id' in create_json
    vp_id = create_json['id']
    assert create_json['lastSyncDate'] is None
    read_json = create_json
    tries = 0
    while read_json['lastSyncDate'] is None:
        assert tries < 10 
        r_check = req_with_auth().get(API_URL + '/venueProviders/' + vp_id)
        assert r_check.status_code == 200
        read_json = r_check.json()
        tries += 1
        sleep(1)


def test_12_edit_venue_provider():
    r_edit = req_with_auth().patch(API_URL + '/venueProviders/AE',
                                   json={'venueIdAtOfferProvider': '12345678'})
    assert r_edit.status_code == 200
    r_check = req_with_auth().get(API_URL + '/venueProviders/AE')
    assert r_check.status_code == 200
    assert r_check.json()['venueIdAtOfferProvider'] == '12345678'


def test_13_delete_venue_provider():
    r_delete = req_with_auth().delete(API_URL + '/venueProviders/AE')
    assert r_delete.status_code == 200
    r_check = req_with_auth().get(API_URL + '/venueProviders/AE')
    assert r_check.status_code == 404


def test_14_get_venue_providers_by_venue():
    r_list = req_with_auth().get(API_URL + '/venueProviders?venueId=AE')
    assert r_list.status_code == 200


def test_15_get_all_venue_providers():
    r_list = req_with_auth().post(API_URL + '/venueProviders')
    assert r_list.status_code == 400

