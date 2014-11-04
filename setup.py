#!/usr/bin/env python3

from unittest import TextTestRunner, TestLoader
from glob import glob
from os.path import splitext, basename, join as pjoin
import os
from distutils.core import setup, Command

# thanks: http://da44en.wordpress.com/2002/11/22/using-distutils/
class TestCommand(Command):
    description=u'run unit tests'
    user_options = [ ]

    def initialize_options(self):
        self._dir = os.getcwdu()

    def finalize_options(self):
        pass

    def run(self):
        u'''
        Finds all the tests modules in tests/, and runs them.
        '''
        testfiles = [ ]
        for t in glob(pjoin(self._dir, u'tests', u'*.py')):
            if not t.endswith(u'__init__.py'):
                testfiles.append(u'.'.join(
                    [u'tests', splitext(basename(t))[0]])
                )

        tests = TestLoader().loadTestsFromNames(testfiles)
        t = TextTestRunner(verbosity = 1)
        t.run(tests)

setup(
    name=u'pyDelphin',
    version=u'0.2',
    url=u'https://github.com/goodmami/pydelphin',
    author=u'Michael Wayne Goodman',
    author_email=u'goodman.m.w@gmail.com',
    description=u'Libraries and scripts for DELPH-IN data.',
    packages=[u'delphin'],
    cmdclass={u'test':TestCommand},
    install_requires=[
        u'networkx',
    ]
)
