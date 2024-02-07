import os
import unittest

from orangecontrib.b22 import __file__ as ROOT_FILE




def getRootDir():
    return os.path.dirname(ROOT_FILE)


def getTestDirs(root_dir=None, test_names=["tests"], ignore_dirs=["__pycache__", "icons"]):
    if root_dir is None:
        root_dir = getRootDir()

    test_dirs = []

    for root, dirs, _ in os.walk(root_dir, topdown=True):
        for test_name in test_names:
            try:
                dirs.remove(test_name)
                test_dirs.append(os.path.join(root, test_name))

            except ValueError:
                pass

        dirs[:] = [d for d in dirs if d not in ignore_dirs]

    return test_dirs


def removeExamples(test_group):
    """_summary_

    Example tests (tests ending with '_example') are meant to be used
    by other tests, meaning they should NOT be run by the main testing
    suite, as some may be MEANT to fail.

    Parameters
    ----------
    test_group : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """
    if hasattr(test_group, "_tests"):
        test_group._tests = list(filter(lambda test: removeExamples(test) is not None, test_group._tests))
    
    else:
        name = test_group._testMethodName
        if len(name) >= 12 and name[-8:] == "_example":
            return None
    
    return test_group


def suite(loader=None, pattern=None):
    if loader is None:
        loader = unittest.TestLoader()

    if pattern is None:
        pattern = "test*.py"

    test_dirs = getTestDirs()

    all_tests = [loader.discover(d, pattern, d) for d in test_dirs]

    return removeExamples(unittest.TestSuite(all_tests))


def load_tests(loader, tests, pattern):
    return suite(loader, pattern)




if __name__ == '__main__':
    unittest.main(defaultTest='suite')
