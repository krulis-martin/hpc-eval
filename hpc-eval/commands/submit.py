import argparse
from typing import override
from commands.base import BaseCommand


class Submit(BaseCommand):
    '''
    Submit command that loads new solution into submit queue.
    '''
    @staticmethod
    def get_name() -> str:
        return 'submit'

    @override
    def _prepare_args_parser(self) -> argparse.ArgumentParser:
        parser = super()._prepare_args_parser()
        parser.add_argument('--user', required=True,
                            help='Identification of the user making the submit.')
        parser.add_argument('--assignment', required=True,
                            help='Identification of the assignment being submitted.')
        return parser

    @override
    def execute(self) -> None:
        print("Executing submit...")
        print(self.args)
