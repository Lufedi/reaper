from attributes.unit_test.discoverer import TestDiscoverer


class JavaScriptTestDiscoverer(TestDiscoverer):
    def __init__(self):
        self.language = 'JavaScript'
        self.languages = ['JavaScript']
        self.extensions = ['*.js']
        self.frameworks = [
            self.__mocha__,
            self.__qunit__
        ]

    # Qunit
    def __qunit__(self, path, sloc):
        pattern = 'QUnit.test\(.*\)'
        return self.measure(path, sloc, pattern)

    # Mocha, Jest, Jasmine
    def __mocha__(self, path, sloc):
        pattern = '(describe\()(.*),(.*)\(\)'
        return self.measure(path, sloc, pattern)
