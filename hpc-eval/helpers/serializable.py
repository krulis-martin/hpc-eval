import types
import json
from helpers.file_lock import FileLock


def _serialize_list_item(value, full_path: str = ''):
    '''
    Serialization of list items is different since one cannot attach type to the key (like in dict).
    If the type (class name) needs to be recognized, a special structure { type, value } is created.
    The 'type' holds the type string and the 'value' is the original (serialized) list item value.
    '''
    (name, serialized) = _serialize('', value, full_path)
    if type(serialized) is dict:
        if not name:
            name = 'dict'
        else:
            name = name[1:]
        return {"type": name, "value": serialized}  # dicts and classes are wrapped in this struct
    else:
        return serialized


def _serialize(name: str, value, full_path: str = ''):
    '''
    Helper function that helps with recursive serialization of basic types.
    It encodes the class names (types) in dict keys by appending @module.classname.
    Values nested in lists are encoded differently, see _serialize_list_item().
    '''
    if type(value) in (int, float, bool, str, types.NoneType):
        return (name, value)  # basic scalar value, nothing to do

    # lists, dicts, and serializable objects are serialized recursively
    elif type(value) is list:
        return (name, [_serialize_list_item(v, f"{full_path}[{i}]") for i, v in enumerate(value)])
    elif type(value) is dict:
        prefix = f'{name}.' if name else ''
        return (name, dict([_serialize(k, v, f"{prefix}{k}") for k, v in value.items()]))
    elif isinstance(value, Serializable):
        serialized = value.serialize(full_path)
        value_type = type(value)
        return (f'{name}@{value_type.__module__}.{value_type.__name__}', serialized)

    # unknown type, nothing we can do...
    else:
        raise Exception(
            f"Property {full_path} has unserializable type {type(value).__name__}.")


def _class_instance(class_name: str):
    '''
    Helper for dynamic class instantiation. Full class name (module.submodule.class) string is expected.
    The constructor of the class must work without any parameters.
    '''
    # parse type
    class_tokens = class_name.split('.')
    class_name = class_tokens.pop(-1)
    module_name = '.'.join(class_tokens)

    # create class instance
    module = __import__(module_name, fromlist=[None])
    cls = getattr(module, class_name)
    return cls()


def _deserialize_list_item(value):
    '''
    Deserialzation of list items. When dict is encountered, it is suspected to be a special structure that
    encodes type of a value. Remaining values are decoded using _deserialize().
    '''
    if type(value) is dict and len(value) == 2 and 'type' in value and 'value' in value:
        type_str = value['type']
        value = _deserialize('', value['value'])[1]
        if type_str == 'dict':
            return value
        else:
            instance = _class_instance(type_str)
            instance.deserialize(value)
            return instance

    else:
        return _deserialize('', value)[1]


def _deserialize(name, value):
    '''
    Deserialization routing processes value (under given key/name).
    Name may hold encoded data type (class) of the value. In such case, the corresponding class is constructed.
    (name, value) pair is returned (since name may have been stripped of the piggybacked type).
    '''
    name_tokens = name.split('@')
    name = name_tokens.pop(0)
    class_name = name_tokens.pop(0) if len(name_tokens) > 0 else None

    if class_name is not None:
        instance = _class_instance(class_name)
        instance.deserialize(value)
        return (name, instance)

    elif type(value) is list:
        value = [_deserialize_list_item(v) for v in value]
    elif type(value) is dict:
        value = dict([_deserialize(k, v) for k, v in value.items()])

    return (name, value)


