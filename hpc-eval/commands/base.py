import argparse
import config.descriptors as cd
from components.workspace import Workspace
from components.log_init import LogInit
from config.loader import ConfigLoader


class BaseCommand:
    '''
    Base class for all commands. Command is a main structure representing the application itself.
    It is also responsible for initialization, config and state loads, and component instantiation.
    '''

    def __init__(self):
        # known components automatically instantiated with config load
        # (keys are used both as config keys and as propery names within this class)
        self.components = {
            'workspace': Workspace,
            'logger': LogInit,  # initializes loguru logger on construction
        }
        self.args = None  # not loaded yet

    def _prepare_args_parser(self) -> argparse.ArgumentParser:
        '''
        Construction method for argparse parser which also sets common arguments for all commands.
        Descendants should override this to add arguments.
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', help='Path to the main config YAML file.', default='config.yaml')
        return parser

    def _validate_args(self) -> bool:
        '''
        Additional post-validation of the arguments. Errors should be printed out
        and False is retuned if the validation fails.
        '''
        return True  # everything is fine

    def parse_args(self, args: list[str]) -> None:
        '''
        Parse and load internal `args` property using constructed argparse parser.
        This method should not be override by regular commands.
        '''
        parser = self._prepare_args_parser()
        self.args = parser.parse_args(args)
        if not self._validate_args():
            print("Arguments validation failed! Terminating...\n")
            parser.print_help()
            exit(1)

    def load_config(self) -> None:
        '''
        Load configuration and instantiate base components (listed in `component` dict).
        '''
        assert self.args is not None, "Arguments need to be loaded first!"
        schema = cd.Dictionary({key: comp_class.get_config_schema() for key, comp_class in self.components.items()})
        loader = ConfigLoader(schema)

        # load entire configuration structure, terminates on failure
        config = loader.load(self.args.config)

        # use config to instantiate components
        for key, comp_class in self.components.items():
            self[key] = comp_class(config=config[key])  # passing config parts to constructor

    def execute(self) -> None:
        '''
        Main method that performs whatever is expected from the command.
        '''
        pass
