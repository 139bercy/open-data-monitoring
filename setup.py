#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = ['Click>=6.0', ]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Paul Moysan",
    author_email='tongyeouki@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    description="Description here",
    entry_points={
        'console_scripts': [
            'app=interfaces.cli:cli'
        ],
    },
    install_requires=requirements,
    long_description=readme,
    include_package_data=True,
    platforms='any',
    keywords='',
    name='open-data-monitoring',
    packages=find_packages("src"),
    package_dir={"": "src"},
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='',
    version='0.0.1',
    zip_safe=False,
)
