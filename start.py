import json
import os
from json import JSONDecodeError
from collections import Counter

import scopus
import numpy as np
import csv
import random
# import pytextrank

from flask import Flask, send_file, jsonify, request, Response
from flask_cors import CORS
from elasticsearch import Elasticsearch

from model.AbstractText import AbstractText
from model.AllResponses import AllResponses
from altmetric.Altmetric import Altmetric
from model.Query import Query
from model.RelevanceMeasures import RelevanceMeasure
from model.ScivalUpdate import ScivalUpdate
from model.Status import Status
from model.UpdateContainer import UpdateContainer
from scival.Scival import Scival
import service.eids_service as eids_service
import service.project_service as project_service
import service.query_service as query_service
import service.relevance_measure_service as relevance_measure_service
import service.status_service as status_service
import service.counter_service as counter_service
from unpaywall.Unpaywall import Unpaywall
from utilities import utils

es = Elasticsearch()

# configure FLASK and get the parameters from the settings file
app = Flask(__name__)
CORS(app)

# initialize config file from environment variable
app.config.from_envvar("LIBINTEL_SETTINGS")

# read the parameters form the config file
location = app.config.get("LIBINTEL_DATA_DIR")
altmetric_key = app.config.get("ALTMETRIC_API_KEY")
altmetric_secret = app.config.get("ALTMETRIC_API_SECRET")
scopus_api_key = app.config.get("SCOPUS_API_KEY")
libintel_user_email = app.config.get("LIBINTEL_USER_EMAIL")


# ----------------------------------- query repository -----------------------------------------------------------------
# retrieves a saved query from disk. If none is found, a new query is created and returned.
@app.route("/query/single/<query_id>", methods=['GET'])
def get_query(query_id):
    try:
        query = query_service.load_query(query_id)
        print(query)
        return jsonify(query)
    except FileNotFoundError:
        query = Query()
        return jsonify(query.__dict__)


# retrieves the Scopus search string and to display it in the browser
@app.route("/query/scopusSearchString/<query_id>", methods=['GET'])
def get_scopus_search_string(query_id):
    try:
        search_string = query_service.load_scopus_query(query_id)
        return Response(search_string, status=200)
    except FileNotFoundError:
        return Response("File not found", status=404)


# saves the query as json document in the working directory as query.json file. Creates a scopus search string and
# saves it as scopus_search_string.txt. Sets project.isQueryDefined = True
@app.route("/query/single/<query_id>", methods=['POST'])
def save_query(query_id):
    project = project_service.load_project(query_id)
    query = request.get_json(silent=True)
    save_query(query_id, query)
    query_service.save_scopus_query(query_id, query)
    project['isQueryDefined'] = True
    project_service.save_project(project)
    return jsonify(query)


# ----------------------------------- project repository ---------------------------------------------------------------

@app.route("/project/all", methods=['GET'])
def list_projects():
    projects = []
    list_filenames = os.listdir(location + '/out/')
    for filename in list_filenames:
        if filename.endswith('.json'):
            path_to_file = location + '/out/' + filename
            try:
                with open(path_to_file) as json_file:
                    project = json.load(json_file)
                    json_file.close()
                    projects.append(project)
            except FileNotFoundError:
                continue
    return jsonify(projects)


# loads a project by the project ID
@app.route("/project/single/<project_id>", methods=['GET'])
def get_project(project_id):
    try:
        project = project_service.load_project(project_id)
        return jsonify(project)
    except FileNotFoundError:
        return Response("File not found", status=404)


# saves a project, creates the project folder if it not exists
@app.route("/project", methods=['post'])
def save_posted_project():
    project = request.get_json(silent=True)
    project_dir = location + '/out/' + project['project_id']
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    project_service.save_project(project)
    return jsonify(project)


# ----------------------------------- EIDs repository ------------------------------------------------------------------
# download the file with the EIDs from the search, stored in the working directory as eids_list.txt
@app.route("/eids/all/<query_id>", methods=['GET'])
def download_eids(query_id):
    # path to the file
    path_to_file = location + '/out/' + query_id + '/' + 'eids_list.txt'
    try:
        return send_file(path_to_file, attachment_filename='eids_list.txt')
    except FileNotFoundError:
        return Response('no list of missed eids', status=404)


# download the file with the missed EIDs from the search, stored in the working directory as missed_eids_list.txt
@app.route("/eids/missed/<query_id>", methods=['GET'])
def download_missed_eids(query_id):
    # path to the file
    path_to_file = location + '/out/' + query_id + '/' + 'missed_eids_list.txt'
    try:
        return send_file(path_to_file, attachment_filename='missed_eids_list.txt')
    except FileNotFoundError:
        return Response('no list of missed eids', status=404)


