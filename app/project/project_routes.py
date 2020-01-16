#################
#    imports    #
#################

import json

from flask import Response, request

import service.project_service as project_service
from model.Project import Project
from . import project_blueprint


################
#    routes    #
################

@project_blueprint.route("/all", methods=['GET'])
def list_projects():
    """shows a list of all available projects"""
    projects = project_service.load_all_projects()
    return json.dumps(projects, default=lambda o: o.__getstate__())


@project_blueprint.route("/single/<project_id>", methods=['GET'])
def get_project(project_id):
    """loads a project by the project ID"""
    try:
        project = project_service.load_project(project_id)
        return json.dumps(project, default=lambda o: o.__getstate__())
    except FileNotFoundError:
        return Response("File not found", status=404)


@project_blueprint.route("/new", methods=['post'])
def create_new_project():
    """creates the project folder if it not exists"""
    project_json = request.get_json(silent=True)
    project = Project(**project_json)
    try:
        project_service.create_project(project)
        return json.dumps(project, default=lambda o: o.__getstate__())
    except IOError:
        return Response("could not create project", status=500)

# loads a project by the project ID
@project_blueprint.route("/single/<project_id>", methods=['DELETE'])
def delete_project(project_id):
    """deletes a project by the project ID"""
    try:
        if project_service.delete_project(project_id):
            return Response("project deleted", status=204)
        else:
            return Response("an error occured", status=500)
    except FileNotFoundError:
        return Response("File not found", status=404)

