# SDG query execution


## Setup

### Clone project

```
git clone https://github.com/ETspielberg/sdg_query_execution.git
```


### Install requirements

The programme is written as python flask application. 
Necessary dependencies are listed in the requirements.txt and can be installed via

```
$ pip install -r requirements.txt
```

### Configuration

The configuration needs only the folder where the csv files with the usage data are stored.
To implement it into a microservice framework it can be configured to the upload directory of the system.
In any case, a subdirectory `/ebslists` is appended.

```
LIBINTEL_DATA_DIR = "${USER_HOME}/.libintel/data"
LIBINTEL_USER_EMAIL = "mike.smith@example.com"

ELSEVIER_URL = "https://api.elsevier.com"
SCOPUS_API_KEY = "<api-key>"
SCIVAL_API_KEY = ""

ALTMETRIC_URL = "https://api.altmetric.com/v1/"
ALTMETRIC_API_KEY = "<api-key>"

UNPAYWALLL_API_URL = "https://api.unpaywall.org/my/request"
```

### Start-Up into development server

To start the application the virtual environment has to be activated.
After that some environmental parameters need to be set for the flask application.
For a development version the following code can be executed: 

```
./venv/Scripts/activate
$env:FLASK_APP="start.py"
$env:FLASK_ENV="development"
$env:LIBINTEL_SETTINGS = "${USER_HOME}\.libintel\config\query_execution.cfg"
python -m flask run
```

File is saved in the upload directory specified in the config file.

## Running an analysis


