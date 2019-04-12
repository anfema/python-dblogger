import os
from setuptools import setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
        name='dblogger',
        version='1.0.0',
        description='Log handler for logging to PostgreSQL Databases (async and sync)',
        long_description='''
            This is a log handler created to write log records to a PostgresSQL database.
            It will automatically detect which version of the postgres database adapter is in
            use and adapt it's logging behaviour to use either psycopg2 for synchronous logging
            (which means the logger blocks until the transaction is in the DB) or it will use
            asyncpg to log asynchronously (a running runloop is required).
        ''',
        long_description_content_type='text/markdown',
        url='https://github.com/anfema/python-dblogger',
        author='Johannes Schriewer',
        author_email='hallo@dunkelstern.de',
        license='LICENSE.txt',
        include_package_data=True,
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Operating System :: OS Independent'
        ],
        keywords='postgresql psycopg2 asyncpg logger db',
        packages=['dblogger'],
        scripts=[
            'bin/create_schema.py',
        ],
        install_requires=[
        ],
        dependency_links=[
        ]
)
