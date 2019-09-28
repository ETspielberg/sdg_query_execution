import json
import os

from elasticsearch import Elasticsearch
from flask import current_app as app

es = Elasticsearch()

def load_project(query_id):
    return es.get(index='projects', doc_type='project', id=query_id)['_source']


def get_all_projects():
    projects = []
    search_result = es.search(index='projects', doc_type="project")['hits']['hits']
    for project_source in search_result:
        projects.append(project_source['_source'])
    return projects


def save_project(project):
    try:
        res = es.index(index='projects', doc_type="project", id=project['project_id'], body=json.dumps(project))
        return res
    except:
        print('could not send scival update')