# download the file with the missed EIDs from the search, stored in the working directory as missed_eids_list.txt
@app.route("/eids/calculateSample/<query_id>", methods=['GET'])
def calculate_sample(query_id):
    out_dir = location + '/out/' + query_id + '/'
    sample_size = int(request.args.get('sample_size'))
    build_sample_list(query_id, sample_size)
    try:
        return send_file(out_dir + 'sample_eids_list.txt', attachment_filename='sample_eids_list.txt')
    except FileNotFoundError:
        return Response('no list of sample eids', status=404, mimetype='text/plain')


def build_sample_list(query_id, sample_size=100):
    if sample_size is None:
        sample_size = 100
    # path to the file
    eids = eids_service.load_eid_list(query_id)

    number = eids.__len__()
    random_sample_eids = []
    if number > sample_size:
        test_indices = random.sample(range(1, eids.__len__()), sample_size)
        for index, value in enumerate(eids):
            if index in test_indices:
                random_sample_eids.append(value)
        eids_service.save_eid_list(project_id=query_id, eids=random_sample_eids, prefix='sample_')
    else:
        eids_service.save_eid_list(project_id=query_id, eids=eids, prefix='sample_')


# retrieves the Scopus search string and to display it in the browser
@app.route("/eids/scopusSearchString/<query_id>", methods=['GET'])
def get_eids_scopus_search_string(query_id):
    prefix = request.args.get('prefix')
    if prefix == 'sample_':
        sample_size = int(request.args.get('sample_size'))
        build_sample_list(query_id, sample_size)
    try:
        eids = eids_service.load_eid_list(query_id, prefix)
    except FileNotFoundError:
        return Response("File not found", status=404)
    search_string = 'EID('
    for index, eid in enumerate(eids):
        if index > 0:
            search_string = search_string + ' OR '
        search_string = search_string + eid
    search_string = search_string + ')'
    return Response(search_string, status=200)


# retrieves the Scopus search string and to display it in the browser
@app.route("/eids/length/<query_id>", methods=['GET'])
def get_eids_list_length(query_id):
    prefix = request.args.get('prefix')
    try:
        eids = eids_service.load_eid_list(query_id, prefix)
        return Response(str(eids.__len__()), status=200)
    except FileNotFoundError:
        return Response("File not found", status=404)


# check the provided test EIDs vs the obtained result set
@app.route("/eids/checkTestEids/<query_id>", methods=['GET'])
def check_test_eids(query_id):
    # load test eids
    test_eids = eids_service.load_eid_list(query_id, 'test_')

    # load collected eids
    eids = eids_service.load_eid_list(query_id)
    relevance_measure = get_relevance_measures(location, query_id)
    if relevance_measure is None:
        relevance_measure = RelevanceMeasure()
    relevance_measure.number_of_search_results = eids.__len__()
    relevance_measure.number_test_entries = test_eids.__len__()
    for test_eid in test_eids:
        if test_eid in eids:
            relevance_measure.number_test_entries_found = relevance_measure.number_test_entries_found + 1
    if relevance_measure.number_of_search_results > 0:
        relevance_measure.recall = relevance_measure.number_test_entries_found / relevance_measure.number_test_entries
    else:
        relevance_measure.recall = 0
    relevance_measure_service.save_relevance_measures(query_id, relevance_measure)
    return jsonify(relevance_measure.__dict__)


# download the file with the missed EIDs from the search, stored in the working directory as missed_eids_list.txt
@app.route("/eids/sample/<query_id>", methods=['GET'])
def download_sample_eids(query_id):
    # path to the file
    path_to_file = location + '/out/' + query_id + '/' + 'test_sample_eids_list.txt'
    try:
        return send_file(path_to_file, attachment_filename='test_sample_eids_list.txt')
    except FileNotFoundError:
        return Response('no list of missed eids', status=404)


# returns true if the eids_list.txt file is present for the given project
@app.route("/eids/check/<query_id>")
def check_eids(query_id):
    path_to_file = location + '/out/' + query_id + '/eids_list.txt'
    return jsonify(os.path.exists(path_to_file))


# uploads the test data and saves it as test_data.csv in the working directory
@app.route('/eids/test/<query_id>', methods=['POST'])
def upload_test_file(query_id):
    print("saving test file for " + query_id)
    project = project_service.load_project(query_id)
    file = request.files['test-file']
    path_to_save = location + '/out/' + query_id + '/'
    if not os.path.exists(path_to_save):
        os.makedirs(path_to_save)
    file.save(path_to_save + 'test_eids_list.txt')
    project['isTestdata'] = True
    project_service.save_project(project)
    return Response('list saved', status=204)


