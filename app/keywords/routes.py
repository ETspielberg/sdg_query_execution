import json

from elasticsearch import Elasticsearch
from flask import Response

from utilities import utils
from . import keywords_blueprint

es = Elasticsearch()

# retrieve the list of keywords for the search
@keywords_blueprint.route("/collect/<query_id>")
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
