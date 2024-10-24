from typing import Self, override
import os
import glob
from loguru import logger


def _normalize_path(path, base_file, _):
    '''
    If the path is relative, convert it to absolute using `base_file` path as reference.
    This function has conveniently the same order of arguments as expected for descriptor postprocessors.
    '''
    logger.trace(f'_normalize_path({path}, {base_file})')
    if os.path.isabs(path):
        return path
    base = os.path.dirname(base_file)
    return os.path.normpath(f'{base}/{path}')


def _glob_postprocessor(pattern, base_file, merge_with):
    '''
    Helper postprocessor that handles glob path patterns (used in String.glob())
    '''
    merge_with = merge_with[:] if merge_with else []
    if not os.path.isabs(pattern) and base_file:
        base = os.path.dirname(base_file)
        pattern = f'{base}/{pattern}'

    merge_with.extend([os.path.normpath(p) for p in glob.glob(pattern, recursive=True)])
    return merge_with


class Base:
    '''
    Base class for all value descriptors. A descriptor represents a value type with optional verification and
    processing parameters.
    '''

    def __init__(self, default=None, description: str | None = None):
        '''
        Initialize parameters common to all descriptors.
        - `default` value used when not present in loaded struct
        - `description` used for generating help
        '''
        self.default = default
        self.description = description
        self.name = None  # key in the parent container
        self.full_name = None  # cache for fully qualified name like `parent.list[2].subitem`
        self.parent = None  # reference to containing descriptor (dict or list)
        self.preprocessor = None  # lambda invoked on a value before validation and loading
        self.postprocessor = None  # lambda invoked on a value just before returned by loading

    def _preprocess(self, value, source):
        if self.preprocessor:
            return self.preprocessor(value, source)
        return value

    def _postprocess(self, value, source, merge_with):
        if self.postprocessor:
            return self.postprocessor(value, source, merge_with)
        return value

    def embed(self, name: str | int, parent: Self):
        '''
        Post-initialize the descriptor by embedding it into a parent structure (dict or list).
        '''
        self.name = name
        self.parent = parent
        self.full_name = None  # this cache needs to be reset (just in case)

    def get_name(self):
        '''
        Return local identifier (dict/list key where the descriptor is embedded).
        '''
        return self.name

    def get_full_name(self):
        '''
        Compute fully qualified name by recusively assembling names of ancestors.
        '''
        if self.full_name is None:
            if self.parent is not None:
                self.full_name = self.parent.get_full_name()
            else:
                self.full_name = ''

            if type(self.name) is int:
                self.full_name += f'[{self.name}]'
            elif type(self.name) is str:
                if self.full_name:
                    self.full_name += '.'
                self.full_name += self.name

        return self.full_name

    def get_description(self):
        '''
        Returns description used for generating user help comment.
        '''
        return self.description

    def get_default_value(self):
        '''
        Returns default value.
        '''
        return self.default

    def set_preprocessor(self, preprocessor: callable) -> Self:
        '''
        Set preprocessor function which is called just before loading/validating an input.
        '''
        self.preprocessor = preprocessor
        return self

    def set_postprocessor(self, postprocessor: callable) -> Self:
        '''
        Set postprocessor function which is called as the last step of loading.
        '''
        self.postprocessor = postprocessor
        return self

    def validate(self, value, source, errors: list) -> bool:
        '''
        Perform validation. On failure, add ValidationError object(s) in the errors list.
        `value` - raw value to be validated
        `source` - path to file (yaml, json, ...) from which the structure is being loaded
        `error` - accumulator list for ValidationError objects
        Returns True on success.
        '''
        return True

    def load(self, value, source, merge_with=None):
        '''
        Load, sanitize, and possibly merge the value.
        `value` - raw value to be loaded
        `source` - path to file (yaml, json, ...) from which the structure is being loaded
        `merge_with` - previously loaded value used when two structures are being merged
        Returns sanitized value (possibly previous from merge_with or default).
        '''
        value = self._preprocess(value, source)

        # this implementation should work for all scalar values
        if value is not None:
            return self._postprocess(value, source, merge_with)
        if merge_with is not None:
            return merge_with
        return self.default