# ----------------------------------- Status repository ----------------------------------------------------------------
# reads the status file (status.json) and returns it.
@app.route("/status/single/<query_id>")
def get_status(query_id):
    try:
        status = status_service.load_status(query_id)
        return jsonify(status)
    except FileNotFoundError:
        return jsonify('status not found', status=404)
    except JSONDecodeError:
        status = Status("STARTING")
        return jsonify(status.__dict__)


# ----------------------------------- Relevance measures repository ----------------------------------------------------
# reads the relavance measures file (relevance_measures.json) and returns it.
@app.route("/relevanceMeasures/single/<query_id>")
def get_relevance_measures(query_id):
    try:
        relevance_measure = relevance_measure_service.load_relevance_measure(query_id)
        return jsonify(relevance_measure)
    except FileNotFoundError:
        return Response("File not found", status=404)


# ----------------------------------- Scival data repository -----------------------------------------------------------
# returns true if the scival_data.csv file is present for the iven project
@app.route("/scival/check/<query_id>")
def check_scival(query_id):
    path_to_file = location + '/out/' + query_id + '/scival_data.csv'
    return jsonify(os.path.exists(path_to_file))


# uploads the scival data and saves it as scival_data.csv in the working directory
@app.route('/scival/single/<query_id>', methods=['POST'])
def upload_scival_file(query_id):
    print("saving scival file for " + query_id)
    if request.method == 'POST':
        project = project_service.load_project(query_id)
        file = request.files['scival-file']
        path_to_save = location + '/out/' + query_id + '/'
        print(path_to_save)
        if not os.path.exists(path_to_save):
            os.makedirs(path_to_save)
        file.save(path_to_save + 'scival_data.csv')
        project['isScivalData'] = True
        project_service.save_project(project)
        import_scival_data(query_id)
    return Response("OK", status=204)


# reads in the scival data and uses the results to update the elasticsearch index
@app.route('/scival/import/<query_id>', methods=['GET'])
def import_scival_data(query_id):
    with open(location + '/out/' + query_id + '/' + 'scival_data.csv', 'r') as csvfile:
        scivals = []
        linereader = csv.reader(csvfile, delimiter=',')
        for row in linereader:
            if row.__len__() != 32:
                continue
            if row[0] == 'Title':
                continue
            scival = Scival(row)
            append_to_index(ScivalUpdate(scival), scival.eid, query_id)
            scivals.append(scival)
        csvfile.close()
    return "imported " + str(scivals.__len__()) + " Scival data"


# ----------------------------------- elasticsearch connections --------------------------------------------------------

def send_to_index(all_responses: AllResponses, query_id):
    all_responses_json = json.dumps(all_responses, cls=HiddenEncoder)
    res = es.index(query_id, 'all_data', all_responses_json, all_responses.id, request_timeout=600)
    print('saved to index ' + query_id)
    return res


def append_to_index(document, eid, query_id):
    update_container = UpdateContainer(document)
    update_json = json.dumps(update_container, cls=HiddenEncoder)
    res = es.update(index=query_id, doc_type="all_data", id=eid, body=update_json)
    print('saved to index ' + query_id)
    return res


# ----------------------------------- keywords endpoint ----------------------------------------------------------------
# retrieve the list of keywords for the search
@app.route("/keywords/<query_id>")
def get_keywords(query_id):
    try:
        result = es.search(index=query_id, doc_type='all_data',
                           filter_path=["hits.hits._source.scopus_abtract_retrieval.authkeywords", "hits.hits._id"])
        keyword_list = []
        for hit in result["hits"]["hits"]:
            keyword_list.extend(hit["_source"]["scopus_abtract_retrieval"]["authkeywords"])
        dictionary = utils.wordlist_to_freq_dict(keyword_list)
        sorted_dict = utils.sort_freq_dict(dictionary)
        return json.dumps([ob.__dict__ for ob in sorted_dict])
    except IOError:
        return Response('no keywords ', status=404)


