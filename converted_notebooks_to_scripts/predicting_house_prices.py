#%%
import json
import numpy as np
import pandas as pd

from collections import namedtuple
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from bs4 import BeautifulSoup

from joblib import load
#%%
# We will define our API input data processing functions; this could be an Apache Spark DAG in production, or some other
# stream processing graph technology, for handling API queries; load balancing could be done by having multiple workers in each
# graph node ready to process request data, with each request data item having a unique request ID to allow the distributed
# data transformations and calculations to return the correct result for a given query to the API.
# Each node in our stream processing DAG could be a generic cloud host, with a specific pod of containers for a given task.
# Kubernetes can be used to manage which hosts run which container pods for which part of the DAG, and direct traffic possibly.

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
            print("HTTP Error 429: You've been blocked for being naughty.")
            return []
        else:
            print(f"HTTP Error {err.code}: Look it up.")
            return []

def api_clean_json(json_string):
    """This function cleans some of our JSON  keys, which clash with Python keywords"""
    clean_json_result = json.dumps(json_string)
    clean_json_result = clean_json_result.replace("class", "category")
    clean_json_result = clean_json_result.replace("type", "subcategory")
    clean_json_result = clean_json_result.replace("osm_subcategory", "osm_type")
    return clean_json_result

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
    except AttributeError: # this handles the case where our JSON loader did not find a JSON response from the API URL.
        return np.nan, np.nan, np.nan, np.nan, np.nan
#%%
# We call our data transformation functions below. This represents the order of transformations in our admittedly 'linear' graph.

# Example used to lookup OpenStreetMap Data - 91 Dames Road, London, E7 0DW
address = '91 Dames Road, London, E7 0DW' # API input from user.

generic_osm_query_url = "https://nominatim.openstreetmap.org/search?q=\"{}\"&format=json"
open_street_map_api_query = generic_osm_query_url.format(address.replace(" ", "%20"))

result = api_get_geodata_object(open_street_map_api_query)
top_result = result if len(result) == 0 else result[0]
top_result_json = api_clean_json(top_result)
geodata_object = api_convert_json_to_named_tuple(top_result_json)

# We now extract the data from our named_tuple object, to be assigned to our prediction dataset.
geodata = api_load_geodata_attributes(geodata_object)
category = geodata[0]
subcategory = geodata[1]
importance = geodata[2]
longitude = geodata[3]
latitude = geodata[4]
#%%
# We will define our dataset for prediction here:

dataset = {'importance': importance, 'latitude': latitude, 'longitude': longitude}

# Our model accepts user input specifying if a house is a non-newbuild or a newbuild.
new_build = False # API input from user.
dataset['Non-Newbuild'] = 1 if not new_build else 0

flat_type = 'Terraced' # API input from user.
flat_type_list = ['Detached','Flat','Semi Detached','Terraced']
for label in flat_type_list:
    dataset[label] = 1 if label == flat_type else 0

lease_type = 'Leasehold' # API input from user.
lease_type_list = ['Leasehold', 'Freehold']
for lease_label in lease_type_list:
    dataset[lease_label] = 1 if lease_label == lease_type else 0

cat_subcat_list = ['amenity','building','highway','landuse','place','shop','cafe','city','convenience','cycleway','footway',
'house','houses','living_street','pedestrian','primary','residential','restaurant','secondary','service','suburb','tertiary',
'trunk','uncategoryified','yes']

for cat_or_subcat in cat_subcat_list:
    dataset[cat_or_subcat] = 1 if (category == cat_or_subcat or subcategory == cat_or_subcat) else 0
#%%
# We will now convert our dataset dictionary to a Pandas DataFrame our KMM can label, and our Random Forest Regressor can
# predict the price from.

# Feature set without lat lon cluster label from KMM.
X = pd.DataFrame(dataset, index=[0])
X
#%%
kmm_X = pd.DataFrame([X.latitude, X.longitude]).T
kmm_X
#%%
# We will load our KMM and obtain a cluster prediction for our observation. This node in our DAG could run multiple container
# instances on a single host for load balancing; a pod dedicated to this transformation on a single host should be enough.

kmm = load('k_means_clustering_model.joblib')
cluster_prediction = kmm.predict(kmm_X)
cluster_prediction
#%%
# We will now create our cluster label variables and assign our cluster_prediction label to 1.

cluster_dummies = {str(i) : 0 for i in range(0, 10)}
cluster_dummies[str(cluster_prediction[0])] = 1
cd_df = pd.DataFrame(cluster_dummies, index=[0])
cd_df
#%%
# We now concatenate the cluster labels DataFrame with the features DataFrame and get the final DataFrame for our
# Random Forest Regressor model.

rfr_X = pd.concat([X, cd_df], axis=1)
rfr_X
#%%
# We inspect our final variables feeding the Random Forest Regressor to make sure we have as many as we expect, and of the right
# type.

rfr_X.info()
#%%
# We will now return the final result of prediction on the transformed data using mock API user input.

rfr = load('serialised_random_forest_regressor.joblib')
rfr.predict(rfr_X)[0]