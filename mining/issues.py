import sys
import requests
from tqdm import tqdm
import csv
import time
import json
import pandas as pd

sys.path.append('..')
from config import *  # noqa: E402
from finder import *  # noqa: E402
from token_management import TokenManagerGraphQL  # noqa: E402


class RepositoryRequest:

    def __init__(self, error_code_wait=1, timeout_wait=2, connection_loss_wait=60):
        self.error_code_wait = error_code_wait
        self.timeout_wait = timeout_wait
        self.connection_loss_wait = connection_loss_wait
        self.response = None

    @staticmethod
    def query_string(owner, name, until):
        return """
        query { 
          search(first: 1, query: "repo:%(owner)s/%(name)s created:<%(until)s", type: ISSUE) {
            issueCount
          }
          rateLimit {
            remaining
            resetAt
          }
        }
        """ % {'owner': owner, 'name': name, 'until': until}

    def query_issues_search(self, owner, name, until, level=0):
        def new_attempt(_time):
            time.sleep(_time)
            self.query_issues_search(owner, name, until, level + 1)
            if level == 0:
                print('success!')

        try:
            request = requests.post(url='https://api.github.com/graphql',
                                    json={'query': self.query_string(owner, name, until)},
                                    headers={"Authorization": "Token " + manager.get_active_token()},
                                    timeout=10)
            if request.status_code == 200:
                self.response = request.json()
            else:
                print('query for (owner: {}, name: {}, until: {}) failed: {}'.format(owner, name, until,
                                                                                     request.status_code))
                new_attempt(self.error_code_wait)
        except requests.exceptions.Timeout as err:
            print('query for (owner: {}, name: {}, until: {}) failed: {}'.format(owner, name, until, err))
            new_attempt(self.timeout_wait)
        except requests.exceptions.ConnectionError as err:
            print('query for (owner: {}, name: {}, until: {} failed: {}'.format(owner, name, until, err))
            new_attempt(self.connection_loss_wait)

    def query_issues(self):
        projects = pd.read_csv(PROJECTS, index_col=False)
        projects = projects[projects['package.json']]
        projects = projects['repository'].to_list()
        try:
            with open(ISSUES, 'w', encoding='utf-8') as output_file:
                writer = csv.writer(output_file)
                writer.writerow(['repository', 'issues'])
                logs = []
                until = today
                for project in tqdm(projects):
                    slug = project.split('/')
                    owner = slug[0]
                    name = slug[1]
                    self.query_issues_search(owner, name, until)
                    try:
                        issue_count = self.response['data']['search']['issueCount']
                        writer.writerow([project, issue_count])
                        try:
                            rate_info = self.response['data']['rateLimit']
                            manager.update_state(rate_info)
                        except TypeError as err:
                            print("failed to retrieve rateLimit: {}".format(err))
                            manager.decrease_remaining()
                        except KeyError as err:
                            print("failed to retrieve rateLimit: {}".format(err))
                            manager.decrease_remaining()
                    except TypeError as err:
                        print("failed (owner: {}, name: {}): {}".format(owner, name, err))
                        manager.decrease_remaining()
                        logs.append(
                            "failed (owner: {}, name: {}): {}".format(owner, name, err))
                    except KeyError as err:
                        print("failed (owner: {}, name: {}): {}".format(owner, name, err))
                        manager.decrease_remaining()
                        logs.append(
                            "failed (owner: {}, name: {}): {}".format(owner, name, err))

                try:
                    with open(PATH_LOGS_DATA(os.path.basename(__file__)), 'w', encoding='utf-8') as logs_file:
                        writer = csv.writer(logs_file)
                        for log in logs:
                            writer.writerow([log])
                except IOError as err:
                    print(err)
        except IOError as err:
            print(err)


if __name__ == '__main__':
    manager = TokenManagerGraphQL(github_tokens)
    requester = RepositoryRequest()
    requester.query_issues()
