class ScopusCitationResponse:

    def __init__(self):
        self.id = ""
        self.type_of_id = ""
        self.citation_count = ""

    def to_output(self, delimiter):
        string = self.id
        string += delimiter
        string += self.type_of_id
        string += delimiter
        string += self.citation_count
        return string
