import unittest
import tempfile
from components.users import Users, User
from commands.add_user import AddUser
from tests.command_tests import CommandTestsBase


class TestUsers(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmpfile = self.tmpdir.name + '/users.json'

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        return super().tearDown()

    def create_users(self, count=0):
        users = Users({'file': self.tmpfile})
        for i in range(1, count+1):
            users.add_user(User(str(i), external_id=f'eid{i}', first_name='John',
                                last_name=f'Doe{i}', email=f'john.doe{i}@email.domain'))
        users.save_json()

    def test_create(self):
        users = Users({'file': self.tmpfile})
        self.assertFalse(users.serialization_file_exists())
        users.add_user(User('42', external_id='forty-two', first_name='John',
                       last_name='doe', email='john.doe@email.domain'))
        self.assertEqual(len(users), 1)
        self.assertEqual(users['42'].email, 'john.doe@email.domain')
        users.save_json()
        self.assertTrue(users.serialization_file_exists())

        users2 = Users({'file': self.tmpfile})
        self.assertTrue(users2.serialization_file_exists())
        users2.load_json()
        self.assertEqual(len(users), len(users2))
        self.assertEqual(users['42'], users2['42'])

    def test_add_empty(self):
        self.create_users()
        users = Users({'file': self.tmpfile})
        self.assertTrue(users.serialization_file_exists())
        id = users.add_user(User(None, first_name='John', last_name='Doe', email='john.doe@email.domain'))
        users.save_json()

        users2 = Users({'file': self.tmpfile})
        users2.load_json()
        self.assertEqual(len(users2), 1)
        self.assertEqual(users[id], users2[id])

    def test_add_nonempty(self):
        self.create_users(2)
        users = Users({'file': self.tmpfile})
        users.load_json(keep_open=True, exclusive=True)
        id = users.add_user(User(None, first_name='John', last_name='Doe', email='john.doe@email.domain'))
        self.assertEqual(id, '3')
        users.save_json()

        users2 = Users({'file': self.tmpfile})
        users2.load_json()
        self.assertEqual(len(users2), 3)
        self.assertEqual(users[id], users2[id])

    def test_update(self):
        self.create_users(3)
        new_data = {'external_id': 'foo', 'first_name': 'Jane', 'last_name': 'Smith'}

        users = Users({'file': self.tmpfile})
        users.load_json(keep_open=True, exclusive=True)
        users.update_user('2', **new_data)
        self.assertEqual(len(users), 3)
        users.save_json()

        users2 = Users({'file': self.tmpfile})
        users2.load_json()
        self.assertEqual(len(users2), 3)
        user = users['2']
        for k, v in new_data.items():
            self.assertEqual(user.__dict__[k], v)
        self.assertEqual(user.email, 'john.doe2@email.domain')

    def test_remove(self):
        self.create_users(3)
        users = Users({'file': self.tmpfile})
        users.load_json(keep_open=True, exclusive=True)
        users.remove_user('2')
        self.assertEqual(len(users), 2)
        users.save_json()

        users2 = Users({'file': self.tmpfile})
        users2.load_json()
        self.assertEqual(len(users2), 2)
        self.assertIsNotNone(users2['1'])
        self.assertIsNone(users2['2'])
        self.assertIsNotNone(users2['3'])


class TestAddUser(CommandTestsBase):
    def test_add_user(self):
        command = AddUser()
        self.run_command(command, [
            '--external-id', 'eid',
            '--first-name', 'Jane',
            '--last-name', 'Doe',
            '--email', 'jane.doe@email.domain'
        ])

        users = Users({'file': f'{self.rootdir}/_users.json'})
        self.assertTrue(users.serialization_file_exists())
        users.load_json()
        self.assertEqual(len(users), 1)
        user = users.get_by_external_id('eid')
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.email, 'jane.doe@email.domain')

    def test_update_user_by_id(self):
        self.add_dummy_users(3)
        command = AddUser()
        self.run_command(command, [
            '--update',
            '--id', '2',
            '--first-name', 'Jane',
            '--last-name', 'Doe',
            '--email', 'jane.doe@email.domain'
        ])

        users = Users({'file': f'{self.rootdir}/_users.json'})
        self.assertTrue(users.serialization_file_exists())
        users.load_json()
        self.assertEqual(len(users), 3)
        user = users['2']
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.email, 'jane.doe@email.domain')

    def test_update_user_by_external_id(self):
        self.add_dummy_users(3)
        command = AddUser()
        self.run_command(command, [
            '--update',
            '--external-id', 'ext1',
            '--first-name', 'Jane',
            '--last-name', 'Doe',
            '--email', 'jane.doe@email.domain'
        ])

        users = Users({'file': f'{self.rootdir}/_users.json'})
        self.assertTrue(users.serialization_file_exists())
        users.load_json()
        self.assertEqual(len(users), 3)
        user = users.get_by_external_id('ext1')
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.email, 'jane.doe@email.domain')

    def test_no_update(self):
        self.add_dummy_users(3)
        command = AddUser()
        self.run_command(command, [
            '--external-id', 'ext1',
            '--first-name', 'Jane',
            '--last-name', 'Doe',
            '--email', 'jane.doe@email.domain'
        ])

        users = Users({'file': f'{self.rootdir}/_users.json'})
        self.assertTrue(users.serialization_file_exists())
        users.load_json()
        self.assertEqual(len(users), 3)
        user = users.get_by_external_id('ext1')
        self.assertIsNotNone(user)
        self.assertNotEqual(user.first_name, 'Jane')
        self.assertNotEqual(user.last_name, 'Doe')
        self.assertNotEqual(user.email, 'jane.doe@email.domain')


if __name__ == '__main__':
    unittest.main()
