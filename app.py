#!/usr/bin/env python


import os

from flask import Flask
from flask import render_template
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
DB = SQLAlchemy(app)


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

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return '<Name {}>'.format(self.name)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/robots.txt')
def robots():
    res = app.make_response('User-agent: *\nAllow: /')
    res.mimetype = 'text/plain'
    return res

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
