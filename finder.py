import os
from datetime import datetime

# root directory
DIR_ROOT = os.path.dirname(os.path.abspath(__file__))
# directory for storing the data: mined and results
DIR_DATA = os.path.join(DIR_ROOT, 'data')
# directory for storing the logs after mining
DIR_LOGS = os.path.join(DIR_ROOT, 'logs')
# directory for storing the cloned projects
DIR_CLONED = os.path.join(os.path.dirname(DIR_ROOT), 'cloned')


# function to resolve the name for the log file, given the mining script and the time of its execution
def PATH_LOGS_DATA(file_name):
    return os.path.join(DIR_LOGS, file_name.replace(".py", "@") + datetime.now().strftime("%Y%m%d%H%M%S") + ".csv")


# path containing the list of projects to compute the features for
PROJECTS = os.path.join(DIR_DATA, 'projects.csv')
# path containing the information about the mined commits
COMMITS = os.path.join(DIR_DATA, 'commits.csv')
# path containing the information about the mined issues
ISSUES = os.path.join(DIR_DATA, 'issues.csv')
# path containing the information on whether a project contains a license or not
LICENSES = os.path.join(DIR_DATA, 'licenses.csv')
# path to store the results of the feature computation
RESULTS = os.path.join(DIR_DATA, 'results.csv')
