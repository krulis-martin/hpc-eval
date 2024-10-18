# from typing import override
from loguru import logger
import config.descriptors as cd
from helpers.serializable import Serializable


class Assignment(Serializable):
    def __init__(self, id: str | None = None, config: dict = {}):
        logger.trace(f'Assignment.__init__({config})')
        self.id = id


class Assignments:
    _config = cd.NamedList(cd.Dictionary({
        'builds': cd.NamedList(cd.Dictionary({
            'overlay': cd.String(None, 'Path to the directory with build files.').path(),
            'run': cd.List(cd.List(cd.String()).collapsible(), 'List of commands to execute for build.'),  # TODO slurm
        }), description='List of build specifications (a required build is referred from a test).'),
        'tests': cd.NamedList(cd.Dictionary({
            'build': cd.String(None, 'Reference to a build used for this test.'),
            'inputs': cd.List(cd.String().path(), description='List of files required for the test (like input data).'),
        }), description='List of tests to be executed.'),
        # cd.String('_users.json', 'Path to the JSON file where user records are stored.').path(),
    }))

    @staticmethod
    def get_config_schema():
        '''
        Return configuration descriptor for this component.
        '''
        return __class__._config

    def __init__(self, config: dict = {}):
        self.assignments = {}

    def __getitem__(self, id) -> Assignment | None:
        '''
        Safe access to assignments by ids. None is returned if no such assignment exists.
        '''
        return self.assignments.get(id)

    def __len__(self) -> int:
        return len(self.assignments)
