################
#    imports   #
################

import csv
import os

from model.ScivalUpdate import ScivalUpdate
from scival.Scival import Scival
from service import project_service, elasticsearch_service
from . import scival_blueprint
from flask import current_app as app
from flask import jsonify, Response, request


################
#    routes    #
################

# returns true if the scival_data.csv file is present for the iven project
@scival_blueprint.route("/check/<project_id>")
def check_scival(project_id):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    path_to_file = location + '/out/' + project_id + '/scival_data.csv'
    return jsonify(os.path.exists(path_to_file))


# uploads the scival data and saves it as scival_data.csv in the working directory
@scival_blueprint.route('/single/<project_id>', methods=['POST'])
def upload_scival_file(project_id):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    print("saving scival file for " + project_id)
    if request.method == 'POST':
        project = project_service.load_project(project_id)
        file = request.files['scival-file']
        path_to_save = location + '/out/' + project_id + '/'
        print(path_to_save)
        if not os.path.exists(path_to_save):
            os.makedirs(path_to_save)
        file.save(path_to_save + 'scival_data.csv')
        project['isScivalData'] = True
        project_service.save_project(project)
        import_scival_data(project_id)
    return Response("OK", status=204)


# reads in the scival data and uses the results to update the elasticsearch index
@scival_blueprint.route('/import/<project_id>', methods=['GET'])
def import_scival_data(project_id):
    print('importing Scival data')
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    with open(location + '/out/' + project_id + '/' + 'scival_data.csv', 'r', encoding='utf-8-sig') as csvfile:
        scivals = []
        linereader = csv.DictReader(csvfile, delimiter=',')
        for row in linereader:
            if row.__len__() < 10:
                continue
            scival = Scival(row)
            elasticsearch_service.append_to_index(ScivalUpdate(scival), scival.eid, project_id)
            scivals.append(scival)
        csvfile.close()
    return "imported " + str(scivals.__len__()) + " Scival data"
