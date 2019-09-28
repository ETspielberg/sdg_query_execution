import requests
from flask import current_app as app

from model import SurveyResult


class SurveyGizmoSurvey:
    def __init__(self, survey_id):
        with app.app_context():
            self._key = app.config.get("LIBINTEL_SURVEY_GIZMO_API_KEY")
            self._secret = app.config.get("LIBINTEL_SURVEY_GIZMO_API_SECRET")
            self._survey_gizmo_url = 'https://restapi.surveygizmo.eu/v5'

        self._base_url = self._survey_gizmo_url + '/survey/' + survey_id
        url = self._base_url + '?api_token=' + self._key + '&api_token_secret=' + self._secret
        r = requests.get(url)
        if r.status_code == 200:
            pages = r.json()['data']['pages']
            for page in pages:
                if 'Publications Contributing to this SDG' in page['title']:
                    for question in page['questions']:
                        if 'MATRIX' in question['type']:
                            for sub_question in question['sub_question']:
                                if 'RADIO' in sub_question['type']:
                                    self._judgment_question_number = sub_question['id']
                                elif 'TEXTBOX' in sub_question['type']:
                                    self._eid_question_number = sub_question['id']
                if 'Select Keywords' in page['title']:
                    for question in page['questions']:
                        if 'CHECKBOX' in question['type']:
                            self._keywords_question_number = question['id']
                            self._keywords_options_number = []
                            for option in question['options']:
                                self._keywords_options_number.append(option['id'])
                if 'Select the Journals' in page['title']:
                    for question in page['questions']:
                        if 'CHECKBOX' in question['type']:
                            self._journal_question_number = question['id']
                            self._journal_options_number = []
                            for option in question['options']:
                                self._journal_options_number.append(option['id'])
                if 'Terminology' in page['title']:
                    for question in page['questions']:
                        if 'ESSAY' in question['type']:
                            self._terminology_question_number = question['id']

    def get_survey_results(self):
        url = self._base_url + '/surveyresponse' + '?api_token=' + self._key + '&api_token_secret=' + self._secret + 'filter[value][0]=Complete&filter[field][0]=status&filter[operator][0]==&filter[field][1]=is_test_data&filter[field][1]==&filter[field][1]=0'
        r = requests.get(url)
        survey_results = []
        if r.status_code == 200:
            for result in r.json()['data']:
                single_result = SurveyResult
                single_result._session = result['SessionID']
                single_result._suggested_keywords = result['[question(' + self._terminology_question_number + ')]']
                for journal_option in self._journal_options_number:
                    key = '[question(' + self._journal_question_number + '), option(' + journal_option + ')]'
                    try:
                        single_result._selected_journals.append(result[key])
                    except:
                        print(key + ' not selected')
                for keyword_option in self._keyword_options_number:
                    key = '[question(' + self._journal_question_number + '), option(' + keyword_option + ')]'
                    try:
                        single_result._selected_keywords.append(result[key])
                    except:
                        print(key + ' not selected')
                for i in range(1, 100):
                    if i not in single_result._selected_journals:
                        single_result._unselected_journals.append(i)
                    if i not in single_result._selected_keywords:
                        single_result._unselected_keywords.append(i)
                    key_eid = '[question(' + self._eid_question_number + '), question_pipe(\"' + str(i) + '\")]'
                    key_judgement = '[question(' + self._judgment_question_number + '), question_pipe(\"' + str(i) + '\")]'
                    single_result._judgements.append({'eid': result[key_eid], 'judgement': ('Yes' in result[key_judgement])})
                survey_results.append(single_result)


