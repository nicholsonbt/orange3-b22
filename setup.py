#!/usr/bin/env python

import os
import sys

from setuptools import setup, find_packages




class Version:
    """ Version representation

    Represents a version number (such as '2.6.7').
    """

    def __init__(self, values):
        """Create a new version representation.

        Creates a new version representation for either a string version
        (such as "2.6.7") or a list (such as '[2, 6, 7]').

        Parameters
        ----------
        values : str | list
            The version to be represented.
        """

        if isinstance(values, str):
            values = [int(v) for v in values.split(".")]

        assert(isinstance(values, list))
        assert(len(values) >= 1)
        assert(all([isinstance(value, int) for value in values]))

        self.values = values
    

    def __repr__(self):
        """ A string representation of the given version.

        Returns
        -------
        str
            The version as a string (such as '2.6.7').
        """

        return ".".join([str(val) for val in self.values])
    
    
    @staticmethod
    def compare(v1, v2):
        """ Compare two version instances.

        Parameters
        ----------
        v1 : Version
            A version instance to be compared with 'v2'.
        v2 : Version
            A version instance to be compared with 'v1'.

        Returns
        -------
        int
            A comparison code representing the relationship between
            'v1' and 'v2'.

        Notes
        -----
        Codes:
        0 : v1 == v2
        1 : v1 > v2
        2 : v1 < v2
        3 : v1 is a subset of v2
        4 : v1 is a superset of v2
        """

        assert(isinstance(v1, Version))
        assert(isinstance(v2, Version))

        for i in range(min(len(v1.values), len(v2.values))):
            if v1.values[i] > v2.values[i]:
                return 1
            
            if v1.values[i] < v2.values[i]:
                return 2
            
        if len(v1.values) == len(v2.values):
            return 0
        
        if len(v1.values) > len(v2.values):
            return 3
        
        return 4
    



class Requirement:
    """_summary_

    _extended_summary_
    """

    def __init__(self, equality, version):
        """_summary_

        _extended_summary_

        Parameters
        ----------
        equality : str
            The equality sign of the given version requirement.
        version : str | Version
            The version required (with respect to the equality).
        """

        if isinstance(version, str):
            version = Version(version)

        assert(isinstance(equality, str))
        assert(isinstance(version, Version))

        self.equality = equality
        self.version = version


    def __repr__(self):
        """_summary_

        _extended_summary_

        Returns
        -------
        str
            _description_
        """

        return self.equality + str(self.version)


    @staticmethod
    def compare(v1, v2):
        """_summary_

        _extended_summary_

        Parameters
        ----------
        v1 : Requirement
            A requirement instance to be compared with 'v2'.
        v2 : Requirement
            A requirement instance to be compared with 'v1'.

        Returns
        -------
        int
            A comparison code representing the relationship between
            'v1' and 'v2'.
        
        Notes
        -----
        Codes:
        0 : v1 == v2
        1 : v1 > v2
        2 : v1 < v2
        3 : v1 is a subset of v2
        4 : v1 is a superset of v2
        """

        assert(isinstance(v1, Requirement))
        assert(isinstance(v2, Requirement))

        return Version.compare(v1.version, v2.version)




