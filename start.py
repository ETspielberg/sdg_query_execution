import csv
import json
import requests
import os

from flask import Flask
from flask import request
from elasticsearch import Elasticsearch
es = Elasticsearch()

# configure FLASK and get the parameters from the settings file
app = Flask(__name__)
# app.config.from_object('yourapplication.default_settings')
app.config.from_envvar("LIBINTEL_SETTINGS")

location = app.config.get("LIBINTEL_DATA_DIR")
elsevier_url = app.config.get("ELSEVIER_URL")
altmetric_url = app.config.get("ALTMETRIC_URL")
altmetric_key = app.config.get("ALTMETRIC_API_KEY")
scopus_api_key = app.config.get("SCOPUS_API_KEY")
unpaywall_api_url = app.config.get("UNPAYWALLL_API_URL")
libintel_user_email = app.config.get("LIBINTEL_USER_EMAIL")


# read in the JSON-data from the request and convert them to a scopus query string
# (one could add alternative query targets here, for example transforming the individual query strings to a WoS-Search
def convert_search_to_scopus_search_string(search):
    search_string = ""
    if search["author_name"]:
        if search_string != "":
            search_string += " AND "
        search_string += "AUTH(" + search["author"] + ")"
    if search["topic"]:
        if search_string != "":
            search_string += " AND "
        search_string += "TITLE-ABS-KEY(" + search["topic"] + ")"
    if search["year"]:
        if search_string != "":
            search_string += " AND "
        search_string += "PUBYEAR(" + search["year"] + ")"
    if search["title"]:
        if search_string != "":
            search_string += " AND "
        search_string += "TITLE(" + search["title"] + ")"
    if search["subject"]:
        if search_string != "":
            search_string += " AND "
        search_string += "SUBJAREA(" + search["subject"] + ")"
    if search["author_id"]:
        if search_string != "":
            search_string += " AND "
        search_string += "AU-ID(" + search["author_id"] + ")"
    if search["affiliation_id"]:
        if search_string != "":
            search_string += " AND "
        search_string += 'AF-ID(' + search["affiliation_id"] + ')'
    return search_string


@app.route('/query_execution', methods=['POST'])
def query_execution():
    # prepare location for saving data
    if not os.path.exists(location):
        os.makedirs(location)

    # load the search queries from the http POST body
    search = request.get_json(silent=True)

    print(search)

    query_id = search['identifier']

    # convert the JSON search object to the search string for the scopus api
    search_string = convert_search_to_scopus_search_string(search).replace(" ", "+")

    # define the number of results for further requests
    results_per_page = 100

    # define the url to be queried, first of all get only the number of results, hence only 1 result per page
    url = elsevier_url + '/content/search/scopus?count=1&query=' + search_string + '&apiKey=' + scopus_api_key
    print("querying URL: " + url)

    # perform the query
    r = requests.get(url)
    if r.status_code == 200:
        # convert response to JSON object
        scopus_first_response = r.json()

        # read the total number of results
        number_of_results = int(scopus_first_response['search-results']['opensearch:totalResults'])
        print('total number of publications for this query: ' + str(number_of_results))

        publication_set = []

        # if results have been found, query all the results
        if number_of_results != 0:

            # calculate the number of requests necessary
            number_of_calls = number_of_results // results_per_page + 1

            # perform the individual calls
            for i in range(number_of_calls):
                start = i * results_per_page
                url = elsevier_url + '/content/search/scopus?start=' + str(start) + '&count=' + str(results_per_page) + '&query=' + search_string + '&apiKey=' + scopus_api_key
                r = requests.get(url)

                # if results are obtained create a ScopusResponse object with all the necessary identifiers accessible.
                if r.status_code == 200:
                    for document in r.json()['search-results']['entry']:
                        print(document)
                        # now we query scopus for citation information, Altmetric for societal impact
                        # and Unpaywall for the Open Access information.
                        # each response is added to the intial Scopus response object
                        # doing this within the loop reduces the "pressure" on the APIs
                        extendData(document)

                        # then we save the extended document to an elastic search index.
                        # from this index, we can construct the table used for further analysis.
                        send_to_index(document, query_id)

                        # add the complete scopus response object to the list
                        publication_set.append(document)
            save_to_file(publication_set)
    return "OK"


def extendData(publication):
    # first get the complete set of data from Scopus
    get_extended_data_from_scopus(publication)

    # then the extended citation data from Scopus
    # get_citation_data_from_scopus(publication)

    # get impact data from altmetrics
    get_altmetric_data(publication)

    # then retrieve the Open Access data from Unpaywall
    get_unpaywall_data(publication)


# to be changed, persist via posting
# TO DO: replace posting by persisting in database. Agree on data structure
def persist_list(scopus_responses):
    payload = json.dumps([ob.__dict__ for ob in scopus_responses])
    url = 'http://localhost:11200/ebsData/saveList'
    headers = {'content-type': 'application/json'}
    post = requests.post(url, data=payload, headers=headers)
    print(post.status_code)


def send_to_index(document, query_id):
    res = es.index(query_id, 'full-data', document)
    print('saved to index ' + query_id)
    return res['result']


# persist the resulting json document on disk
def save_to_file(documents):
    out_dir = location + '/out/'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    with open(out_dir + 'data_out.json', 'w') as json_file:
        json.dump(documents, json_file)
    print('saved results to disk')


def get_extended_data_from_scopus(document):
    if document['prism:doi'] is not None:
        url = elsevier_url + '/content/abstract/doi/' + document['prism:doi'] + '?apiKey=' + scopus_api_key + '&httpAccept=application%2Fjson'
        r = requests.get(url)
        print("queryied URL: " + url + " with status code " + str(r.status_code))
        if r.status_code == 200:
            response = r.json()
            try:
                del response['abstracts-retrieval-response']['item']
            except KeyError:
                print('no additional classification')
            document['extended_data'] = response


def get_citation_data_from_scopus(document):
    if document['prism:doi'] is not None:
        url = elsevier_url + '/content/abstract/citations?doi=' + document['prism:doi'] + '&apiKey=' + scopus_api_key
        r = requests.get(url)
        print("queryied URL: " + url + " with status code " + str(r.status_code))
        if r.status_code == 200:
            document['citation_response'] = r.json()


def get_unpaywall_data(document):
    if document['prism:doi'] is not None:
        url = unpaywall_api_url + '/' + document['prism:doi'] + "?email=" + libintel_user_email
        r = requests.get(url)
        print("queryied URL: " + url + " with status code " + str(r.status_code))
        if r.status_code == 200:
            document['unpaywall_response'] = r.json()


def get_altmetric_data(document):
    if document['prism:doi'] is not None:
        url = altmetric_url + '/doi/' + document['prism:doi'] + '?key=' + altmetric_key
        r = requests.get(url)
        print("queryied URL: " + url + " with status code " + str(r.status_code))
        if r.status_code == 200:
            document['altmetric_response'] = r.json()
