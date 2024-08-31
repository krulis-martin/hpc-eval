import config.descriptors as cd
import copy


class ConfigLoader:
    def __init__(self, schema: cd.Dictionary):
        assert 'general' not in schema.items, "Component config must not contain reserved key 'general'"
        self.schema = copy.copy(schema)
        self.schema.items = copy.copy(self.schema.items)
        self.schema.items['general'] = cd.Dictionary({
            # TODO - use glob
            'config_files': cd.List(cd.String().path())
        }, description='Global configuration')

    def load(self, root_file):
        pass
