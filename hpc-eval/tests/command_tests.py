import unittest
import os
import tempfile
from ruamel.yaml import YAML
from commands.base import BaseCommand


class CommandTestsBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.rootdir = self.tempdir.name
        self.config_file = self.rootdir + '/config.yaml'
        with open(self.config_file, 'w') as fp:
            yaml = YAML()
            yaml.dump({
                'logger': [{
                    'sink': '/dev/null',
                    'level': 'ERROR',
                }]
            }, fp)
        os.chdir(self.rootdir)

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        return super().tearDown()

    def run_command(self, command: BaseCommand, args: list):
        '''
        Simulate what happens in main, providing custom commandline args.
        '''
        command.parse_args(args)
        command.load_config()
        command.load_state()
        command.execute()
        command.save_state()
