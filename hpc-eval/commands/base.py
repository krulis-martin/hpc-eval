import argparse
import config.descriptors as cd
from config.loader import ConfigLoader
from components.workspace import Workspace
from components.log_init import LogInit
from components.users import Users


class BaseCommand:
    '''
    Base class for all commands. Command is a main structure representing the application itself.
    It is also responsible for initialization, config and state loads, and component instantiation.
    '''

    def __init__(self):
        # known components automatically instantiated with config load
        # (keys are used both as config keys and as propery names within this class)
        self.components = {
            'logger': LogInit,  # initializes loguru logger on construction
            'workspace': Workspace,
            'users': Users,
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
        Arguments are loaded before logger initialization, print() must be used for additional notifications.
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
        schema = cd.Dictionary({key: comp_class.get_config_schema() for key, comp_class in self.components.items()
                                if ConfigLoader.is_configurable(comp_class)})
        loader = ConfigLoader(schema)

        # load entire configuration structure, terminates on failure
        config = loader.load(self.args.config)

        # use config to instantiate components
        for key, comp_class in self.components.items():
            if ConfigLoader.is_configurable(comp_class):
                self.__dict__[key] = comp_class(config=config[key])  # passing config parts to constructor
            else:
                self.__dict__[key] = comp_class()  # no config

    def load_state(self) -> None:
        '''
        Load states of the components, perform necessary file locking.
        An error should be raised if the state cannot be loaded of the files cannot be locked.
        '''
        pass

    def execute(self) -> None:
        '''
        Main method that performs whatever is expected from the command.
        '''
        pass

    def save_state(self) -> None:
        '''
        Save states of all modified components. The state may be saved already during the execution,
        this method is called just before termination (even if execution raised an error).
        '''
        pass