class Serializable:
    '''
    An interface for (de)serialization into JSON or similar structured format.
    Limitations:
    - Constructor must work without arguments (so empty instances can be easily created).
    - Properties not starting with _ are serialized automatically.
    - (Nested) properties must be basic types (scalar, list, dict), or Serializable instances.
    If the default behavior needs to be changed, descendant class should override serialize() and deserialize().
    Remaining methods (except for constructor) should not be overriden.
    '''

    def __init__(self, file: str | None = None, lock_timeout: int = 10):
        '''
        The file holds the path to the serialization file used for load/save operations.
        The lock timeout is used for locking operations of the serialization file.
        '''
        self._serialization_file = FileLock(file) if file else None
        self._lock_timeout = lock_timeout

    def serialize(self, full_path: str = '') -> dict:
        '''
        Generate a basic type structure that is directly serializable by json
        or a similar library (yaml, ...).
        '''
        data = {name: value for name, value in self.__dict__.items() if not name.startswith('_')}
        return _serialize('', data, full_path)[1]  # [1] = only the value

    def deserialize(self, data: dict) -> None:
        '''
        Fill in internal properties from a deserialization structure.
        '''
        for key, serialized in data.items():
            (name, value) = _deserialize(key, serialized)
            if name not in self.__dict__:
                continue

            if self.__dict__[name] is not None and type(self.__dict__[name]) is not type(value):
                raise Exception(f"Deserialization type mismatch. Property {name} is expected to be \
                                {type(self.__dict__[name]).__name__} but {type(value).__name__} type given.")

            self.__dict__[name] = value

    def set_serialization_file(self, file: str, open=False, exclusive=False) -> None:
        '''
        Set a file associated with this object so the user may more conveniently call save/load functions without
        specifying the file over and over again. Optionally, the file can be opened (and locked).
        Exclusive mode indicates opening for writing (so it can be later saved).
        '''
        if self._serialization_file is not None:
            if self._serialization_file.get_file_name() == file and self._serialization_file.is_open() == open and (
                    not open or self._serialization_file.is_exclusive() == exclusive):
                return  # already set and in the right state
            self._serialization_file.close()

        self._serialization_file = FileLock(file)
        if open:
            if not self._serialization_file.open(exclusive=exclusive, timeout=self._lock_timeout):
                raise RuntimeError(f"Unable to acquire a lock for file '{file}'.")

    def open_serialization_file(self, exclusive=False, soft=False) -> bool:
        '''
        Open and lock the serialization file. If the file is already locked in the right mode, nothing happens.
        Exclusive mode indicates opening for writing (so it can be later saved).
        The soft mode will report failures as False return value, otherwise an error is risen.
        '''
        if self._serialization_file is None:
            raise RuntimeError("No serialization file was specified.")
        else:
            if self._serialization_file.get_fp() is not None and self._serialization_file.is_exclusive() == exclusive:
                return True
            self._serialization_file.close()

        if not self._serialization_file.open(exclusive=exclusive, timeout=self._lock_timeout):
            if soft:
                return False  # soft failure is reported by return value
            else:
                raise RuntimeError(f"Unable to acquire a lock for file '{self._serialization_file.get_file_name()}'.")

    def close_serialization_file(self) -> bool:
        '''
        Close the serialization file and release the lock.
        False is returned if the file was already closed.
        '''
        if self._serialization_file is None:
            raise RuntimeError("No serialization file was specified.")
        return self._serialization_file.close()

    def serialization_file_exists(self) -> bool:
        if self._serialization_file is None:
            raise RuntimeError("No serialization file was specified.")
        return self._serialization_file.exists()

    def load_json(self, file: str | None = None, keep_open=False, exclusive=False) -> None:
        '''
        Simplifies direct loading from a JSON file.
        Keep open flag indicates the serialization file is kept open (and locked) after loading.
        Exclusive flag means the file is open in read-write mode with exclusive lock (so it can be saved later).
        '''
        if file is not None:
            self.set_serialization_file(file, open=True, exclusive=exclusive)
        else:
            if self._serialization_file is None:
                raise Exception("Path to a serialization file must be specified.")
            self.open_serialization_file(exclusive=exclusive)

        self._serialization_file.get_fp().seek(0)
        data = json.load(self._serialization_file.get_fp())
        self.deserialize(data)

        if not keep_open:
            self.close_serialization_file()

    def save_json(self, file: str | None = None, keep_open=False) -> None:
        '''
        Simplifies direct serialization into a JSON file.
        Keep open flag indicates the serialization file is kept open (and locked) after storing.
        '''
        if file is not None:
            self.set_serialization_file(file, open=True, exclusive=True)
        else:
            if self._serialization_file is None:
                raise Exception("Path to a serialization file must be specified.")
            self.open_serialization_file(exclusive=True)

        data = self.serialize()
        self._serialization_file.get_fp().seek(0)
        self._serialization_file.get_fp().truncate(0)  # lets make sure the entire file overwritten
        json.dump(data, self._serialization_file.get_fp())

        if not keep_open:
            self.close_serialization_file()
