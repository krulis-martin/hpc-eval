import config.descriptors as cd
import copy
# from helpers.file_lock import FileLock


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
            # TODO - use glob
            'config_files': cd.List(cd.String().path()),
            'lock_timeout': cd.Integer(10, "Default timeout [s] for all file locking operations.")
        }, description='Global configuration')

    def load(self, root_file):
        pass
        # FileLock.set_default_timeout() # TODO