class Bounds:
    """_summary_

    _extended_summary_
    """

    def __init__(self):
        """_summary_

        _extended_summary_
        """

        self.upper = None
        self.lower = None
        self.exclude = []


    def addBounds(self, bounds):
        """_summary_

        _extended_summary_

        Parameters
        ----------
        bounds : Bounds
            _description_
        """

        assert(isinstance(bounds, Bounds))

        valid = list(set([bounds.lower, bounds.upper]) - {None})

        for ver in bounds.exclude + valid:
            self.addRequirement(ver)


    def addRequirement(self, ver):
        """_summary_

        _extended_summary_

        Parameters
        ----------
        ver : Requirement
            _description_

        Raises
        ------
        Exception
            _description_

        Notes
        -----
        CASE ==:
        Ensure between upper and lower.
        Set as upper and lower.
        Ensure upper and lower not subset of same excluded.
        Remove redundant excluded.

        CASE >=:
        Check between upper and lower.
        Set as lower.
        Ensure upper and lower not subset of same excluded.
        Remove redundant excluded.

        CASE <=:
        Check between upper and lower.
        Set as upper.
        Ensure upper and lower not subset of same excluded.
        Remove redundant excluded.

        CASE !=:
        Add to excluded.
        Ensure upper and lower not subset of same excluded.
        Remove redundant excluded.

        CASE >:
        Check between upper and lower.
        Set as lower.
        Ensure upper and lower not subset of same excluded.
        Remove redundant excluded.

        CASE <:
        Check between upper and lower.
        Set as upper.
        Ensure upper and lower not subset of same excluded.
        Remove redundant excluded.
        """

        assert(isinstance(ver, Requirement))

        if ver.equality == "!=":
            # Add to excluded (!=).
            self.exclude.append(ver)

        else:
            valid = self.checkBetweenBounds(ver)

            # Ensure between upper and lower (==).
            assert(ver.equality != "==" or valid)

            # Ensure between upper and lower (>=, <=, >, <).
            if not valid:
                return
            
            # Set as lower and/or upper.
            if ver.equality == "==":
                self.lower = self.upper = ver

            elif ver.equality == ">=" or ver.equality == ">":
                self.lower = ver

            elif ver.equality == "<=" or ver.equality == "<":
                self.upper = ver

            else:
                raise Exception("Unknown equality given.")
            
        # Ensure if lower and upper are equal, they are both inclusive.
        if self.lower is not None and self.upper is not None:
            equal = Requirement.compare(self.lower, self.upper)

            if equal == 0:
                assert(self.lower.equality != ">")
                assert(self.upper.equality != "<")

        i = 0
        while i < len(self.exclude):
            exclude = self.exclude[i]

            valid_1 = Requirement.compare(self.lower, exclude)
            valid_2 = Requirement.compare(self.upper, exclude)

            # Ensure upper and lower not subset of same excluded.
            assert(valid_1 != 3 or valid_2 != 3)

            # Remove redundant excluded.
            if valid_1 == 1 or valid_2 == 2:
                self.exclude.pop(i)
            
            else:
                i += 1

        
    def checkBetweenBounds(self, version):
        """_summary_

        _extended_summary_

        Parameters
        ----------
        version : Requirement
            _description_

        Returns
        -------
        bool
            _description_

        Notes
        -----
        Codes:
        0 : v1 == v2
        1 : v1 > v2
        2 : v1 < v2
        3 : v1 is a subset of v2
        4 : v1 is a superset of v2
        """

        assert(isinstance(version, Requirement))

        if self.lower is not None:
            code = Requirement.compare(version, self.lower)

            if code == 2 or code == 4:
                return False
            
        if self.upper is not None:
            code = Requirement.compare(version, self.upper)

            if code == 1 or code == 4:
                return False
            
        
        for exclude in self.exclude:
            code = Requirement.compare(version, exclude)

            if code == 0 or code == 3:
                return False
            
        return True
    
    
    def __repr__(self):
        """_summary_

        _extended_summary_

        Returns
        -------
        str
            _description_
        """

        valid = list(set([self.lower, self.upper]) - {None})

        bounds = valid + self.exclude

        text = [str(ver) for ver in bounds]

        return ",".join(text)




class Requirements:
    """_summary_

    _extended_summary_
    """

    def __init__(self):
        """_summary_

        _extended_summary_
        """

        self.requirements = dict()


    def addRequirment(self, text):
        """_summary_

        _extended_summary_

        Parameters
        ----------
        text : str
            _description_
        """

        assert(isinstance(text, str))

        required, *additional = text.split(',')
        name, eq, ver = Requirements.partition(required)

        versions = [(eq, ver)] + [Requirements.partition(x)[1:] for x in additional]

        bounds = Bounds()

        for eq, ver in versions:
            if eq == "" and ver == "":
                continue
            
            assert(eq != "")
            assert(ver != "")

            bounds.addRequirement(Requirement(eq, Version(ver)))


        if name in self.requirements:
            self.requirements[name].addBounds(bounds)

        else:
            self.requirements[name] = bounds


    def getBounds(self):
        """_summary_

        _extended_summary_

        Returns
        -------
        list
            _description_
        """

        requirements = [k + str(self.requirements[k]) for k in self.requirements]

        return requirements


    @staticmethod
    def partition(text):
        """_summary_

        _extended_summary_

        Parameters
        ----------
        text : str
            _description_

        Returns
        -------
        tuple
            _description_
        """

        assert(isinstance(text, str))

        parts = text.partition("==")
        if parts[1] == "==":
            return parts
        
        parts = text.partition(">=")
        if parts[1] == ">=":
            return parts
        
        parts = text.partition("<=")
        if parts[1] == "<=":
            return parts
        
        parts = text.partition("!=")
        if parts[1] == "!=":
            return parts
        
        parts = text.partition(">")
        if parts[1] == ">":
            return parts

        return text.partition("<")




