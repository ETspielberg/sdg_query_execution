import json
import os

from flask import current_app as app


def load_eid_list(project_id, prefix=''):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    # path to the file
    out_dir = location + '/out/' + project_id + '/'
    with open(out_dir + prefix + 'eids_list.txt') as f:
        eids = f.readlines()
        f.close()
        # remove whitespace characters like `\n` at the end of each line
    return [x.strip() for x in eids]


def save_eid_list(project_id, eids, prefix=''):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    out_dir = location + '/out/' + project_id + '/'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    with open(out_dir + prefix + 'eids_list.txt', 'w') as list_file:
        for eid in eids:
            list_file.write(eid + '\n')
        list_file.close()


def load_judgement_file(project_id, prefix=''):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    path_to_file = location + '/out/' + project_id + '/' + prefix + ''
    with open(path_to_file) as json_file:
        project = json.load(json_file)
        json_file.close()
        return project
