#!/usr/bin/env python


import os

import functools

from collections import OrderedDict

from utcdatetime import utcdatetime, UTC

from flask import (
    Flask, render_template, request, jsonify, url_for, redirect)
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
DB = SQLAlchemy(app)
API_WRITE_KEY = os.environ['API_WRITE_KEY']


class InvalidAPIRequest(Exception):
    def __init__(self, message, status_code=400, request_json=None):
        Exception.__init__(self)

        self.message = message
        self.status_code = status_code
        self.request_json = request_json

    def to_dict(self):
        return {
            'error': self.message,
            'request': self.request_json,
         }


class TrainArrival(DB.Model):
    id = DB.Column(
        DB.Integer, primary_key=True)

    timetable_datetime = DB.Column(
        DB.DateTime(timezone=True)
    )

    actual_datetime = DB.Column(
        DB.DateTime(timezone=True)
    )

    station_3alpha = DB.Column(
        DB.String(length=5)
    )

    def __init__(self, timetable_datetime, actual_datetime, station_3alpha):
        self.timetable_datetime = timetable_datetime
        self.actual_datetime = actual_datetime
        self.station_3alpha = station_3alpha

    def __repr__(self):
        return '<Name {}>'.format(self.name)

    @property
    def minutes_late(self):
        delta = self.actual_datetime - self.timetable_datetime
        return int(delta.total_seconds() / 60)

    def to_dict(self):
        # raise RuntimeError(repr(self.timetable_datetime))
        return OrderedDict([
            ('timetable_datetime', self.format_datetime(
                self.timetable_datetime)),
            ('actual_datetime', self.format_datetime(
                self.actual_datetime)),
            ('station_3alpha', self.station_3alpha),
        ])

    @classmethod
    def from_json(cls, the_json):
        req_fields = set(
            ['timetable_datetime', 'actual_datetime', 'station_3alpha'])

        if set(the_json.keys()) != req_fields:

            raise InvalidAPIRequest(
                'Required fields: {}'.format(', '.join(req_fields)),
                400,
                the_json)

        return cls(
            timetable_datetime=cls.parse_datetime(
                the_json['timetable_datetime']),

            actual_datetime=cls.parse_datetime(
                the_json['actual_datetime']),

            station_3alpha=the_json['station_3alpha']
        )

    @staticmethod
    def parse_datetime(string):
        """
        Convert a UTC datetime string like '2015-01-01T14:23:00Z' into a Python
        datetime object with UTC tzinfo.
        """
        return utcdatetime.from_string(string).astimezone(UTC)

    @staticmethod
    def format_datetime(python_datetime):
        """
        python_datetime is a naive (no-timezone) and native python datetime.
        However it is always stored in the database as UTC, so we can safely
        assume it has that timezone.
        """

        timezone_aware_datetime = python_datetime.replace(tzinfo=UTC)
        utc_datetime = utcdatetime.from_datetime(timezone_aware_datetime)
        return str(utc_datetime)


@app.errorhandler(InvalidAPIRequest)
def handle_invalid_api_request(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def require_api_token(func):
    @functools.wraps(func)
    def check_token(*args, **kwargs):
        # want header like 'Authorization: token abcdefg'

        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('token '):
            raise InvalidAPIRequest(
                    'Required HTTP header: `Authorization: token <token>`',
                    401)

        elif auth_header[6:] != API_WRITE_KEY:
            raise InvalidAPIRequest('Bad API key given, sorry.', 403)

        return func(*args, **kwargs)

    return check_token


@app.route('/')
def home():
    recent_arrivals = (
        TrainArrival.query.order_by('timetable_datetime').limit(5)
    )
    return render_template('index.html', train_arrivals=recent_arrivals)


@app.route('/api/train-arrivals/', methods=['POST'])
@require_api_token
def create_train_arrival():
    train_arrival = TrainArrival.from_json(request.json)

    DB.session.add(train_arrival)
    DB.session.commit()

    return redirect(
        url_for('retrieve_train_arrival', object_id=train_arrival.id),
        303
    )


@app.route('/api/train-arrivals/<int:object_id>/', methods=['GET'])
def retrieve_train_arrival(object_id):
    return jsonify(
        TrainArrival.query.filter_by(id=object_id).first_or_404().to_dict()
    )


@app.route('/robots.txt')
def robots():
    res = app.make_response('User-agent: *\nAllow: /')
    res.mimetype = 'text/plain'
    return res

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
