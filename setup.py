
# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


import os.path

readme = ''
here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, 'README.rst')
if os.path.exists(readme_path):
    with open(readme_path, 'rb') as stream:
        readme = stream.read().decode('utf8')


setup(
    long_description=readme,
    name='xepmts',
    version='0.4.5',
    description='Python client for accessing the XENON experiment PMT data.',
    python_requires='>=3.6',
    project_urls={"documentation": "https://xepmts.readthedocs.io/", "homepage": "https://github.com/jmosbacher/xepmts"},
    author='Yossi Mosbacher',
    author_email='joe.mosbacher@gmail.com',
    license='MIT',
    classifiers=['Development Status :: 2 - Pre-Alpha', 'Intended Audience :: Developers', 'License :: OSI Approved :: MIT License', 'Natural Language :: English', 'Programming Language :: Python :: 3.7', 'Programming Language :: Python :: 3.8'],
    entry_points={"console_scripts": ["xepmts = xepmts.cli:main"]},
    packages=['xepmts', 'xepmts.api', 'xepmts.api.v1', 'xepmts.api.v2'],
    package_dir={"": "."},
    package_data={"xepmts.api": ["endpoint_templates/*.yml"], "xepmts.api.v2": ["endpoint_templates/*.yml"]},
    install_requires=['click', 'eve-jwt==0.*,>=0.1.3', 'eve-panel==0.*,>=0.3.7'],
    extras_require={"dev": ["bumpversion", "coverage", "flake8", "invoke", "isort", "nbsphinx", "numpydoc", "pylint", "pytest", "sphinx", "sphinx-material", "tox", "yapf"]},
)
