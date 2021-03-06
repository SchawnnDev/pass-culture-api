""" recommendation model """
from datetime import datetime
from flask import current_app as app
from sqlalchemy.sql import expression

db = app.db


class Recommendation(app.model.PcObject, db.Model):

    id = db.Column(db.BigInteger,
                   primary_key=True,
                   autoincrement=True)

    userId = db.Column(db.BigInteger,
                       db.ForeignKey('user.id'),
                       nullable=False,
                       index=True)

    user = db.relationship(lambda: app.model.User,
                           foreign_keys=[userId],
                           backref='recommendations')

    mediationId = db.Column(db.BigInteger,
                            db.ForeignKey('mediation.id'),
                            nullable=True) # NULL for recommendation created directly from a thing or an event

    mediation = db.relationship(lambda: app.model.Mediation,
                                foreign_keys=[mediationId],
                                backref='recommendations')

    thingId = db.Column(db.BigInteger,
                        db.ForeignKey('thing.id'),
                        nullable=True) # NULL for recommendation created from a mediation or an event

    thing = db.relationship(lambda: app.model.Thing,
                            foreign_keys=[thingId],
                            backref='recommendations')

    eventId = db.Column(db.BigInteger,
                        db.ForeignKey('event.id'),
                        db.CheckConstraint('("mediationId" IS NOT NULL AND "thingId" IS NULL AND "eventId" IS NULL)'
                                           + 'OR ("mediationId" IS NULL AND "thingId" IS NOT NULL AND "eventId" IS NULL)'
                                           + 'OR ("mediationId" IS NULL AND "thingId" IS NULL AND "eventId" IS NOT NULL)',
                                           name='check_reco_has_mediationid_xor_thingid_xor_eventid'),
                        nullable=True) # NULL for recommendation created a mediation or an offer

    event = db.relationship(lambda: app.model.Event,
                            foreign_keys=[eventId],
                            backref='recommendations')

    shareMedium = db.Column(db.String(20),
                            nullable=True)

    inviteforEventOccurenceId = db.Column(db.BigInteger,
                                          db.ForeignKey('event_occurence.id'),
                                          nullable=True)

    inviteforEventOccurence = db.relationship(lambda: app.model.EventOccurence,
                                              foreign_keys=[inviteforEventOccurenceId],
                                              backref='inviteRecommendations')

    dateCreated = db.Column(db.DateTime,
                            nullable=False,
                            default=datetime.now)

    dateUpdated = db.Column(db.DateTime,
                            nullable=False,
                            default=datetime.now)

    dateRead = db.Column(db.DateTime,
                         nullable=True,
                         index=True)

    validUntilDate = db.Column(db.DateTime,
                               nullable=True,
                               index=True)

    isClicked = db.Column(db.Boolean,
                          nullable=False,
                          server_default=expression.false(),
                          default=False)

    isFavorite = db.Column(db.Boolean,
                           nullable=False,
                           server_default=expression.false(),
                           default=False)

    isFirst = db.Column(db.Boolean,
                        nullable=False,
                        server_default=expression.false(),
                        default=False)

    def _asdict(self, **options):
        venue = None
        if 'venueTz' in options\
           and options['venueTz']\
           and (self.mediation is None
                or self.mediation.tutoIndex is None):
            if self.event is not None:
                venue = self.event.occurences[0].venue
            elif self.mediation is not None\
                 and self.mediation.event is not None:
                venue = self.mediation.event.occurences[0].venue
            elif self.thing is not None:
                venue = self.thing.offers[0].venue
            elif self.mediation is not None\
                 and self.mediation.thing is not None:
                venue = self.mediation.thing.offers[0].venue
        options['timezone'] = 'UTC-3' if venue and venue.departementCode == '97'\
                                      else 'Europe/Paris'
        return super()._asdict(**options)


    @property
    def mediatedOffers(self):
        #TODO
        pass
        
    # FIXME: This is to support legacy code in the webapp
    # it should be removed once all requests from the webapp
    # have an app version header, which will mean that all
    # clients (or at least those who do use the app) have
    # a recent version of the app

    @property
    def mediatedOccurences(self):
        occurences = []
        if self.mediationId is None:
            if self.event is None:
                return None
            else:
                occurences = self.event.occurences
        else:
            if self.mediation.event is None:
                return None
            else:
                occurences = self.mediation.event.occurences
        return sorted(occurences,
                      key=lambda o: o.beginningDatetime,
                      reverse=True)

app.model.Recommendation = Recommendation
