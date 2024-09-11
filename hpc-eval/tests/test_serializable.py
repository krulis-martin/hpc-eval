import unittest
import json
import tempfile
from helpers.serializable import Serializable


class Data1(Serializable):
    def __init__(self, file=None, a=None):
        super().__init__(file)
        self.a = a

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.a == other.a


class Data2(Serializable):
    def __init__(self, file=None, a=None, b=None):
        super().__init__(file)
        self.a = a
        self.b = b

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.a == other.a and self.b == other.b


class Data3(Serializable):
    def __init__(self, file=None, a=None, b=None, c=None):
        super().__init__(file)
        self.a = a
        self.b = b
        self.c = c

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.a == other.a and self.b == other.b and self.c == other.c


class TestConfig(unittest.TestCase):

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmpfile = self.tmpdir.name + '/data.json'
        with open(self.tmpfile, 'w') as fp:
            json.dump({"data": 42}, fp)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        return super().tearDown()

    def test_serialization_scalars(self):
        data = Data3(self.tmpfile, 1, 'foo', True)
        self.assertTrue(data.serialization_file_exists())
        data.save_json()

        data2 = Data3(self.tmpfile)
        data2.load_json()
        self.assertEqual(data, data2)
        self.assertTrue(data.serialization_file_exists())

    def test_serialization_nested_structs(self):
        data = Data2(self.tmpfile, [[1, 2], ['a', 'b'], [True, [False]]], {
            "list1": [{"foo": 1, "bar": 2, "nestedlist": [1, 2, 3]}],
            "dict1": {
                "nestedlist2": ['a', 'b', None, 'c', {}],
                "flag": True,
                "nothing": None
            }
        })
        data.save_json()

        data2 = Data2(self.tmpfile)
        data2.load_json()
        self.assertEqual(data, data2)

    def test_serialization_classes(self):
        self.maxDiff = None
        data = Data2(self.tmpfile, [Data1(42), Data2('a', 54), {"data": Data1("str")}, [Data1(1)]], {
            "key1": Data2(Data1(42), Data1(54)),
            "list": [Data1(1), Data2('a', 'b')]
        })
        data.save_json()

        data2 = Data2(self.tmpfile)
        data2.load_json()
        self.assertEqual(data, data2)

    def test_serialization_nonexist(self):
        file = self.tmpdir.name + '/nonexist.json'
        data = Data1(file, 42)
        self.assertFalse(data.serialization_file_exists())
        data.save_json()
        self.assertTrue(data.serialization_file_exists())

        data2 = Data1(file)
        data2.load_json()
        self.assertEqual(data, data2)
