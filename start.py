import csv
import json
import requests
import os

from flask import Flask
from flask import request
from model.ScopusSearchResponse import ScopusResponse

# configure FLASK and get the parameters from the settings file
app = Flask(__name__)
# app.config.from_object('yourapplication.default_settings')
app.config.from_envvar("LIBINTEL_SETTINGS")

location = app.config.get("LIBINTEL_DATA_DIR")
elsevier_url = app.config.get("ELSEVIER_URL")
scopus_api_key = app.config.get("SCOPUS_API_KEY")
unpaywall_api_url = app.config.get("UNPAYWALLL_API_URL")
libintel_user_email = app.config.get("LIBINTEL_USER_EMAIL")


# read in the JSON-data from the request and convert them to a scopus query string
# (one could add alternative query targets here, for example transforming the individual query strings to a WoS-Search
def convert_search_to_scopus_search_string(search):
    search_string = ""
    if search["author"]:
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
        search_string += "Year(" + search["year"] + ")"
    if search["title"]:
        if search_string != "":
            search_string += " AND "
        search_string += "TITLE(" + search["title"] + ")"
    if search["subject"]:
        if search_string != "":
            search_string += " AND "
        search_string += "SUBJAREA(" + search["subject"] + ")"
    if search["auth_id"]:
        if search_string != "":
            search_string += " AND "
        search_string += "AU-ID(" + search["auth_id"] + ")"
    return search_string


def get_group_search_term(group):
    string = ""
    for id in group.split():
        if string != "":
            string += " AND "
        string += id
    string = 'AF-ID(' + string + ')'
    return string



@app.route('/query_execution', methods=['POST'])
def query_execution():
    # prepare location for saving data
    if not os.path.exists(location):
        os.makedirs(location)

    # load the search queries from the http POST body
    search = request.get_json(silent=True)

    # convert the JSON search object to the search string for the scopus api
    search_string = convert_search_to_scopus_search_string(search).replace(" ", "+")

    # get the list of groups to be analyzed from the request. each group is defined by a comma separated list of identifiers
    if search['groups']:
        groups = search['groups']
    else:
        groups = []

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

        for group in groups:
            search_string_group = search_string + get_group_search_term(group)
            url = elsevier_url + '/content/search/scopus?count=1&query=' + search_string + '&apiKey=' + scopus_api_key
            r.request(url)
            group.response = r.json()
            group.number = group.response['search-results']['opensearch:totalResults']
            print('number of publications for group ' + group + ': ' + str(group.number))

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
                        scopus_response = ScopusResponse()

                        # for each identifier, test, whether it is present and if so, attach it to the Scopus response object.
                        try:
                            if document['pubmed_id'] is not None:
                                scopus_response.pubmed_id = document['pubmed_id']
                        except KeyError:
                            print("Scopus: no PubMed ID given")
                        else:
                            print("Scopus: no PubMed ID given")
                        try:
                            if document['prism:doi'] is not None:
                                scopus_response.doi = document['prism:doi']
                        except KeyError:
                            print("Scopus: no PubMed ID given")
                        else:
                            print("Scopus: no PubMed ID given")

                        if document['dc:identifier'] is not None:
                            scopus_response.scopus_id = document['dc:identifier']
                        else:
                            print("Scopus: no Scopus ID given")
                        if document['eid'] is not None:
                            scopus_response.eid = document['eid']
                        else:
                            print("Scopus: no EID given")
                        if document['prism:url'] is not None:
                            scopus_response.url = document['prism:url']
                        else:
                            print("Scopus: no URL given")
                        if document['citedby-count'] is not None:
                            scopus_response.cited_by_scopus = document['citedby-count']
                        else:
                            print("Scopus: no Cited-By given")

                        # attach the actual scopus response
                        scopus_response.response = document

                        # add the complete scopus response object to the list
                        publication_set.append(scopus_response)

            # now we have a list of all the publications from the intial query.
            # we go through every one of them and query scopus for citation information, Altmetric for societal impact
            # and Unpaywall for the Open Access information.
            # aach response is added to the intial Scopus response object

            for publication in publication_set:
                # first get the citation data from Scopus
                if publication.scopus_id is not None:
                    url = elsevier_url + '/content/abstract/citation?scopus_id=' + publication.scopus_id + '&apiKey=' + scopus_api_key
                    r = requests.get(url)
                    print("queryied URL: " + url + " with status code " + str(r.status_code))
                    if r.status_code == 200:
                        publication.citation_response = r.json()

                # then retrieve the Open Access data from Unpaywall
                if publication.doi is not None:
                    url = unpaywall_api_url + '/' + publication.doi + "?email=" + libintel_user_email
                    r = requests.get(url)
                    print("queryied URL: " + url + " with status code " + str(r.status_code))
                    if r.status_code == 200:
                        publication.unpaywall_response = r.json()
                        print(publication.unpaywall_response)

    return "OK"


# to be changed, persist via posting
# TO DO: replace posting by persisting in database. Agree on data structure
def persist_list(scopus_responses):
    payload = json.dumps([ob.__dict__ for ob in scopus_responses])
    url = 'http://localhost:11200/ebsData/saveList'
    headers = {'content-type': 'application/json'}
    post = requests.post(url, data=payload, headers=headers)
    print(post.status_code)


# to be changed, persist all necessary fields on disk
# TO DO: agree on data structure
def save_ebs_list_file(ebs_titles, ebs_filename, ebs_model, ebs_mode):
    with open(location + "\\" + ebs_model + "\\" + ebs_filename.replace(".csv", "_") + ebs_mode + "_out.csv", 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=';',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['ISBN', 'Title', 'Subject area', 'price', 'year', 'total usage', 'price per usage', 'selected', 'EBS model ID', 'weighting factor'])
        for item in ebs_titles:
            spamwriter.writerow([item.isbn, '"' + item.title + '"', item.subject_area, str(item.price), str(item.year), str(item.total_usage), str(item.cost_per_usage), str(item.selected), ebs_model, str(item.weighting_factor)])