class ValidationError:
    '''
    A structure holding descriptor and an error message.
    '''

    def __init__(self, descriptor: Base, source, message: str):
        self.full_name = descriptor.get_full_name()
        self.source = source
        self.message = message

    def __str__(self):
        name = f"'{self.full_name}'" if self.full_name else '<root>'
        return f"{name} (in '{self.source}'): {self.message}"


class Integer(Base):
    '''
    Descriptor of integral parameter.
    '''

    def __init__(self, default: int | None = 0, description: str | None = None):
        super().__init__(default=default, description=description)

    @override
    def validate(self, value, source, errors: list) -> bool:
        value = self._preprocess(value, source)
        if type(value) is not int:
            errors.append(ValidationError(self, source, f"Integer value expected, {type(value).__name__} given."))
            return False
        return True


class String(Base):
    '''
    Descriptor of a string parameter.
    '''

    def __init__(self, default: str | None = '', description: str | None = None):
        super().__init__(default=default, description=description)
        self.enum_values = None

    def enum(self, values: list | str) -> Self:
        '''
        Make the string parameter accept only values from given enum-list.
        If called multiple times, all given options are concatenated.
        '''
        if type(values) is str:
            values = [values]
        if self.enum_values is None:
            self.enum_values = values
        else:
            self.enum_values.extend(values)
        return self

    def path(self) -> Self:
        '''
        Treat the string as a fs path. Convert relative paths to absolute paths using source file as base.
        '''
        self.enum_values = None
        self.postprocessor = _normalize_path
        return self

    def glob(self) -> Self:
        '''
        Treat the string as a glob pattern. When loading, the glob is resolved returning a list of paths
        (instead of a string).
        '''
        self.enum_values = None
        self.postprocessor = _glob_postprocessor
        return self

    @override
    def validate(self, value, source, errors: list) -> bool:
        value = self._preprocess(value, source)
        if type(value) is not str:
            errors.append(ValidationError(self, source, f"String value expected, {type(value).__name__} given."))
            return False

        if self.enum_values and value not in self.enum_values:
            errors.append(ValidationError(self, source,
                                          f"Value {value} is not in enum [{', '.join(self.enum_values)}]"))
            return False

        return True


class Bool(Base):
    '''
    Descriptor of a bool flag.
    '''

    def __init__(self, default: bool | None = False, description: str | None = None):
        super().__init__(default=default, description=description)

    @override
    def validate(self, value, source, errors: list) -> bool:
        value = self._preprocess(value, source)
        if type(value) is not bool:
            errors.append(ValidationError(self, source, f"Bool value expected, {type(value).__name__} given."))
            return False
        return True


class Dictionary(Base):
    '''
    Descriptor for dictionaries, which act as a container for other descriptors.
    '''

    def __init__(self, items: dict[str, Base], default: dict = {}, description: str | None = None):
        '''
        Items is a dictionary where names matches names in the described structure and values are value descriptors.
        The value descriptors are automatically embedded (have their parent and name properties set).
        '''
        super().__init__(default={}, description=description)
        self.items = items
        for name in items:
            assert isinstance(items[name], Base), f"Config dict value of '{name}' is not a descriptor object."
            items[name].embed(name, self)
            self.default[name] = default.get(name, items[name].default)

    @override
    def validate(self, value, source, errors: list) -> bool:
        value = self._preprocess(value, source)
        if type(value) is not dict:
            errors.append(ValidationError(self, source, f"Value '{value}' is not a dict."))
            return False

        ok = True
        for key, val in value.items():
            if key in self.items:
                if not self.items[key].validate(val, source, errors):
                    ok = False
            else:
                errors.append(ValidationError(self, source, f"Unexpected dict key '{key}'."))
                ok = False
        return ok

    @override
    def load(self, value: dict | None, source, merge_with: dict | None = None):
        if not value:
            return merge_with if merge_with else self.default.copy()

        res = self.default.copy()
        merge_with = merge_with or {}
        for key, item in self.items.items():
            res[key] = item.load(value.get(key), source, merge_with.get(key))
        return res


