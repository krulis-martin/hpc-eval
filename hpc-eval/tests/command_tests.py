import unittest
import os
import tempfile
from ruamel.yaml import YAML
from commands.base import BaseCommand
from components.users import Users, User


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

    def add_user(self, id: str | None, external_id: str | None, first_name: str, last_name: str, email: str) -> None:
        '''
        Helper method that adds a single user providing all the data as args.
        '''
        users = Users({'file': f'{self.rootdir}/_users.json'})
        if users.serialization_file_exists():
            users.load_json(keep_open=True, exclusive=True)
        users.add_user(User(id, external_id=external_id, first_name=first_name,
                       last_name=last_name, email=email))
        users.save_json()

    def add_users(self, user_list: list[User]) -> None:
        '''
        Helper method that adds a list of users.
        '''
        users = Users({'file': f'{self.rootdir}/_users.json'})
        if users.serialization_file_exists():
            users.load_json(keep_open=True, exclusive=True)
        for user in user_list:
            users.add_user(user)
        users.save_json()

    def add_dummy_users(self, count: int) -> list[User]:
        '''
        A more convenient helper that adds given number of dummy users.
        Also returns the list of User objects that were just created.
        '''
        users = []
        for i in range(1, count+1):
            users.append(User(str(i), external_id=f'ext{i}', first_name=f'Name{i}',
                              last_name=f'Surname{i}', email=f'email{i}@test.domain'))
        self.add_users(users)
        return users

    def run_command(self, command: BaseCommand, args: list):
        '''
        Simulate what happens in main, providing custom commandline args.
        '''
        command.parse_args(args)
        command.load_config()
        command.load_state()
        command.execute()
        command.save_state()
