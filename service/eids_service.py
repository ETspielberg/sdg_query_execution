import csv
import glob
import os

from flask import current_app as app


def load_eid_list(project_id, prefix=''):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    # path to the file
    path_to_file = location + '/out/' + project_id + '/' + prefix + 'eids_list.txt'
    with open(path_to_file) as f:
        eids = f.readlines()
        f.close()
        # remove whitespace characters like `\n` at the end of each line
    return [x.strip() for x in eids]


def load_all_files(project_id, prefix=''):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    # path to the file
    base_path = location + '/out/' + project_id + '/'
    eids =[]
    for file in glob.glob(base_path + '*' + prefix + 'eids_list.txt'):
        path_to_file = base_path + file
        with open(path_to_file) as f:
            eids = eids + f.readlines()
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


def load_judgement_file(project_id):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    path_to_file = location + '/out/' + project_id + '/sample_judgement_eids_list.csv'
    judgement_list = []
    with open(path_to_file, 'r') as csvfile:
        linereader = csv.reader(csvfile, delimiter=',')
        for line in linereader:
            if line.__len__() < 2:
                continue
            if line[0] == 'identifier':
                continue
            if line[0] == 'eid':
                continue
            judgement = {'eid': line[0], 'isRelevant': (line[1].strip().lower() == 'true')}
            judgement_list.append(judgement)
        return judgement_list


def generate_judgement_file(judgements, project_id):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    path_to_file = location + '/out/' + project_id + '/sample_judgement_eids_list.csv'
    with open(path_to_file, 'w') as csvfile:
        csvfile.write('eid,isRelevant\n')
        for judgement in judgements:
            csvfile.write(judgement['eid'] + ',' + str(judgement['judgement']) + '\n')
        csvfile.close()


def get_last_change(project_id, prefix=''):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    path_to_file = location + '/out/' + project_id + '/' + prefix + 'eids_list.txt'
    last_change = os.path.getmtime(path_to_file)
    return last_change


def get_query_ids(project_id, prefix=''):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    folder = location + '/out/' + project_id
    query_ids = []
    for file in os.listdir(folder):
            if 'eids_list.txt' in file:
                query_id = file.replace('eids_list.txt', '')
                if query_id != '':
                    query_ids.append(query_id)
    return query_ids
