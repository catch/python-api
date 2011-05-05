# Copyright 2011 Catch.com, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from setuptools import setup

__version__ = "0.5"
setup(install_requires=('simplejson',),
      include_package_data=True,
      name='py-catchapi',
      version=__version__,
      author="Ariel Backenroth",
      author_email="ariel@catch.com",
      description='A python wrapper around the Catch API',
      license='Apache License',
      url='http://github.com/catch/python-api',
      keywords='catch snaptic api',
      test_suite="test_catchapi",
      packages=('catchapi',),
      classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
      ])

