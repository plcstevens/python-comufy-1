import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
LICENSE = open(os.path.join(here, 'LICENSE.txt')).read()

requires = [
    ]

setup(
    name                  = 'pycomufy',
    version               = '1.1',
    description           = 'pycomufy',
    long_description      = README + '\n\n' +  CHANGES,
    classifiers           = [
                                'Development Status :: 5 - Production/Stable',
                                'Environment :: Web Environment',
                                'Intended Audience :: Developers',
                                'License :: OSI Approved :: BSD License',
                                'Programming Language :: Python',
                                'Programming Language :: Python :: 2.6',
                                'Programming Language :: Python :: 2.7',
                                'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
                                'Topic :: Internet :: WWW/HTTP :: Social Media',
                                'Topic :: Internet :: WWW/HTTP :: Facebook',
                                'Topic :: Internet :: WWW/HTTP :: Twitter',
                            ],
    author                = 'Philip Stevens, Tauri-Tec Ltd',
    author_email          = 'philip@tauri-tec.com',
    url                   = 'https://github.com/plcstevens/python-comufy/',
    license               = 'BSD',
    keywords              = 'web wsgi bfg pylons pyramid comufy facebook twitter heroku',
    packages              = find_packages(exclude = ['ez_setup', 'examples', 'tests']),
    include_package_data  = True,
    zip_safe              = False,
    test_suite            = 'pycomufy',
    install_requires      = requires,
    entry_points          = """\
                            """,
    )

