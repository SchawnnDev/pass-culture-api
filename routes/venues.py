""" venues """
from flask import current_app as app, jsonify, request

from utils.human_ids import dehumanize
from utils.includes import VENUES_INCLUDES
from utils.rest import expect_json_data,\
                       handle_rest_get_list,\
                       update

def update_venue(venue):
    update(venue, request.json)
    if 'providers' in request.json:
        for provider_dict in request.json['providers']:
            provider = app.model.Provider()
            update(provider, provider_dict)
            app.model.PcObject.check_and_save(provider)
            venue_provider = app.model.VenueProvider()
            venue_provider.isActive = True
            venue_provider.venue = venue
            venue_provider.provider = provider
            app.model.PcObject.check_and_save(venue_provider)
    app.model.PcObject.check_and_save(venue)


@app.route('/venues', methods=['GET'])
def list_venues():
    return handle_rest_get_list(app.model.Venue)


@app.route('/venues/<venueId>', methods=['GET'])
def get_venue(venueId):
    query = app.model.Venue.query.filter_by(id=dehumanize(venueId))
    venue = query.first_or_404()
    return jsonify(venue._asdict(include=VENUES_INCLUDES))


@app.route('/venues', methods=['POST'])
@expect_json_data
def create_venue():
    venue = app.model.Venue()
    update_venue(venue)
    return jsonify(new_venue._asdict(include=VENUES_INCLUDES)), 201


@app.route('/venues/<venueId>', methods=['PATCH'])
@expect_json_data
def edit_venue(venueId):
    venue = app.model.Venue\
                     .query.filter_by(id=dehumanize(venueId))\
                     .first_or_404()
    update_venue(venue)
    return jsonify(venue._asdict(include=VENUES_INCLUDES)), 200
