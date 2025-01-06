import os
from setuptools import setup, find_packages


CONFIGURATION_DIRECTORY = 'configuration'
SOURCE_DIRECTORY = 'cdk'
TEST_DIRECTORY = 'tests'

data_files = []
for root, dirs, files in os.walk(CONFIGURATION_DIRECTORY):
    data_files.append((os.path.relpath(root, CONFIGURATION_DIRECTORY),
                       [os.path.join(root, f) for f in files]))


setup(
    name='bedrock-pac',
    version='0.0.1',
    # declare your packages
    packages=find_packages(
        where=SOURCE_DIRECTORY,
        exclude=(TEST_DIRECTORY,)
    ),
    package_dir={"": SOURCE_DIRECTORY},

    # include data_files
    data_files=data_files,

    # setup the shebang
    # options={
    #     'test_integ': {
    #         'use_test_runtime_env': True,
    #         'test_args': [f'{TEST_DIRECTORY}/', '-v', '--cov-farm=setup.cfg'],
    #         'update_py_modification_times': True,
    #         'requires_build': True,
    #     },
    # },
    test_command=f"pytest {TEST_DIRECTORY}/ -v --cov-config=setup.cfg"

    # Enable build-time format checking
    # check_format=True,

    # Enable linting at build time
    # test_flake8=True,
)
