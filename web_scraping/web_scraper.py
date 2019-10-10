import pandas as pd
import numpy as np
import json


from collections import namedtuple
from urllib2 import urlopen, Request, HTTPError
from bs4 import BeautifulSoup
from datetime import datetime
from os.path import abspath
from os import remove
from random import randrange
from time import sleep
from itertools import chain


def get_url_list(generic_url_string, start_page, end_page):
    """This function simply returns a list of a generic url strings, with a page URL argument,
     from a starting page number to an ending page number"""
    return [generic_url_string.format(i) for i in xrange(start_page, end_page)]


def write_html_to_disk(url, generic_filepath, pageno, debug=False):
    """This function takes a URL, and a generic file path, and page number, and writes the returned HTML to disk for
     multi-page websites. It is intended to be used as a way to process a list of URLs with page numbers."""
    delay = randrange(1,3)
    sleep(delay)
    f = urlopen(url)
    data = f.read()
    filename = generic_filepath.format(pageno)
    with open(filename, "w+") as html_file:
        html_file.write(data)
        if debug:
            print "Downloaded {} to {}".format(url, filename)


def write_multiple_html_to_disk_from_list(start, end, generic_filepath, url_list):
    """This function writes HTML objects to disk, to save on heap size"""
    url_sublist = url_list[start:end]
    [write_html_to_disk(url, generic_filepath, pgnum) for url, pgnum in zip(url_sublist, xrange(start+1,end+1))]


def read_html_from_disk(generic_filepath, pagenum, debug=False):
    """This function reads a saved HTML file from disk"""
    html_filepath = abspath(generic_filepath.format(pagenum))
    html_from_file = urlopen("file:///{}".format(html_filepath)).read()
    remove(html_filepath)
    if debug:
        print "Read and deleted {}".format(html_filepath)
    return BeautifulSoup(html_from_file, 'lxml')


def multi_page_scrape(soup_list, tag, tag_class):
    """This function is for getting tags from a collection of multiple html files as BeautifulSoup objects"""
    return list(chain.from_iterable([soup.find_all(tag, class_=tag_class) for soup in soup_list]))


def parse_date(date_string):
    """This function transforms date strings into something we can use as a datetime object"""
    ds = date_string
    dsl = ds.split(" ")
    return " ".join(["".join([char if not char.isalpha() else "" for char in dsl[0]]), " ".join(dsl[1:])])

# Defining our OpenStreetMap API JSON data getter and transformer functions. This is a big performance bottleneck.

def get_geodata_object(openstreetmap_api_url):
    """this function takes our OpenStreetMap API URL and returns a JSON response.
    We also write the response to disk for safe keeping"""
    try:
        url = openstreetmap_api_url
        sleep(1)
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        json_response_text = BeautifulSoup(urlopen(req), "lxml").text
        json_response = json.loads(json_response_text)
        with open("osm_json_responses.txt", "a+") as outfile:
            json.dump(json_response, outfile)
            outfile.write('\n')
        return json_response
    except HTTPError as err:
        if err.code == 429:
            print "HTTP Error 429: You've been blocked for being naughty."
            json_response = json.loads("[]")
            with open('osm_json_responses.txt', 'a+') as outfile:
                json.dump(json_response, outfile)
                outfile.write('\n')
            return []
        else:
            print "HTTP Error {}: Look it up.".format(err.code)
            json_response = json.loads("[]")
            with open("osm_json_responses.txt", "a+") as outfile:
                json.dump(json_response, outfile)
                outfile.write('\n')
            return []


def convert_json_to_named_tuple(json_):
    """This function is solely for our convenience when referencing JSON response attributes in data set creation"""
    return json.loads(json_, object_hook=lambda dict_: namedtuple('X', dict_.keys())(*dict_.values()))


def clean_json(json_string):
    """This function cleans some of our JSON  keys, which clash with Python keywords"""
    result = json.dumps(json_string)
    result = result.replace("class", "category")
    result = result.replace("type", "subcategory")
    result = result.replace("osm_subcategory", "osm_type")
    return result


def load_geodata_attributes(geodata_obj):
    """This function takes a JSON response namedtuple object and returns OpenStreetMap API attributes in a tuple"""
    try:
        return (geodata_obj.category,
                geodata_obj.subcategory,
                float(geodata_obj.importance),
                float(geodata_obj.lon),
                float(geodata_obj.lat))
    except AttributeError: # this handles the case where our JSON loader did not find a JSON response from the API URL.
        return np.nan, np.nan, np.nan, np.nan, np.nan


