import logging

from os import getpid
from sys import stdout
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse
from datetime import datetime

app = Flask(__name__)
api = Api(app)
pid = getpid()


class HousePricePredictionAPI(Resource):
    def get(self):
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('city',
                            type=str,
                            required=True,
                            location='args',
                            help='ERROR 400 - Please provide a valid city name.')
        

        query_dict = parser.parse_args()

        # city = query_dict['city']
        # app_id = query_dict['app_id']
        # date = datetime.strptime(query_dict['date'], '%Y%m%d').strftime('%Y-%m-%d')

        # return weather_data_query(city, app_id, date)


api.add_resource(HousePricePredictionAPI, '/api', endpoint='api')

if __name__ == '__main__':
    handler = RotatingFileHandler(filename='test_rest_api.log', maxBytes=10000, backupCount=1)
    stream_handler = StreamHandler(stdout)
    handler.setLevel(logging.DEBUG)
    stream_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler) #To log to a rotating file.
    app.logger.addHandler(stream_handler) # To log to stdout.
    app.run(debug=True)