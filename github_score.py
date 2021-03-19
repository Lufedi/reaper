import shutil
import sys
import csv
import pandas as pd
from tqdm import tqdm
from lib.attributes import Attributes
from attributes.continuous_integration import main as ci_main
from attributes.architecture import main as architecture_main
from attributes.documentation import main as documentation_main
from attributes.unit_test.discoverer import get_test_discoverer
from datetime import datetime
from dateutil import relativedelta
from finder import *
from config import *
from clone_all import clone


class MockCursor(object):
    def __init__(self, language):
        self.language = language

    def execute(self, string):
        pass

    def fetchone(self):
        if self.language == 'js':
            return ['JavaScript']
        elif self.language == 'c':
            return ['C']
        elif self.language == 'rb':
            return ['Ruby']
        elif self.language == 'csharp':
            return ['C#']
        elif self.language == 'java':
            return ['Java']
        elif self.language == 'php':
            return ['PHP']
        elif self.language == 'cpp':
            return ['C++']
        elif self.language == 'swift':
            return ['Swift']
        elif self.language == 'py':
            return ['Python']
        elif self.language == 'oc':
            return ['Objective-C']

    def close(self):
        pass


class MockCursor2(object):
    def __init__(self, language):
        self.language = language

    def execute(self, string):
        pass

    def fetchone(self):
        return [self.language]

    def close(self):
        pass


# function to compute the history score
def get_history_score(table, first, last):
    delta = relativedelta.relativedelta(last, first)
    num_months = delta.years * 12 + delta.months
    num_commits = len(table.index)
    if num_months >= 1:
        return num_commits / num_months
    else:
        return 0


# function to compute the management score
def get_management_score(table, first, last):
    delta = relativedelta.relativedelta(last, first)
    num_months = delta.years * 12 + delta.months
    num_commits = len(table.index)
    if num_months >= 1:
        return num_commits / num_months
    else:
        return 0


# function to compute the contributor score
def get_contributor_score(table):
    unique_contributors = list(set(table['name'].to_list()))
    num_commits = len(table.index)
    nr_commits = []
    for contributor in unique_contributors:
        nr_commits.append(len(table[table['name'] == contributor].index))
    nr_commits = sorted(nr_commits, reverse=True)
    aggregate = 0
    num_core_contributors = 0
    for nr in nr_commits:
        num_core_contributors += 1
        aggregate += nr
        if (aggregate / num_commits) >= 0.8:
            break
    return num_core_contributors


if __name__ == '__main__':
    df_projects = pd.read_csv(PROJECTS, index_col=False)  # read .csv with projects to analyse
    projects = df_projects['repository'].to_list()  # extract slugs (owner/name)
    languages = df_projects['language'].to_list()  # extract languages
    commits = pd.read_csv(COMMITS, index_col=False)  # read commits
    issues = pd.read_csv(ISSUES, index_col=False)  # read issues
    licenses = pd.read_csv(LICENSES, index_col='repository')  # read licenses
    try:
        with open(RESULTS, 'w') as out_file:
            writer = csv.writer(out_file)
            header = ['project']
            header.extend(FEATURES)
            writer.writerow(header)  # write header to csv
            for index, project in tqdm(enumerate(projects)):
                results = []  # array to store results
                fake_cursor = MockCursor2(languages[index])  # fake cursor to mimic response of GHTorrent query
                p_slug = project.split('/')
                p_owner = p_slug[0]  # project owner
                p_name = p_slug[1]  # project name
                p_commits = commits[commits['repository'] == project].copy()  # extract associated commits
                # translate the column of strings to column of datetime objects
                p_commits['committedDate'] = p_commits['committedDate'].apply(lambda x:
                                                                              datetime.strptime(x,
                                                                                                "%Y-%m-%dT%H:%M:%SZ"))
                # sort commits by commit-date in descending order
                p_commits.sort_values(by=['committedDate'], inplace=True, ascending=False)
                p_commits = p_commits.reset_index()  # reset index to query later
                p_issues = issues[issues['repository'] == project].copy()
                latest_time = p_commits.loc[0, 'committedDate']  # query the date of the latest commit
                # query the date of the earliest commit
                earliest_time = p_commits.loc[len(p_commits.index)-1, 'committedDate']
                if not clone_all:
                    p_file_name = clone(p_owner, p_name, DIR_CLONED, today)  # clone now
                else:
                    p_file_name = os.path.join(DIR_CLONED, p_owner, p_name)  # already cloned
                for feature in FEATURES:
                    if feature == 'architecture':
                        _, a_score = architecture_main.run(None, p_file_name, fake_cursor, threshold=0)
                        results.append(a_score)
                    elif feature == 'management':
                        m_score = get_management_score(p_issues, earliest_time, latest_time)
                        results.append(m_score)
                    elif feature == 'community':
                        c_score = get_contributor_score(p_commits)
                        results.append(c_score)
                    elif feature == 'continuous_integration':
                        _, ci_score = ci_main.run(None, p_file_name, None)
                        results.append(ci_score)
                    elif feature == 'documentation':
                        _, d_score = documentation_main.run(None, p_file_name, fake_cursor, threshold=0)
                        results.append(d_score)
                    elif feature == 'history':
                        h_score = get_history_score(p_commits, earliest_time, latest_time)
                        results.append(h_score)
                    elif feature == 'license':
                        l_score = int(licenses.loc[project, 'license'])
                        results.append(l_score)
                    elif feature == 'unit_test':
                        u_score = get_test_discoverer(languages[index]).discover(p_file_name)
                        results.append(u_score)
                if delete_after:
                    shutil.rmtree(p_file_name)  # delete analysed repository if declared in config
                to_write = project
                to_write.extend(results)
                writer.writerow(to_write)  # write results to file
    except IOError as err:
        print(err)
