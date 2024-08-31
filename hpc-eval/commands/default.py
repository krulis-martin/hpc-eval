import argparse
from typing import override
from commands.base import BaseCommand


class Default(BaseCommand):
    '''
    Default command performs all the steps of evaluation (download, build, test, save results).
    '''
    @staticmethod
    def get_name() -> str:
        return 'default'

    def __init__(self):
        pass

    @override
    def _prepare_args_parser(self) -> argparse.ArgumentParser:
        parser = super()._prepare_args_parser()
        return parser

    @override
    def _validate_args(self) -> bool:
        print("Args are faulty...")
        return False

    @override
    def execute(self) -> None:
        print("Executing default...")
        print(self.args)
