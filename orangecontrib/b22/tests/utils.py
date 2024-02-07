import contextlib
import io
import sys
import os
import unittest




@contextlib.contextmanager
def nostderr():
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    yield
    sys.stderr = original_stderr




class ExampleValidTest(unittest.TestCase):
    def test_example(self):
        self.assertEqual(True, True, "This test shouldn't ever fail!")




class ExampleInvalidTest(unittest.TestCase):
    def test_example(self):
        self.assertEqual(True, False, "This test is expected to fail!")



class SkipTest(unittest.TestCase):
    def runTest(self):
        raise unittest.SkipTest("Test would take to long.")



class TestRunner:
    def __init__(self, test_classes=None, verbosity=2):
        self.verbosity = verbosity

        self.loader = unittest.TestLoader()
        self.runner = unittest.TextTestRunner(verbosity=self.verbosity)

        if test_classes is None:
            test_classes = []

        if not isinstance(test_classes, list):
            if not issubclass(test_classes, unittest.TestCase):
                raise Exception
            
            test_classes = [test_classes]
        
        self.test_classes = test_classes


    def addTestClasses(self, test_classes):
        if not isinstance(test_classes, list):
            if not issubclass(test_classes, unittest.TestCase):
                raise Exception
            
            test_classes = [test_classes]

        self.test_classes.extend(test_classes)

    
    def run(self):
        return self.runner.run(unittest.TestSuite([
            self.loader.loadTestsFromTestCase(c) for c in self.test_classes
        ]))




if __name__ == "__main__":
    runner = TestRunner([ExampleValidTest, ExampleInvalidTest])
    runner.run()