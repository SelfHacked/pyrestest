#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


from pyrestest import __version__ as VERSION


if sys.argv[-1] == 'publish':
    try:
        import wheel
        print('Wheel version: ', wheel.__version__)
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print('Tagging the version on git:')
    os.system("git tag -a %s -m 'version %s'" % (VERSION, VERSION))
    os.system('git push --tags')
    sys.exit()

readme = open('README.rst').read()

install_requirements = [
    'pytest-django',
    'djangorestframework',
]

setup(
    name='pyrestest',
    version=VERSION,
    description="""A lightweight test library to test REST API.""",  # noqa
    long_description=readme,
    author='Varuna Bamunusinghe',
    author_email='varuna@selfdecode.com',
    url='https://github.com/SelfHacked/pyrestest',
    packages=['pyrestest'],
    include_package_data=True,
    install_requires=install_requirements,
    license='MIT',
    zip_safe=False,
    keywords='pyrestest',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
