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
    def query_string(owner, name, until, cursor):
        return """
        query { 
          repository(owner:"%(owner)s", name:"%(name)s") {
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 100, until: "%(until)s", after: %(cursor)s) {
                    nodes {
                      oid
                      author {
                        email
                        name
                        user {
                            databaseId
                            login
                        }
                      }
                      committedDate
                    }
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                  }
                }
              }
            }
          }
          rateLimit {
            remaining
            resetAt
          }
        }
        """ % {'owner': owner, 'name': name, 'until': until, 'cursor': cursor}

    def query_commits_search(self, owner, name, until, cursor, level=0):
        def new_attempt(_time):
            time.sleep(_time)
            self.query_commits_search(owner, name, until, cursor, level + 1)
            if level == 0:
                print('success!')

        try:
            request = requests.post(url='https://api.github.com/graphql',
                                    json={'query': self.query_string(owner, name, until, cursor)},
                                    headers={"Authorization": "Token " + manager.get_active_token()},
                                    timeout=10)
            if request.status_code == 200:
                self.response = request.json()
            else:
                print('query for (owner: {}, name: {}, until: {}, cursor: {}) failed: {}'.format(owner, name, until,
                                                                                                 cursor,
                                                                                                 request.status_code))
                new_attempt(self.error_code_wait)
        except requests.exceptions.Timeout as err:
            print('query for (owner: {}, name: {}, until: {}, cursor: {}) failed: {}'.format(owner, name, until,
                                                                                             cursor, err))
            new_attempt(self.timeout_wait)
        except requests.exceptions.ConnectionError as err:
            print('query for (owner: {}, name: {}, until: {}, cursor: {}) failed: {}'.format(owner, name, until,
                                                                                             cursor, err))
            new_attempt(self.connection_loss_wait)

    def query_commits(self):
        projects = pd.read_csv(PROJECTS, index_col=False)
        projects = projects[projects['package.json']]
        projects = projects['repository'].to_list()
        try:
            with open(COMMITS, 'w', encoding='utf-8') as output_file:
                writer = csv.writer(output_file)
                writer.writerow(['repository', 'oid', 'email', 'name', 'login', 'id', 'committedDate'])
                logs = []
                until = today + "T00:00:00"
                for project in tqdm(projects):
                    has_next_page = True
                    start_cursor = 'null'
                    slug = project.split('/')
                    owner = slug[0]
                    name = slug[1]
                    while has_next_page:
                        self.query_commits_search(owner, name, until, start_cursor)
                        try:
                            page_info = self.response['data']['repository']['defaultBranchRef']['target']['history'][
                                'pageInfo']
                            has_next_page = page_info['hasNextPage']
                            if has_next_page:
                                start_cursor = '"' + page_info['endCursor'] + '"'
                            commits = self.response['data']['repository']['defaultBranchRef']['target']['history'][
                                'nodes']
                            for commit in commits:
                                oid = commit['oid']
                                committed_date = commit['committedDate']
                                try:
                                    author_email = commit['author']['email']
                                    author_name = commit['author']['name']
                                    try:
                                        author_login = commit['author']['user']['login']
                                        author_id = commit['author']['user']['databaseId']
                                    except TypeError:  # no id
                                        author_login = 'deleted!user'
                                        author_id = None
                                except TypeError:  # deleted author
                                    author_email = 'deleted!user'
                                    author_name = 'deleted!user'
                                    author_login = 'deleted!user'
                                    author_id = None
                                writer.writerow([project, oid, author_email, author_name, author_login, author_id,
                                                 committed_date])
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
                            print("failed (owner: {}, name: {}, cursor: {}): {}".format(owner, name, start_cursor, err))
                            has_next_page = False
                            manager.decrease_remaining()
                            logs.append(
                                "failed (owner: {}, name: {}, cursor: {}): {}".format(owner, name, start_cursor, err))
                        except KeyError as err:
                            print("failed (owner: {}, name: {}, cursor: {}): {}".format(owner, name, start_cursor, err))
                            has_next_page = False
                            manager.decrease_remaining()
                            logs.append(
                                "failed (owner: {}, name: {}, cursor: {}): {}".format(owner, name, start_cursor, err))

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
    requester.query_commits()
