import logging

from os import getpid
from sys import stdout
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse
from house_price_model import OpenStreetMapQuery, HousePriceModel

app = Flask(__name__)
api = Api(app)
pid = getpid()


# Default web query:
# http://127.0.0.1:5000/api?address=91%20Dames%20Road,%20London,%20E7%200DW&new_build=False&flat_type=Terraced&lease_type=Leasehold
class NewAPIQuery(object):
    def __init__(self, address, new_build, flat_type, lease_type):
        app.logger.info("The process id is: %s", pid)
        app.logger.info('QUERY using the following parameters: {}'.format(locals()))
        self.new_req = OpenStreetMapQuery(address, new_build, flat_type, lease_type)
        self.new_req.set_dataset()
        self.valid_query = True if len(self.new_req.result) > 0 else False
        app.logger.info('QUERY address found: {}'.format(self.valid_query))
        self.dataset = self.new_req.get_dataset()
        self.model = HousePriceModel(self.dataset)

    def get_prediction(self):
        prediction = self.model.predict_house_price()
        return prediction


class HousePricePredictionAPI(Resource):
    def get(self):
        """The expected API request parameters are address, new_build, flat_type, lease_type"""
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('address',
                            type=str,
                            required=True,
                            location='args',
                            help='ERROR 400 - Please provide address in the format: Number Street, London, Postcode.')
        parser.add_argument('new_build',
                            type=str,
                            required=True,
                            location='args',
                            help='ERROR 400 - Please enter True or False to identify if the property is a new build.')
        parser.add_argument('flat_type',
                            type=str,
                            required=True,
                            location='args',
                            help='ERROR 400 - Specify if the property is a Flat, Detached, Semi Detached or Terraced')
        parser.add_argument('lease_type',
                            type=str,
                            required=True,
                            location='args',
                            help='ERROR 400 - Specify if the property is Leasehold or Freehold')
        query_dict = parser.parse_args()
        address = query_dict['address']
        new_build = True if query_dict['new_build'] == 'true' else False
        flat_type = query_dict['flat_type']
        lease_type = query_dict['lease_type']
        query_object = NewAPIQuery(address, new_build, flat_type, lease_type)
        if query_object.valid_query is True:
            prediction = query_object.get_prediction()
            app.logger.info('SUCCESS 200 - Valid request and prediction made.')
            response = {
                        'code': 200,
                        'Predicted House Price': prediction,
                        'Model Inputs': query_dict
            }
            return jsonify(response)
        else:
            app.logger.error('ERROR 400 - Address search returned no data.')
            response = {
                'status': '400',
                'message': 'Address search returned no data.'
            }
            return jsonify(response)


api.add_resource(HousePricePredictionAPI, '/api', endpoint='api')

if __name__ == '__main__':
    handler = RotatingFileHandler(filename='test_rest_api.log', maxBytes=10000, backupCount=1)
    stream_handler = StreamHandler(stdout)
    handler.setLevel(logging.DEBUG)
    stream_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)  # To log to a rotating file.
    app.logger.addHandler(stream_handler)  # To log to stdout.
    app.run(debug=True)
