import json
import os
import unittest

from attributes.architecture import main
from tests import REPOS_PATH


class MainTestCase(unittest.TestCase):
    @unittest.skipIf(not os.path.exists(REPOS_PATH), 'setup.sh not run.')
    def test_main(self):
        result, value = main.run(0, os.path.join(REPOS_PATH, 'superagent'), MockCursor('js'), threshold=0)
        self.assertTrue(result)
        self.assertLess(0, value)


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

    def close(self):
        pass