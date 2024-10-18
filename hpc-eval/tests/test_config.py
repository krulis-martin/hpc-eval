import unittest
import pyfakefs.fake_filesystem_unittest as unittest_fs
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

    def test_simple_defaults(self):
        descs = cd.Dictionary({
            "foo": cd.String('abc'),
            "bar": cd.Integer(42),
            "spam": cd.Bool(),
            "eggs": cd.List(cd.String())
        })
        input = {}
        errors = []
        self.assertTrue(descs.validate(input, '', errors))
        self.assertEqual(len(errors), 0)
        loaded = descs.load(input, '')
        self.assertDictEqual(loaded, {
            "foo": "abc",
            "bar": 42,
            "spam": False,
            "eggs": [],
        })

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

    def test_collapsible_list_ok(self):
        descs = cd.Dictionary({"foo": cd.List(cd.Integer()).collapsible()})
        errors = []
        self.assertTrue(descs.validate({"foo": []}, '', errors))
        self.assertTrue(descs.validate({"foo": [1, 2, 3]}, '', errors))
        self.assertTrue(descs.validate({"foo": 42}, '', errors))
        self.assertEqual(len(errors), 0)
        loaded = descs.load({"foo": [1, 2, 3]}, '')
        self.assertEqual(loaded["foo"], [1, 2, 3])
        loaded = descs.load({"foo": 42}, '')
        self.assertEqual(loaded["foo"], [42])

    def test_named_list_ok(self):
        descs = cd.NamedList(cd.Integer())
        input = {
            "foo": 1,
            "bar": 2,
            "spam": 42,
        }
        errors = []
        self.assertTrue(descs.validate(input, '', errors))
        self.assertEqual(len(errors), 0)
        loaded = descs.load(input, '')
        self.assertDictEqual(loaded, input)

    def test_named_list_fail(self):
        descs = cd.NamedList(cd.Integer())
        input = {
            "foo": 1,
            "bar": 2,
            "spam": 'str',
        }
        errors = []
        self.assertFalse(descs.validate(input, 'file.yaml', errors))
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].full_name, 'spam')
        self.assertEqual(str(errors[0]), "'spam' (in 'file.yaml'): Integer value expected, str given.")


class TestConfigWithFs(unittest_fs.TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.fs.create_dir('/test')

    def fix_dirs(self, dirs):
        return [os.path.normpath(d) for d in dirs]

    def test_glob_ok(self):
        self.fs.create_dir('/test/sub')
        self.fs.create_file('/test/a.yaml')
        self.fs.create_file('/test/b.yaml')
        self.fs.create_file('/test/c.txt')
        self.fs.create_file('/test/sub/a.yaml')
        desc = cd.String().glob()
        patterns = {
            '*.yaml': self.fix_dirs(['/test/a.yaml', '/test/b.yaml']),
            './*.yaml': self.fix_dirs(['/test/a.yaml', '/test/b.yaml']),
            '/test/*.yaml': self.fix_dirs(['/test/a.yaml', '/test/b.yaml']),
            '**/*.yaml': self.fix_dirs(['/test/a.yaml', '/test/b.yaml', '/test/sub/a.yaml']),
            '/**/*.yaml': self.fix_dirs(['/test/a.yaml', '/test/b.yaml', '/test/sub/a.yaml']),
            '**/../*.yaml': self.fix_dirs(['/test/a.yaml', '/test/b.yaml']),
            './*/*.yaml': self.fix_dirs(['/test/sub/a.yaml']),
            '*.txt': self.fix_dirs(['/test/c.txt']),
            '/**/*.md': self.fix_dirs([]),
        }

        for p in patterns:
            errors = []
            self.assertTrue(desc.validate(p, '/test/a.yaml', errors))
            self.assertEqual(errors, [])

        for p, correct in patterns.items():
            res = desc.load(p, '/test/a.yaml')
            self.assertIs(type(res), list)
            self.assertListEqual(res, correct)

    def test_path(self):
        desc = cd.String().path()
        res = desc.load('.hidden.file', '/test/config.yaml')
        self.assertEqual(res, '/test/.hidden.file')
        res = desc.load('.hidden.file', '/test/sub/config.yaml')
        self.assertEqual(res, '/test/sub/.hidden.file')
        res = desc.load('./sub/.hidden.file', '/test/config.yaml')
        self.assertEqual(res, '/test/sub/.hidden.file')


if __name__ == '__main__':
    unittest.main()
