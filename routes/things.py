""" things """
import simplejson as json
from flask import current_app as app, jsonify, request
from flask_login import current_user

from utils.includes import THING_INCLUDES
from utils.rest import expect_json_data,\
                       load_or_404,\
                       login_or_api_key_required,\
                       handle_rest_get_list,\
                       update

Thing = app.model.Thing


@app.route('/things/<ofType>:<identifier>', methods=['GET'])
def get_thing(ofType, identifier):
    query = Thing.query.filter(
        (Thing.type == ofType) &
        (Thing.idAtProviders == identifier)
    )
    thing = query.first_or_404()
    return json.dumps(thing)

@app.route('/things', methods=['GET'])
def list_things():
    return handle_rest_get_list(Thing)

@app.route('/userThings', methods=['GET'])
@login_or_api_key_required
def list_user_things():
    things = []
    thing_ids = []
    for offerer in current_user.offerers:
        for managedVenue in offerer.managedVenues:
            for offer in managedVenue.offers:
                if offer.thingId and offer.thingId not in thing_ids:
                    thing_ids.append(offer.thingId)
                    things.append(offer.thing)
    return jsonify([
        thing._asdict(
            include=THING_INCLUDES,
            has_dehumanized_id=True,
            has_model_name=True
        ) for thing in things
    ]), 200

@app.route('/things', methods=['POST'])
@login_or_api_key_required
@expect_json_data
def post_thing():
    thing = Thing()
    update(thing, request.json)
    app.model.PcObject.check_and_save(thing)
    return jsonify(thing._asdict(
        include=THING_INCLUDES,
        has_dehumanized_id=True,
        has_model_name=True
    )), 201

@app.route('/things/<id>', methods=['PATCH'])
@login_or_api_key_required
@expect_json_data
def patch_thing(id):
    thing = load_or_404(Thing, id)
    update(thing, request.json)
    app.model.PcObject.check_and_save(thing)
    return jsonify(
        thing._asdict(
            include=THING_INCLUDES,
            has_dehumanized_id=True,
            has_model_name=True
        )
    ), 200
