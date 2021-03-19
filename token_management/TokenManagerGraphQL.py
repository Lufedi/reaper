from token_management.TokenManagerAbstract import TokenManagerAbstract
from datetime import datetime, timedelta
import requests
import time


class TokenManagerGraphQL(TokenManagerAbstract):

    def __init__(self, tokens):
        self.tokens = tokens
        self.tokens_state = dict()
        self.active_token_id = None
        self.query = """
                        query {
                            rateLimit {
                                remaining
                                resetAt
                            }
                        }
                        """
        for index, token in enumerate(tokens):
            self.check_state(index)
        self.update_active_token()

    def check_state(self, token_id, level=0):
        def new_attempt(_time):
            print('waiting {} seconds and trying again...'.format(_time))
            time.sleep(_time)
            print('new attempt...')
            self.check_state(token_id, level + 1)
            if level == 0:
                print('success!')
        try:
            request = requests.post(url='https://api.github.com/graphql', json={'query': self.query},
                                    headers={"Authorization": "Token " + self.tokens[token_id]}, timeout=10)
            if request.status_code == 200:
                result = request.json()
                self.tokens_state[self.tokens[token_id]] = [result['data']['rateLimit']['remaining'],
                                                            datetime.strptime(result['data']['rateLimit']['resetAt'],
                                                                              '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=1)
                                                            ]
            else:
                print('rateLimit query failed to run by returning code of {} when using token (id: {}, sha: )'.format(
                    request.status_code, token_id, self.tokens[token_id]))
                new_attempt(self.error_code_wait)
        except requests.exceptions.Timeout as err:
            print('rateLimit query failed to {}'.format(err))
            new_attempt(self.timeout_wait)
        except requests.exceptions.ConnectionError as err:
            print('rateLimit query failed to {}'.format(err))
            new_attempt(self.connection_loss_wait)

    def override_state(self, token_id, state):
        pass

    def update_state(self, rate_info):
        self.tokens_state[self.tokens[self.active_token_id]] = [
            rate_info['remaining'],
            datetime.strptime(rate_info['resetAt'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=1)
        ]
        if rate_info['remaining'] == 0:
            print('token (id: {}, sha: {}) reached the hour limit'.format(
                self.active_token_id, self.tokens[self.active_token_id]))
            print('searching for another token...')
            self.update_active_token()

    def decrease_remaining(self):
        self.tokens_state[self.tokens[self.active_token_id]] = [
            self.tokens_state[self.tokens[self.active_token_id]][0] - 1,
            self.tokens_state[self.tokens[self.active_token_id]][1]
        ]
        if self.tokens_state[self.tokens[self.active_token_id]][0] == 0:
            print('token (id: {}, sha: {}) reached the hour limit'.format(
                self.active_token_id, self.tokens[self.active_token_id]))
            print('searching for another token...')
            self.update_active_token()

    def update_active_token(self):
        ready_tokens = []
        for key, value in self.tokens_state.items():
            if value[0] != 0 or (value[0] == 0 and value[1] < datetime.now()):
                ready_tokens.append(key)
        if len(ready_tokens) > 0:
            self.active_token_id = self.tokens.index(ready_tokens[0])
            print('new active token: (id: {}, sha: {})'.format(self.active_token_id, self.tokens[self.active_token_id]))
        else:
            times = []
            for key, value in self.tokens_state.items():
                times.append(value[1])
            print('all tokens reached the hour limit. waiting until {}...'.format(min(times)))
            self.wait_until(min(times), 60)
            self.active_token_id = times.index(min(times))
            print('new active token: (id: {}, sha: {})'.format(self.active_token_id, self.tokens[self.active_token_id]))

    def get_active_token(self):
        return self.tokens[self.active_token_id]