class List(Base):
    '''
    Descriptor representing a list of items of the same (sub)type.
    '''

    def __init__(self, sub_type: Base, default: list = [], description: str | None = None):
        '''
        Descriptor for a list of items of the same sub_type.
        `sub_type` is descriptor of the items in the list.
        '''
        super().__init__(default=default, description=description)
        self.sub_type = sub_type
        self.sub_type.embed(-1, self)  # -1 indicate no valid index
        self.append = False
        self.is_collapsible = False

    def set_append(self, append: bool = True) -> Self:
        self.append = append
        return self

    def collapsible(self, collapsible: bool = True) -> Self:
        '''
        If the list is collapsible, it allows replacing itself with its sub type in the config,
        and creating a list with single sub-item in the load.
        Note: this works only if the sub-type is not a list.
        '''
        self.is_collapsible = collapsible
        return self

    @override
    def validate(self, value, source, errors: list) -> bool:
        value = self._preprocess(value, source)
        if type(value) is not list:
            if self.is_collapsible:  # it is possible this is collapsed single value (shorthand)
                self.sub_type.name = 0
                ok = self.sub_type.validate(value, source, errors)
                self.sub_type.name = -1  # reset to normal
                return ok

            errors.append(ValidationError(self, source, f"Value '{value}' is not a list."))
            return False

        ok = True
        for idx, val in enumerate(value):
            self.sub_type.name = idx  # bit of a hack actually, we need to smuggle index into descriptor somehow
            if not self.sub_type.validate(val, source, errors):
                ok = False
        self.sub_type.name = -1  # reset to normal
        return ok

    @override
    def load(self, value, source, merge_with: list | None = []):
        if type(value) is not list and value is not None and self.is_collapsible:
            value = [value]

        if not value:
            return merge_with if merge_with else self.default.copy()

        res = merge_with[:] if self.append and merge_with else []
        for idx, val in enumerate(value):
            self.sub_type.name = idx  # bit of a hack actually, we need to smuggle index into descriptor somehow
            res.append(self.sub_type.load(val, source))

        return res


class NamedList(Base):
    '''
    Descriptor representing a dictionary which works as an associative array
    (names matters all values have the same type).
    '''

    def __init__(self, sub_type: Base, default: dict = {}, description: str | None = None):
        '''
        Descriptor for a named-list (dict) of items of the same sub_type.
        `sub_type` is descriptor of the items in the list.
        '''
        super().__init__(default=default, description=description)
        self.sub_type = sub_type
        self.sub_type.embed(None, self)  # -1 indicate no valid index

    @override
    def validate(self, value, source, errors: list) -> bool:
        value = self._preprocess(value, source)
        if type(value) is not dict:
            errors.append(ValidationError(self, source, f"Value '{value}' is not a dictionary."))
            return False

        ok = True
        for name, val in value.items():
            self.sub_type.name = name  # bit of a hack actually, we need to smuggle the name into descriptor somehow
            if not self.sub_type.validate(val, source, errors):
                ok = False
        self.sub_type.name = None  # reset to normal
        return ok

    @override
    def load(self, value: dict | None, source, merge_with: dict | None = {}):
        if not value:
            return merge_with if merge_with else self.default.copy()

        res = merge_with.copy()
        for name, val in value.items():
            self.sub_type.name = name  # bit of a hack actually, we need to smuggle the name into descriptor somehow
            res[name] = self.sub_type.load(val, source)

        return res
