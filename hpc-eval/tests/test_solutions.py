import unittest
import tempfile
from components.solutions import Solutions, Solution


class TestSolutions(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmpfile = self.tmpdir.name + '/solutions.json'

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        return super().tearDown()

    def create_solutions(self, count=0):
        solutions = Solutions({'file': self.tmpfile})
        for i in range(1, count+1):
            solutions.add_solution(Solution(str(i), external_id=f'eid{i}', user_id=f'u{i}', assignment_id=f'a{i}'))
        solutions.save_json()

    def same_solutions(self, s1, s2) -> bool:
        self.assertIsInstance(s1, Solution)
        self.assertIsInstance(s2, Solution)
        for k in s1.__dict__:
            self.assertEqual(s1.__dict__[k], s2.__dict__[k])

    def test_create(self):
        solutions = Solutions({'file': self.tmpfile})
        self.assertFalse(solutions.serialization_file_exists())
        solutions.add_solution(Solution('42', external_id='forty-two', user_id='u1', assignment_id='a1'))
        self.assertEqual(len(solutions), 1)
        self.assertEqual(solutions['42'].external_id, 'forty-two')
        solutions.save_json()
        self.assertTrue(solutions.serialization_file_exists())

        solutions2 = Solutions({'file': self.tmpfile})
        self.assertTrue(solutions2.serialization_file_exists())
        solutions2.load_json()
        self.assertEqual(len(solutions), len(solutions2))
        self.same_solutions(solutions['42'], solutions2['42'])

    def test_add_empty(self):
        self.create_solutions()
        solutions = Solutions({'file': self.tmpfile})
        self.assertTrue(solutions.serialization_file_exists())
        id = solutions.add_solution(Solution(None, user_id='u1', assignment_id='a1'))
        solutions.save_json()

        solutions2 = Solutions({'file': self.tmpfile})
        solutions2.load_json()
        self.assertEqual(len(solutions2), 1)
        self.same_solutions(solutions[id], solutions2[id])

    def test_add_nonempty(self):
        self.create_solutions(2)
        solutions = Solutions({'file': self.tmpfile})
        solutions.load_json(keep_open=True, exclusive=True)
        id = solutions.add_solution(Solution(None, user_id='u1', assignment_id='a1'))
        self.assertEqual(id, '3')
        solutions.save_json()

        solutions2 = Solutions({'file': self.tmpfile})
        solutions2.load_json()
        self.assertEqual(len(solutions2), 3)
        self.same_solutions(solutions[id], solutions2[id])

    def test_remove(self):
        self.create_solutions(3)
        solutions = Solutions({'file': self.tmpfile})
        solutions.load_json(keep_open=True, exclusive=True)
        rs = solutions.remove_solution('2')
        self.assertEqual(len(solutions), 2)
        self.assertEqual(rs.id, '2')
        solutions.save_json()

        solutions2 = Solutions({'file': self.tmpfile})
        solutions2.load_json()
        self.assertEqual(len(solutions2), 2)
        self.assertIsNotNone(solutions2['1'])
        self.assertIsNone(solutions2['2'])
        self.assertIsNotNone(solutions2['3'])


if __name__ == '__main__':
    unittest.main()
