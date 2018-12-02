import json
import numpy as np
import pandas as pd

from collections import namedtuple
from urllib2 import urlopen, Request, HTTPError
from bs4 import BeautifulSoup
from joblib import load


def api_get_geodata_object(openstreetmap_api_url):
    """this function takes our OpenStreetMap API URL and returns a JSON response.
    We also write the response to disk for safe keeping"""
    try:
        url = openstreetmap_api_url
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        json_response_text = BeautifulSoup(urlopen(req), "lxml").text
        json_response = json.loads(json_response_text)
        return json_response
    except HTTPError as err:
        if err.code == 429:
            print "HTTP Error 429: You've been blocked for being naughty."
            return []
        else:
            print "HTTP Error {}: Look it up.".format(err.code)
            return []


def api_clean_json(json_string):
    """This function cleans some of our JSON  keys, which clash with Python keywords"""
    result = json.dumps(json_string)
    result = result.replace("class", "category")
    result = result.replace("type", "subcategory")
    result = result.replace("osm_subcategory", "osm_type")
    return result


def api_convert_json_to_named_tuple(json_):
    """This function is solely for our convenience when referencing JSON response attributes in dataset creation"""
    return json.loads(json_, object_hook=lambda dict_: namedtuple('X', dict_.keys())(*dict_.values()))


def api_load_geodata_attributes(geodata_obj):
    """This function takes a JSON response namedtuple object and returns OpenStreetMap API attributes in a tuple"""
    try:
        return (geodata_obj.category,
                geodata_obj.subcategory,
                float(geodata_obj.importance),
                float(geodata_obj.lon),
                float(geodata_obj.lat))
    except AttributeError:  # this handles the case where our JSON loader did not find a JSON response from the API URL.
        return np.nan, np.nan, np.nan, np.nan, np.nan

# address = '91 Dames Road, London, E7 0DW' # API input from user.
# new_build = False # API input from user.
# flat_type = 'Terraced' # API input from user.
# lease_type = 'Leasehold' # API input from user.


class OpenStreetMapQuery(object):
    def __init__(self, address, new_build, flat_type, lease_type):
        self.address = address
        self.new_build = new_build
        self.flat_type = flat_type.replace("%20", " ")
        self.lease_type = lease_type
        self.generic_osm_query_url = 'https://nominatim.openstreetmap.org/search?q=\"{}\"&format=json'
        self.open_street_map_api_query = self.generic_osm_query_url.format(self.address.replace(' ', '%20'))
        self.dataset = {}  # This will be our dataset returned by a method.

        # We get the geodata object as a named tuple.
        self.result = api_get_geodata_object(self.open_street_map_api_query)
        self.top_result = self.result if len(self.result) == 0 else self.result[0]
        self.top_result_json = api_clean_json(self.top_result)
        self.geodata_object = api_convert_json_to_named_tuple(self.top_result_json)

        # We now extract the data from our named_tuple object, to be assigned to our prediction dataset.
        self.geodata = api_load_geodata_attributes(self.geodata_object)
        self.category = self.geodata[0]
        self.subcategory = self.geodata[1]
        self.importance = self.geodata[2]
        self.longitude = self.geodata[3]
        self.latitude = self.geodata[4]

    def set_dataset(self):
        dataset = self.dataset
        dataset['importance'] = self.importance
        dataset['latitude'] = self.latitude
        dataset['longitude'] = self.longitude
        dataset['Non-Newbuild'] = 1 if not self.new_build else 0
        flat_type_list = ['Detached', 'Flat', 'Semi Detached', 'Terraced']
        for label in flat_type_list:
            dataset[label] = 1 if label == self.flat_type else 0
        lease_type_list = ['Leasehold', 'Freehold']
        for lease_label in lease_type_list:
            dataset[lease_label] = 1 if lease_label == self.lease_type else 0
        cat_subcat_list = ['amenity', 'building', 'highway', 'landuse', 'place', 'shop', 'cafe', 'city', 'convenience',
                           'cycleway', 'footway', 'house', 'houses', 'living_street', 'pedestrian', 'primary',
                           'residential', 'restaurant', 'secondary', 'service', 'suburb', 'tertiary', 'trunk',
                           'uncategoryified', 'yes']
        for cat_or_subcat in cat_subcat_list:
            dataset[cat_or_subcat] = 1 if (self.category == cat_or_subcat or self.subcategory == cat_or_subcat) else 0

    def get_dataset(self):
        return self.dataset


class HousePriceModel(object):
    def __init__(self, dataset):
        self.dataset = dataset
        self.X = pd.DataFrame(dataset, index=[0])
        self.kmm_X = pd.DataFrame([self.X.latitude, self.X.longitude]).T
        self.kmm = load('k_means_clustering_model.joblib')
        self.rfr = load('serialised_random_forest_regressor.joblib')

    def predict_house_price(self):
        cluster_prediction = self.kmm.predict(self.kmm_X)
        cluster_dummies = {str(i): 0 for i in xrange(0, 10)}
        cluster_dummies[str(cluster_prediction[0])] = 1
        cd_df = pd.DataFrame(cluster_dummies, index=[0])
        rfr_X = pd.concat([self.X, cd_df], axis=1)
        return self.rfr.predict(rfr_X)[0]
