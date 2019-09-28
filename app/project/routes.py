import json
import os

from flask import jsonify, Response, request
from flask import current_app as app

import service.project_service as project_service
from . import project_blueprint


@project_blueprint.route("/all", methods=['GET'])
def list_projects():
    projects = project_service.get_all_projects()
    return jsonify(projects)


# loads a project by the project ID
@project_blueprint.route("/single/<project_id>", methods=['GET'])
def get_project(project_id):
    try:
        project = project_service.load_project(project_id)
        return jsonify(project)
    except FileNotFoundError:
        return Response("File not found", status=404)


# saves a project, creates the project folder if it not exists
@project_blueprint.route("/new", methods=['post'])
def save_posted_project():
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    project = request.get_json(silent=True)
    project_dir = location + '/out/' + project['project_id']
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    project_service.save_project(project)
    return jsonify(project)