def main():
    url_list = get_url_list("https://nethouseprices.com/house-prices/london?page={}", 1, 12484)
    write_multiple_html_to_disk_from_list(0, 40, "page{}_raw.html", url_list)
    soup_kitchen = [read_html_from_disk("page{}_raw.html", i) for i in xrange(1, 41)]

    # Identified from element inspections via the Chrome developer console.
    # We will then do a multiple scrape across many soup objects, and return a flattened list of each observation for
    # each data series.

    addresses = multi_page_scrape(soup_kitchen, "strong", "street-details-head-row")
    prices = multi_page_scrape(soup_kitchen, "strong", "street-details-price-row")
    details = multi_page_scrape(soup_kitchen, "div", "street-details-row")
    sale_dates_rows = multi_page_scrape(soup_kitchen, "tr", "sold_price_row")

    # We now processes our sales date strings, to a format compatible for conversion to Python datetime objects.

    sale_date_strings = [i.findChildren('td')[-1].text for i in sale_dates_rows]
    cleaned_sale_date_strings = [parse_date(i) for i in sale_date_strings]
    sale_dates = [datetime.strptime(i, "%d %B %Y") for i in cleaned_sale_date_strings]

    # Our scraped data series are set below.

    addr = [i.find("a").string.replace(u"\xa0", " ") for i in addresses]
    pxs = [float(i.string.replace(u"\xa3", "").replace(u",", "")) for i in prices]
    property_characteristics = [[i.strip() for i in categories.string.split(",")] for categories in details]

    #  Some of our data points do not have flat type, so we must adapt for this.

    flat_type = [i[0] if len(i) == 3 else np.nan for i in property_characteristics]
    lease_type = [i[1] if len(i) == 3 else i[0] for i in property_characteristics]
    build_status = [i[2] if len(i) == 3 else i[1] for i in property_characteristics]

    # This is our OpenStreetMap API call for each address converted to a URL.
    # This step can result in a temporary blacklist if too many requests are made in a short period of time.
    # This is why we have built a delay into our OpenStreetMap API dataset.

    generic_osm_query_url = "https://nominatim.openstreetmap.org/search?q=\"{}\"&format=json"

    # if not exists("osm_json_responses.txt"): # This condition prevents us running this expensive code if the output
    # file exists.

    geodata_urls = [generic_osm_query_url.format(i.replace(" ", "%20")) for i in addr]
    json_search_results = [get_geodata_object(url) for url in geodata_urls]
    top_search_results = [result if len(result) == 0 else result[0] for result in json_search_results]

    # We now convert these top search results back to JSON to make namedtuples for ease of referencing in data series
    # creation. This allows us to more easily load the JSON attributes without

    top_search_results_as_json = [clean_json(i) for i in top_search_results]
    geodata_json = [convert_json_to_named_tuple(result) for result in top_search_results_as_json]

    # TODO: add data parsed from display_name about borough as alternative to k Mean Clustering, to data frame.
    # json_search_results = [get_geodata_object(url) for url in geodata_urls]
    geodata = [load_geodata_attributes(result_named_tuple) for result_named_tuple in geodata_json]

    category = [i[0] for i in geodata]
    subcategory = [i[1] for i in geodata]
    importance = [i[2] for i in geodata]
    longitude = [i[3] for i in geodata]
    latitude = [i[4] for i in geodata]

    # We construct our data set.
    variables = [addr, pxs, sale_dates, flat_type, lease_type, build_status, category, subcategory, importance,
                 longitude, latitude]
    series_names = ["addresses",
                    "prices",
                    "sale_dates",
                    "flat_type",
                    "lease_type",
                    "build_status",
                    "category",
                    "subcategory",
                    "importance",
                    "longitude",
                    "latitude"]

    # Check all series are the same length.
    if len(pxs) == sum([len(dataseries) for dataseries in variables]) / len(variables):
        # Setup dictionary for dataframe.
        dataset = {series_name: series for series_name, series in zip(series_names, variables)}

    dataset_frame = pd.DataFrame(dataset)
    # We will save down our dataset to a CSV and JSON files, for persistence, and manual data inspection if required.
    dataset_frame.to_csv("dataset_frame.csv")
    dataset_frame.to_json("dataset_frame.json")

if __name__ == '__main__':
        main()
