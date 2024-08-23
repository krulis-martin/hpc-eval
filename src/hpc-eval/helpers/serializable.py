import types
import json


def _serialize(value, name: str):
    '''
    Helper function that helps with recursive serialization of basic types.
    '''
    if type(value) in (int, float, bool, str, types.NoneType):
        return value  # basic scalar value, nothing to do

    # lists, dicts, and serializable objects are serialized recursively
    elif type(value) is list:
        return [_serialize(v, f"{name}[{i}]") for i, v in enumerate(value)]
    elif type(value) is dict:
        return {k: _serialize(v, f"{name}.{k}") for k, v in value.items()}
    elif issubclass(Serializable, value):
        return value.serialize()

    # unknown type, nothing we can do...
    else:
        raise Exception(
            f"Property {name} has unserializable type {type(value)}.")


class Serializable:
    '''
    An interface for (de)serialization into JSON or similar structured format.
    '''

    def __init__(self, file: str | None = None):
        self._serialization_file = file

    def serialize(self) -> dict:
        '''
        Generate a basic type structure that is directly serializable by json
        or a similar library (yaml, ...).
        '''
        res = {}
        for name, value in self.__dict__.items():
            res[name] = _serialize(value, name)

        return res

    def deserialize(self, data: dict) -> None:
        '''
        Fill in internal properties from a deserialization structure.
        '''
        for key, value in data.items():
            if key not in self.__dict__:
                continue

            if issubclass(Serializable, type(self[key])):
                pass

            if type(self[key]) in (int, float, bool, str):
                if type(self[key]) is not type(value):
                    raise Exception(
                        f"Deserialization type mismatch. Property {key} is \
                            expected to be {type(self[key])} but \
                            {type(value)} type given.")

                self[key] = value

    def set_serialization_file(self, file: str) -> None:
        '''
        Set a file associated with this object so the user may more
        conveniently use save/load functions without specifying the
        file over and over again.
        '''
        self._serialization_file = file

    def save_json(self, file: str | None = None) -> None:
        '''
        Simplifies direct serialization into a JSON file.
        '''
        if file is None:
            if self._serialization_file is None:
                raise Exception("Path to a json file must be specified.")
            file = self._serialization_file

        data = self.serialize()
        with open(file, 'w') as fp:
            json.dump(data, fp)
        self._serialization_file = file

    def load_json(self, file: str | None = None) -> None:
        '''
        Simplifies direct loading from a JSON file.
        '''
        if file is None:
            if self._serialization_file is None:
                raise Exception("Path to a json file must be specified.")
            file = self._serialization_file

        with open(file, 'r') as fp:
            data = json.load(fp)
            self.deserialize(data)
        self._serialization_file = file
