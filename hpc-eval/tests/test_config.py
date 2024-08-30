import unittest
import os
import config.descriptors as cd


class TestConfig(unittest.TestCase):

    def test_simple_struct_ok(self):
        descs = cd.Dictionary({
            "foo": cd.String(''),
            "bar": cd.Integer(42),
            "spam": cd.Bool(),
            "eggs": cd.List(cd.String())
        })
        input = {
            "foo": "fofo",
            "bar": 1,
            "spam": True,
            "eggs": ["egg"]
        }
        errors = []
        self.assertTrue(descs.validate(input, '', errors))
        self.assertEqual(len(errors), 0)
        loaded = descs.load(input, '')
        self.assertDictEqual(loaded, input)

    def test_simple_struct_fail(self):
        descs = cd.Dictionary({
            "foo": cd.String(''),
            "bar": cd.Integer(42),
            "spam": cd.Bool(),
            "eggs": cd.List(cd.String())
        })
        input = {
            "foo": 42,
            "bar": "1",
            "spam": 1,
            "boiled": "eggs",
        }
        errors = []
        self.assertFalse(descs.validate(input, 'file.yaml', errors))
        self.assertEqual(len(errors), 4)
        for error in errors:
            self.assertIsInstance(error, cd.ValidationError)
        self.assertEqual(str(errors[0]), "'foo' (in 'file.yaml'): String value expected, int given.")
        self.assertEqual(str(errors[1]), "'bar' (in 'file.yaml'): Integer value expected, str given.")
        self.assertEqual(str(errors[2]), "'spam' (in 'file.yaml'): Bool value expected, int given.")
        self.assertEqual(str(errors[3]), "<root> (in 'file.yaml'): Unexpected dict key 'boiled'.")

    def test_nested_struct_ok(self):
        descs = cd.Dictionary({
            "foo": cd.Dictionary({
                "bar": cd.List(cd.Dictionary({
                    "spam": cd.String('')
                }))
            })
        })
        input = {
            "foo": {
                "bar": [
                    {"spam": "a"},
                    {"spam": "b"},
                ]
            }
        }
        errors = []
        self.assertTrue(descs.validate(input, '', errors))
        self.assertEqual(len(errors), 0)
        loaded = descs.load(input, '')
        self.assertDictEqual(loaded, input)

    def test_nested_struct_fail(self):
        descs = cd.Dictionary({
            "foo": cd.Dictionary({
                "bar": cd.List(cd.Dictionary({
                    "spam": cd.String('')
                }))
            })
        })
        input = {
            "foo": {
                "bar": {
                    "spam": "a",
                },
            }
        }
        errors = []
        self.assertFalse(descs.validate(input, 'file.yaml', errors))
        self.assertEqual(len(errors), 1)
        self.assertEqual(str(errors[0]), "'foo.bar' (in 'file.yaml'): Value '{'spam': 'a'}' is not a list.")

        input = {
            "foo": {
                "bar": [
                    {"spam": "a"},
                    {"spam": 42},
                ]
            }
        }
        errors = []
        self.assertFalse(descs.validate(input, 'file.yaml', errors))
        self.assertEqual(len(errors), 1)
        self.assertEqual(str(errors[0]), "'foo.bar[1].spam' (in 'file.yaml'): String value expected, int given.")

    def test_string_enum_ok(self):
        descs = cd.String('').enum(['ERROR', 'INFO', 'DEBUG'])
        errors = []
        self.assertTrue(descs.validate('ERROR', '', errors))
        self.assertTrue(descs.validate('INFO', '', errors))
        self.assertTrue(descs.validate('DEBUG', '', errors))
        self.assertEqual(len(errors), 0)

    def test_string_enum_fail(self):
        descs = cd.String('').enum(['ERROR', 'INFO', 'DEBUG'])
        descs.name = 'arg'
        errors = []
        self.assertFalse(descs.validate('FOO', 'file1.yaml', errors))
        self.assertFalse(descs.validate('BAR', 'file2.yaml', errors))
        self.assertFalse(descs.validate('SPAM', 'file3.yaml', errors))
        self.assertEqual(len(errors), 3)
        self.assertEqual(errors[0].full_name, 'arg')
        self.assertEqual(errors[1].full_name, 'arg')
        self.assertEqual(errors[2].full_name, 'arg')
        self.assertEqual(errors[0].source, 'file1.yaml')
        self.assertEqual(errors[1].source, 'file2.yaml')
        self.assertEqual(errors[2].source, 'file3.yaml')
        self.assertEqual(str(errors[0]), "'arg' (in 'file1.yaml'): Value FOO is not in enum [ERROR, INFO, DEBUG]")
        self.assertEqual(str(errors[1]), "'arg' (in 'file2.yaml'): Value BAR is not in enum [ERROR, INFO, DEBUG]")
        self.assertEqual(str(errors[2]), "'arg' (in 'file3.yaml'): Value SPAM is not in enum [ERROR, INFO, DEBUG]")

    def test_path_ok(self):
        descs = cd.String().path()
        res = descs.load('./../jobs', '/opt/hpc-eval/config.yaml')
        self.assertEqual(res, os.path.normpath('/opt/jobs'))


if __name__ == '__main__':
    unittest.main()
