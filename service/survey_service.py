import csv
import json
import os

from flask import current_app as app

from SurveyProvider.SurveyGizmo import SurveyGizmo
from model.Survey import Survey
from service import facettes_service, elasticsearch_service
from service.eids_service import generate_judgement_file
from utilities.HiddenEncoder import HiddenEncoder
from utilities.utils import replace_index_by_clear_name


def load_judgement_file(project_id, query_id):
    path_to_file = get_path_to_judgement_file(project_id, query_id)
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


def generate_judgement_file(judgements, project_id, query_id):
    path_to_file = get_path_to_judgement_file(project_id, query_id)
    with open(path_to_file, 'w') as csvfile:
        csvfile.write('eid,isRelevant\n')
        for judgement in judgements:
            csvfile.write(judgement['eid'] + ',' + str(judgement['judgement']) + '\n')
        csvfile.close()


def save_survey(survey, prefix=''):
    """
    saves the survey to disc
    :param survey: the survey to be saved
    :param prefix: an optional prefix to save the survey
    :return:
    """
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    out_dir = location + '/out/' + survey.project_id
    try:
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        with open(out_dir + '/' + prefix + 'survey.json', 'w') as json_file:
            json_file.write(json.dumps(survey, cls=HiddenEncoder))
        return True
    except IOError:
        return False


def load_survey(project_id, prefix=''):
    """
    loads a survey from disc
    :param project_id: the Id of the current project
    :param prefix: an optional prefix of the survey to be retrieved
    :return: the survey object loaded from disc
    """
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    path_to_file = location + '/out/' + project_id + '/' + prefix + 'survey.json'
    with open(path_to_file) as json_file:
        survey = Survey(**json.load(json_file))
        return survey


def collect_survey_data(project):
    """
    retrieves the survey data from the survey provider and generates the survey object.
    :param project: the project the survey shall be collected for
    :return: the survey object
    """
    print('collecting survey results for survey id {}'.format(project.survey_id))
    gizmo_survey = SurveyGizmo(survey_id=project.survey_id, project_id=project.project_id)
    survey_results = gizmo_survey.survey.survey_results
    judgements = []
    try:
        keywords_facettes = facettes_service.load_facettes_list(project.project_id)
        journals_facettes = facettes_service.load_facettes_list(project.project_id, 'journal')
    except IOError:
        facettes_service.generate_lists(project.project_id)
        keywords_facettes = facettes_service.load_facettes_list(project.project_id)
        journals_facettes = facettes_service.load_facettes_list(project.project_id, 'journal')
    for result in survey_results:
        replace_index_by_clear_name(result.selected_keywords, keywords_facettes)
        replace_index_by_clear_name(result.unselected_keywords, keywords_facettes)
        replace_index_by_clear_name(result.selected_journals, journals_facettes)
        replace_index_by_clear_name(result.unselected_journals, journals_facettes)
        judgements = judgements + result.judgements
    generate_judgement_file(judgements, project.project_id)
    return gizmo_survey.survey


def get_path_to_judgement_file(project_id, query_id):
    with app.app_context():
        location = app.config.get("LIBINTEL_DATA_DIR")
    path_to_file = '{}/out/{}/{}/sample_judgement_identifier_list.csv'.format(location, project_id, query_id)
    return path_to_file