# ----------------------------------- execution endpoint ---------------------------------------------------------------
# executes the defined and saved query in scopus
@app.route('/query/execution/<query_id>', methods=['POST'])
def query_execution(query_id):
    # prepare location for saving data
    out_dir = location + '/out/' + query_id + '/'
    if not os.path.exists(location):
        return Response("query not yet defined", status=404)

    # reads the saved Scopus search string from disk
    search_string = query_service.load_scopus_query(query_id)

    # retrieve the project from disk, set the booleans and save the project
    project = project_service.load_project(query_id)
    project['isEidsCollected'] = False
    project['isEidsCollecting'] = True
    project_service.save_project(project)

    # prepares the status file
    status = Status("EIDS_COLLECTING")
    status_service.save_status(query_id, status)

    # perform the search in Scopus
    search = scopus.ScopusSearch(search_string, refresh=True, query_id=query_id)

    # retrieve the EIDs
    eids = search.EIDS

    # set the total number of results to the relevance measure save it to disk
    relevance_measure = RelevanceMeasure()
    relevance_measure.total_number_of_query_results = eids.__len__()
    relevance_measure_service.save_relevance_measures(query_id, relevance_measure)

    # set the total number of results to the status save it to disk
    status.total = relevance_measure.total_number_of_query_results
    status_service.save_status(query_id, status)

    # print the results to the command line for logging
    print('found ' + str(eids.__len__()) + ' in Scopus')

    # persist EIDs to file
    eids_service.save_eid_list(project_id=query_id, eids=eids)

    # set the status and save it to disk
    status = Status("EIDS_COLLECTED")
    status_service.save_status(query_id, status)

    # set the project boolean and save the project
    project['isEidslist'] = True
    project['isEidsCollected'] = True
    project['isEidsCollecting'] = False
    project_service.save_project(project)

    return Response({"status": "FINISHED"}, status=204)


@app.route('/collect_data/<query_id>', methods=['POST'])
def data_collection_execution(query_id):
    # load project and eid list. initialize missed eid list
    project = project_service.load_project(query_id)
    project['isDataCollecting'] = True
    project['isDataCollected'] = False
    eids = eids_service.load_eid_list(query_id)
    missed_eids = []

    status = Status("DATA_COLLECTING")
    status.total = eids.__len__()
    status_service.save_status(query_id, status)

    if status.total > 0:
        es.indices.delete(project['project_id'], ignore=[400, 404])
        for idx, eid in enumerate(eids):
            # update the progress status and save the status to disk
            status.progress = idx + 1
            status_service.save_status(query_id, status)

            # print progress
            print('processing entry ' + str(idx) + 'of ' + str(status.total) + ' entries: ' +
                  str(idx / status.total * 100) + '%')

            # retrieve data from scopus
            try:
                scopus_abstract = scopus.ScopusAbstract(eid, view="FULL")
            except IOError:
                missed_eids.append(eid)
                continue

            # create new AllResponses object to hold the individual information
            response = AllResponses(eid, project['name'], project['project_id'])

            # add scopus abstract to AllResponses object
            response.scopus_abtract_retrieval = scopus_abstract

            # get doi and collect unpaywall data and Altmetric data
            doi = scopus_abstract.doi
            if doi is not None:
                if doi is not "":
                    response.unpaywall_response = Unpaywall(libintel_user_email, doi)
                    response.altmetric_response = Altmetric(altmetric_key, doi)
                    response.scival_data = Scival([])

            # send response to elastic search index
            send_to_index(response, project['project_id'])
    eids_service.save_eid_list(project_id=project['project_id'], eids=missed_eids, prefix='missed_')

    status.status = "DATA_COLLECTED"
    status_service.save_status(query_id, status)
    project['isDataCollecting'] = False
    project['isDataCollected'] = True
    project_service.save_project(project)
    return Response({"status": "FINISHED"}, status=204)


@app.route('/collect_references/<query_id>', methods=['POST'])
def references_collection_execution(query_id):
    # initialize lists, read sample size from request and load eid list
    sample_size = int(request.args.get('sample_size'))
    missed_eids = []
    references_eids = []
    eids = eids_service.load_eid_list(query_id)

    # load project and set booleans
    project = project_service.load_project(query_id)
    project['isReferencesCollecting'] = True
    project['isReferencesCollected'] = False
    project_service.save_project(project)

    # prepare status
    status = Status("REFERENCES_COLLECTING")
    status.total = eids.__len__()
    status_service.save_status(query_id, status)

    # if eids are given, cycle through all of them
    if status.total > 0:
        for idx, eid in enumerate(eids):
            # update the progress status and save the status to disk
            status.progress = idx + 1
            status_service.save_status(query_id, status)

            # print progress
            print('processing entry ' + str(idx) + 'of ' + str(status.total) + ' entries: ' +
                  str(idx / status.total * 100) + '%')

            # retrieve refereces from scopus
            try:
                scopus_abstract = scopus.ScopusAbstract(eid, view="FULL")
                if scopus_abstract.references is not None:
                    references_eids = references_eids + scopus_abstract.references
                else:
                    print('no references given in scopus export.')
            except IOError:
                missed_eids.append(eid)
                continue
    # transform references eids into tuple and calculate the occurences
    references_eids_tuple = tuple(references_eids)
    occurences = Counter(references_eids_tuple)
    most_occurences = occurences.most_common(sample_size)

    # save the counter with the most occurences to disk
    counter_service.save_counter(query_id, most_occurences, 'references_')
    eids_service.save_eid_list(query_id, missed_eids, prefix='missed_')

    # set the status and save it to disk
    status.status = "DATA_COLLECTED"
    status_service.save_status(query_id, status)

    # set the project booleans and save it to disk
    project['isReferencesCollecting'] = False
    project['isReferencesCollected'] = True
    project_service.save_project(project)

    return Response({"status": "FINISHED"}, status=204)


