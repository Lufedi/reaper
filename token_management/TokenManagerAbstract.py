import abc
from datetime import datetime, timedelta
import time


class TokenManagerAbstract(metaclass=abc.ABCMeta):
    timeout_wait = 2
    connection_loss_wait = 60
    error_code_wait = 1

    def set_timeout_wait(self, period):
        self.timeout_wait = period

    def set_connection_loss_wait(self, period):
        self.connection_loss_wait = period

    def set_error_code_wait(self, period):
        self.error_code_wait = period

    @abc.abstractmethod
    def check_state(self, token_id):
        pass

    @abc.abstractmethod
    def override_state(self, token_id, state):
        pass

    @abc.abstractmethod
    def update_state(self, rate_info):
        pass

    @abc.abstractmethod
    def decrease_remaining(self):
        pass

    @abc.abstractmethod
    def update_active_token(self):
        pass

    @abc.abstractmethod
    def get_active_token(self):
        pass

    @staticmethod
    def wait_until(until, period=60):
        while datetime.now() < until:
            time.sleep(period)

