################
#    imports   #
################

from service import query_service
from . import query_viewer_blueprint


################
#    routes    #
################

@query_viewer_blueprint.route("/view/<project>/<version>/<name>", methods=['GET'])
def display_query(project, version, name):
    return query_service.get_versioned_query_as_html(project, version, name)