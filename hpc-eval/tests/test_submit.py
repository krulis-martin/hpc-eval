import os
import unittest
import zipfile
from components.solutions import Solutions
from commands.submit import Submit
from tests.command_tests import CommandTestsBase


class TestSubmitCommand(CommandTestsBase):
    def test_submit(self):
        self.add_dummy_users(2)
        files = {
            'solution.hpp': '#define N 42',
            'solution.cpp': '#include "solution.hpp";\nint main() { return N; }',
        }
        prep_dir = self.create_temp_dir(files)

        command = Submit()
        self.run_command(command, [
            '--external-id', 'sol1',
            '--user', '1',
            '--assignment', 'ass',
            prep_dir + '/solution.hpp',
            prep_dir + '/solution.cpp',
        ])

        solutions = Solutions({'file': f'{self.rootdir}/_solutions/solutions.json'})
        self.assertTrue(solutions.serialization_file_exists())
        solutions.load_json()
        self.assertEqual(len(solutions), 1)
        solution = solutions.get_by_external_id('sol1')
        self.assertIsNotNone(solution)
        self.assertIsNotNone(solution.dir)
        self.assertEqual(solution.external_id, 'sol1')
        self.assertEqual(solution.assignment_id, 'ass')
        self.assertEqual(solution.user_id, '1')

        for name, content in files.items():
            path = f'{self.rootdir}/_solutions/ass/1/{solution.get_dir()}/{name}'
            self.assertTrue(os.path.exists(path))
            self.assertEqual(self.get_file_contents(path), content)

    def test_submit_with_subdirs(self):
        self.add_dummy_users(2)
        files = {
            'include/solution.hpp': '#define N 42',
            'src/solution.cpp': '#include "solution.hpp";\nint main() { return N; }',
            'src/submodule/sub.cpp': 'void foo() { printf("foo"); }',
        }
        prep_dir = self.create_temp_dir(files)

        command = Submit()
        self.run_command(command, [
            '--external-id', 'sol1',
            '--user', '1',
            '--assignment', 'ass',
            prep_dir + '/include',
            prep_dir + '/src',
        ])

        solutions = Solutions({'file': f'{self.rootdir}/_solutions/solutions.json'})
        self.assertTrue(solutions.serialization_file_exists())
        solutions.load_json()
        self.assertEqual(len(solutions), 1)
        solution = solutions.get_by_external_id('sol1')
        self.assertIsNotNone(solution)
        self.assertIsNotNone(solution.dir)
        self.assertEqual(solution.external_id, 'sol1')
        self.assertEqual(solution.assignment_id, 'ass')
        self.assertEqual(solution.user_id, '1')

        for name, content in files.items():
            path = f'{self.rootdir}/_solutions/ass/1/{solution.get_dir()}/{name}'
            self.assertTrue(os.path.exists(path))
            self.assertEqual(self.get_file_contents(path), content)

    def test_two_submits(self):
        self.add_dummy_users(2)
        files = {
            'hello1.py': 'print("Hello")',
            'hello2.py': 'print("Hello world")',
        }
        prep_dir = self.create_temp_dir(files)

        command1 = Submit()
        self.run_command(command1, [
            '--external-id', 'sol1',
            '--user', '1',
            '--assignment', 'ass',
            prep_dir + '/hello1.py',
        ])

        command2 = Submit()
        self.run_command(command2, [
            '--external-id', 'sol2',
            '--user', '1',
            '--assignment', 'ass',
            prep_dir + '/hello2.py',
        ])

        solutions = Solutions({'file': f'{self.rootdir}/_solutions/solutions.json'})
        self.assertTrue(solutions.serialization_file_exists())
        solutions.load_json()
        self.assertEqual(len(solutions), 2)

        solution1 = solutions.get_by_external_id('sol1')
        self.assertIsNotNone(solution1)
        self.assertIsNotNone(solution1.dir)
        self.assertEqual(solution1.external_id, 'sol1')
        self.assertEqual(solution1.assignment_id, 'ass')
        self.assertEqual(solution1.user_id, '1')
        self.assertTrue(f'{self.rootdir}/_solutions/ass/1/{solution1.get_dir()}/hello1.py')
        self.assertEqual(self.get_file_contents(
            f'{self.rootdir}/_solutions/ass/1/{solution1.get_dir()}/hello1.py'), files['hello1.py'])

        solution2 = solutions.get_by_external_id('sol2')
        self.assertIsNotNone(solution2)
        self.assertIsNotNone(solution2.dir)
        self.assertNotEqual(solution1.get_dir(), solution2.get_dir())
        self.assertEqual(solution2.external_id, 'sol2')
        self.assertEqual(solution2.assignment_id, 'ass')
        self.assertEqual(solution2.user_id, '1')
        self.assertTrue(f'{self.rootdir}/_solutions/ass/1/{solution2.get_dir()}/hello2.py')
        self.assertEqual(self.get_file_contents(
            f'{self.rootdir}/_solutions/ass/1/{solution2.get_dir()}/hello2.py'), files['hello2.py'])

    def test_zip_submit(self):
        self.add_dummy_users(2)
        files = {
            'solution.hpp': '#define N 42',
            'solution.cpp': '#include "solution.hpp";\nint main() { return N; }',
        }
        prep_dir = self.create_temp_dir(files)
        with zipfile.ZipFile(prep_dir + '/submit.zip', 'w') as z:
            for file in files:
                z.write(f'{prep_dir}/{file}', file)

        command = Submit()
        self.run_command(command, [
            '--external-id', 'sol1',
            '--user', '1',
            '--assignment', 'ass',
            '--extract',
            prep_dir + '/submit.zip',
        ])

        solutions = Solutions({'file': f'{self.rootdir}/_solutions/solutions.json'})
        self.assertTrue(solutions.serialization_file_exists())
        solutions.load_json()
        self.assertEqual(len(solutions), 1)
        solution = solutions.get_by_external_id('sol1')
        self.assertIsNotNone(solution)
        self.assertIsNotNone(solution.dir)
        self.assertEqual(solution.external_id, 'sol1')
        self.assertEqual(solution.assignment_id, 'ass')
        self.assertEqual(solution.user_id, '1')

        for name, content in files.items():
            path = f'{self.rootdir}/_solutions/ass/1/{solution.get_dir()}/{name}'
            self.assertTrue(os.path.exists(path))
            self.assertEqual(self.get_file_contents(path), content)


if __name__ == '__main__':
    unittest.main()
