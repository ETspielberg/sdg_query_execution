import requests
from flask import current_app as app


class Unpaywall:

    def __init__(self, doi):
        with app.app_context():
            email = app.config.get("LIBINTEL_USER_EMAIL")
        self.unpaywall_url = "https://api.unpaywall.org/my/request"
        self.email = email
        url = self.unpaywall_url + '/' + doi + "?email=" + self.email
        r = requests.get(url)
        print("queryied URL: " + url + " with status code " + str(r.status_code))
        if r.status_code == 200:
            self.json = r.json()['results'][0]
            self._doi = self.json['doi']
            self._doi_resolver = self.json['doi_resolver']
            self._evidence = self.json['evidence']
            self._free_fulltext_url = self.json['free_fulltext_url']
            self._is_boai_license = self.json['is_boai_license']
            self._is_free_to_read = self.json['is_free_to_read']
            self._is_subscription_journal = self.json['is_subscription_journal']
            self._license = self.json['license']
            self._oa_color = self.json['oa_color']
            self._reported_noncompliant_copies = self.json['reported_noncompliant_copies']
            try:
                self._title = self.json['title']
            except KeyError:
                self._title = "no title given"
            self._url = self.json['url']
        else:
            self.json = None
            self._doi = None
            self._doi_resolver = None
            self._evidence = None
            self._free_fulltext_url = None
            self._is_boai_license = None
            self._is_free_to_read = None
            self._is_subscription_journal = None
            self._license = None
            self._oa_color = None
            self._reported_noncompliant_copies = None
            self._title = None
            self._url = None

    @property
    def doi(self):
        return self._doi

    @property
    def doi_resolver(self):
        return self._doi_resolver

    @property
    def evidence(self):
        return self._evidence

    @property
    def free_fulltext_url(self):
        return self._free_fulltext_url

    @property
    def is_boai_license(self):
        return self._is_boai_license

    @property
    def is_free_to_read(self):
        return self._is_free_to_read

    @property
    def is_subscription_journal(self):
        return self._is_subscription_journal

    @property
    def license(self):
        return self._license

    @property
    def oa_color(self):
        return self._oa_color

    @property
    def reported_noncompliant_copies(self):
        return self._reported_noncompliant_copies

    @property
    def title(self):
        return self._title

    @property
    def url(self):
        return self._url

    def __getstate__(self):
        state = self.__dict__.copy()
        try:
            del state['email']
            del state['unpaywall_url']
            del state['json']
            return state
        except KeyError:
            return state
