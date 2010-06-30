# Copyright (c) 2010 Harry Tormey <harry@snaptic.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


'''The setup and build script for the python-snaptic library.'''

__author__ = 'harry@snaptic.com'
__version__ = '0.4'


METADATA = dict(
  name = "py-snaptic",
  version = __version__,
  py_modules = ['snaptic'],
  author='Harry Tormey',
  author_email='harry@snaptic.com',
  description='A python wrapper around the Snaptic API',
  license=' MIT License',
  url='http://github.com/snaptic/python-api',
  keywords='snaptic api',
)

# Extra package metadata to be used only if setuptools is installed
SETUPTOOLS_METADATA = dict(
  install_requires = ['setuptools', 'simplejson'],
  include_package_data = True,
  classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Internet',
  ],
)

def Main():

  # Use setuptools if available, otherwise fallback and use distutils
  try:
    import setuptools
    METADATA.update(SETUPTOOLS_METADATA)
    setuptools.setup(**METADATA)
  except ImportError:
    import distutils.core
    distutils.core.setup(**METADATA)


if __name__ == '__main__':
  Main()


