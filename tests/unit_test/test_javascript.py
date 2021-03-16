import os
import unittest

from attributes.unit_test.discoverer import get_test_discoverer
from tests import get_lsloc, REPOS_PATH


class JavaScriptTestDiscovererTestCase(unittest.TestCase):
    def setUp(self):
        self.discoverer = get_test_discoverer('JavaScript')

    @unittest.skipIf(not os.path.exists(REPOS_PATH), 'setup.sh not run.')
    def test_discover_mocha(self):
        # Test: Project using Mocha
        path = os.path.join(REPOS_PATH, 'superagent')
        proportion = self.discoverer.discover(path)
        self.assertLess(0, proportion)

    @unittest.skipIf(not os.path.exists(REPOS_PATH), 'setup.sh not run.')
    def test_discover_qunit(self):
        # Test: Project using QUnit
        path = os.path.join(REPOS_PATH, 'jquery-mobile')
        proportion = self.discoverer.discover(path)
        self.assertLess(0, proportion)

    @unittest.skipIf(not os.path.exists(REPOS_PATH), 'setup.sh not run.')
    def test_mocha(self):
        # Test: Project using Mocha
        path = os.path.join(REPOS_PATH, 'superagent')
        proportion = self.discoverer.__mocha__(
            path, get_lsloc(path, self.discoverer.languages)
        )
        self.assertLess(0, proportion)

    @unittest.skipIf(not os.path.exists(REPOS_PATH), 'setup.sh not run.')
    def test_no_mocha(self):
        # Test: Project not using Mocha
        path = os.path.join(REPOS_PATH, 'jquery-mobile')
        proportion = self.discoverer.__mocha__(
            path, get_lsloc(path, self.discoverer.languages)
        )
        self.assertEqual(0, proportion)

    @unittest.skipIf(not os.path.exists(REPOS_PATH), 'setup.sh not run.')
    def test_qunit(self):
        # Test: Project using Mocha
        path = os.path.join(REPOS_PATH, 'jquery-mobile')
        proportion = self.discoverer.__qunit__(
            path, get_lsloc(path, self.discoverer.languages)
        )
        self.assertLess(0, proportion)

    @unittest.skipIf(not os.path.exists(REPOS_PATH), 'setup.sh not run.')
    def test_no_qunit(self):
        # Test: Project using Mocha
        path = os.path.join(REPOS_PATH, 'superagent')
        proportion = self.discoverer.__qunit__(
            path, get_lsloc(path, self.discoverer.languages)
        )
        self.assertEqual(0, proportion)
