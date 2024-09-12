import config.descriptors as cd
import copy
import os
from ruamel.yaml import YAML
from helpers.file_lock import FileLock


def _load_yaml(file):
    if os.path.exists(file):
        yaml = YAML(typ='safe')
        with open(file, 'r') as fp:
            return yaml.load(fp)
    else:
        return {}


class ConfigLoader:
    @staticmethod
    def is_configurable(cls):
        '''
        Return True if given class is configurable (duck typing detection).
        '''
        return hasattr(cls, 'get_config_schema') and isinstance(cls.__dict__.get('get_config_schema'), staticmethod)

    def __init__(self, schema: cd.Dictionary):
        assert 'general' not in schema.items, "Component config must not contain reserved key 'general'"
        self.schema = copy.copy(schema)
        self.schema.items = copy.copy(self.schema.items)
        self.schema.items['general'] = cd.Dictionary({
            'config_files': cd.String().glob(),
            'lock_timeout': cd.Integer(10, "Default timeout [s] for all file locking operations.")
        }, description='Global configuration')

    def load(self, root_file):
        root_cfg = _load_yaml(root_file)
        config = self.schema.load(root_cfg, root_file)

        # apply general config
        general = config['general']
        FileLock.set_default_timeout(general['lock_timeout'])
        # print(general['config_files'])
        # TODO - proces general.config_files

        return config