def readRequirements(*filenames):
    """_summary_

    _extended_summary_

    Returns
    -------
    list
        _description_
    """

    root = os.path.dirname(__file__)
    file_paths = [os.path.join(root, filename) for filename in filenames]

    requirements = sorted(set([line.partition('#')[0].strip()
                               for file_path in file_paths
                               for line in open(file_path)]) - {""})
    
    requirements = sorted(set(requirements) - {""})
    
    r = Requirements()

    for requirement in requirements:
        r.addRequirment(requirement)

    return r.getBounds()




def include_documentation(local_dir, install_dir):
    global DATA_FILES
    if 'bdist_wheel' in sys.argv and not os.path.exists(local_dir):
        print("Directory '{}' does not exist. "
              "Please build documentation before running bdist_wheel."
              .format(os.path.abspath(local_dir)))
        sys.exit(0)

    doc_files = []
    for dirpath, dirs, files in os.walk(local_dir):
        doc_files.append((dirpath.replace(local_dir, install_dir),
                          [os.path.join(dirpath, f) for f in files]))
    DATA_FILES.extend(doc_files)




NAME = "Orange3-B22"

VERSION = "0.0.1"

AUTHOR = "nicholsonbt"

AUTHOR_EMAIL = "b.nicholson@diamond.ac.uk"

URL = "https://github.com/nicholsonbt/orange3-b22"

DESCRIPTION = "Extends Orange with useful features for Diamond Light Source B22 beamline."

README_FILE = os.path.join(os.path.dirname(__file__), 'README.pypi')
LONG_DESCRIPTION = open(README_FILE).read()

LONG_DESCRIPTION_TYPE = "text/markdown"

LICENSE = "GPLv3+"

PYTHON_REQUIRES = ">3.8.0"

PACKAGES = find_packages()

PACKAGE_DATA = {
    'orangecontrib.b22.widgets': ['icons/*.svg'],
}

DATA_FILES = []

INSTALL_REQUIRES = readRequirements("requirements.txt")

EXTRAS_REQUIRE = {}

ENTRY_POINTS = {
    # Entry points that marks this package as an orange add-on. If set, addon will
    # be shown in the add-ons manager even if not published on PyPi.
    'orange3.addon': (
        'b22 = orangecontrib.b22',
    ),

    # Entry point used to specify packages containing tutorials accessible
    # from welcome screen. Tutorials are saved Orange Workflows (.ows files).
    'orange.widgets.tutorials': (
        # Syntax: any_text = path.to.package.containing.tutorials
        'b22tutorials = orangecontrib.b22.tutorials',
    ),

    # Entry point used to specify packages containing widgets.
    'orange.widgets': (
        # Syntax: category name = path.to.package.containing.widgets
        # Widget category specification can be seen in
        #    orangecontrib/example/widgets/__init__.py
        'B22 = orangecontrib.b22.widgets',
    ),

    # Register widget help
    "orange.canvas.help": (
        'html-index = orangecontrib.b22.widgets:WIDGET_HELP_PATH',)
}

KEYWORDS = (
    "orange3 add-on",
    "orange3-b22"
    "B22",
    "spectroscopy",
    "infrared",
)

CLASSIFIERS = [
    'Development Status :: 1 - Planning',
    'Intended Audience :: Education',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Programming Language :: Python :: 3 :: Only'
]

NAMESPACE_PACKAGES = ["orangecontrib"]

TEST_SUITE = "orangecontrib.b22.tests.suite"




if __name__ == '__main__':

    include_documentation('doc/build/htmlhelp', 'help/orange3-b22')

    setup(
        name=NAME,
        version=VERSION,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        url=URL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type=LONG_DESCRIPTION_TYPE,
        license=LICENSE,
        python_requires=PYTHON_REQUIRES,
        packages=PACKAGES,
        package_data=PACKAGE_DATA,
        data_files=DATA_FILES,
        install_requires=INSTALL_REQUIRES,
        extras_require=EXTRAS_REQUIRE,
        entry_points=ENTRY_POINTS,
        keywords=KEYWORDS,
        classifiers=CLASSIFIERS,
        namespace_packages=NAMESPACE_PACKAGES,
        test_suite=TEST_SUITE,
        include_package_data=True,
        zip_safe=False,
    )