@app.route('/prepare_abstracts/<query_id>', methods=['POST'])
def count_keywords(query_id):
    project = project_service.load_project(query_id)
    out_dir = location + '/out/' + project['project_id'] + '/'
    result = es.search(index=project['project_id'], doc_type='all_data',
                       filter_path=["hits.hits._source.scopus_abtract_retrieval.abstract", "hits.hits._id"],
                       request_timeout=600)
    keyword_list = []
    for hit in result["hits"]["hits"]:
        keyword_list.append(AbstractText(hit['_id'], hit["_source"]["scopus_abtract_retrieval"]["abstract"]))
    with open(out_dir + 'abstracts.json', 'w') as json_file:
        json_file.write(json.dumps([ob.__dict__ for ob in keyword_list]))
        json_file.close()
    return Response({"status": "FINISHED"}, status=204)


# @app.route("/calculateTextrank/<query_id>")
# def calculate_text_rank(query_id):
#     path_to_file = location + '/out/' + query_id + '/abstracts.json'
#     for graf in pytextrank.parse_doc(pytextrank.json_iter(path_to_file)):
#         print(pytextrank.pretty_print(graf))
#     return "ok"

@app.route('/analysis/overlap', methods=['GET'])
def calculate_overlap():
    print('calculating overview')
    list_ids = request.args.getlist('primary')
    second_list = request.args.getlist('secondary')
    if second_list.__len__() == 0:
        array = calculate_symmetric_overlap(list_ids)
        length_func = np.vectorize(get_length)
        print(length_func(array))
        return Response({"status": "FINISHED"}, status=200)
    else:
        calculate_asymmetric_overlap(list_ids, second_list)
        return Response({"status": "FINISHED"}, status=200)


def get_length(x):
    if x is not None:
        return len(x)
    else:
        return 0


def calculate_symmetric_overlap(primary):
    primary_length = len(primary)
    overlap_map = np.empty((primary_length, primary_length), dtype=object)
    data = {}
    for key in primary:
        data[key] = eids_service.load_eid_list(key, '')
    for i in range(0, primary_length):
        for entry in data[primary[i]]:
            found = False
            for j in range(i + 1, primary_length):
                if entry in data[primary[j]]:
                    if overlap_map[i, j] is None:
                        overlap_map[i, j] = [entry]
                        overlap_map[j, i] = [entry]
                    else:
                        overlap_map[i, j].append(entry)
                        overlap_map[j, i].append(entry)
                    found = True
            if not found:
                if overlap_map[i, i] is None:
                    overlap_map[i, i] = [entry]
                else:
                    overlap_map[i, i].append(entry)
    return overlap_map


def calculate_asymmetric_overlap(primary, secondary):
    primary_length = primary.__len__()
    secondary_length = secondary.__len__()
    overlap_map = np.empty((primary_length, secondary_length), dtype=object)
    data = {}
    for key in primary:
        data[key] = eids_service.load_eid_list(key, '')
    for key in secondary:
        data[key] = eids_service.load_eid_list(key, '')
    for i in range(0, primary_length):
        for entry in data[primary[i]]:
            found = False
            for j in range(0, secondary):
                if j == i:
                    continue
                if entry in data[secondary[j]]:
                    if overlap_map[i, j] is None:
                        overlap_map[i, j] = [entry]
                    else:
                        overlap_map[i, j].append(entry)
                    found = True
            if not found:
                if overlap_map[i, i] is None:
                    overlap_map[i, i] = [entry]
                else:
                    overlap_map[i, i].append(entry)
    return overlap_map


class HiddenEncoder(json.JSONEncoder):
    def default(self, o):
        return {k.lstrip('_'): v for k, v in o.__getstate__().items()}
