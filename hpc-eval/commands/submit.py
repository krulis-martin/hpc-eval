import os
import argparse
import shutil
import zipfile
from typing import override
from loguru import logger
from commands.base import BaseCommand
from components.solutions import Solution, Solutions


class Submit(BaseCommand):
    '''
    Submit command that loads new solution into submit queue.
    '''
    @staticmethod
    def get_name() -> str:
        return 'submit'

    def __init__(self):
        super().__init__()
        self.components['solutions'] = Solutions

    @override
    def _prepare_args_parser(self) -> argparse.ArgumentParser:
        parser = super()._prepare_args_parser()
        parser.add_argument('--id', type=str,
                            help='Internal ID of the solution. Assigned automatically if missing.')
        parser.add_argument('--external-id', type=str,
                            help='Optional external ID for the solution (must be unique).')
        parser.add_argument('--user', type=str,
                            help='Identification of the user making the submit (by internal ID).')
        parser.add_argument('--user-ext', type=str,
                            help='Identification of the user making the submit (by external ID).')
        parser.add_argument('--assignment', type=str,
                            help='Identification of the assignment being submitted.')
        parser.add_argument('--extract', default=False, action="store_true",
                            help='Extract a .zip archive into the submit box. Only a sigle file must be given.')
        parser.add_argument('files', type=str, metavar="file", nargs="+",
                            help='File to be copied into submit box.')
        return parser

    @override
    def _validate_args(self) -> bool:
        if not self.args.user and not self.args.user_ext:
            print("Either --user or --user-ext must be used to identify the user.")
            return False

        if self.args.extract:
            if len(self.args.files) != 1:
                print("If --extract option is selected, a single archive file must be given.")
                return False

            if not self.args.files[0].endswith('.zip'):
                print("Only .zip archives are supported by the extraction option at the moment.")
                return False

        for file in self.args.files:
            if not os.path.exists(file) or not os.access(file, os.R_OK):
                print(f"File '{file}' does not exist or is not readable.")
                return False

        return True

    @override
    def load_state(self) -> None:
        if self.users.serialization_file_exists():
            self.users.load_json()
        if self.solutions.serialization_file_exists():
            self.solutions.load_json(keep_open=True, exclusive=True)  # for update

    def _create_solution(self, user, assignment) -> Solution:
        '''
        Creates new solution object, fills it with correct data, and adds it in the container.
        '''
        solution_args = {
            'id': self.args.id or None,
            'external_id': self.args.external_id or None,
            'user_id': user.id,
            'assignment_id': assignment.id,
        }

        solution = Solution(**solution_args)
        if self.solutions.add_solution(solution) is None:
            return None
        return solution

    def _prepare_temp_dir(self) -> str:
        '''
        Stage a temp dir with a copy of all submitted files.
        Returns path to the tmp dir.
        '''
        tmp_dir = self.workspace.create_tmp_dir('submit')
        logger.debug(f'Staging newly submitted files in {tmp_dir}.')

        if self.args.extract:
            logger.trace(f"Extracting ZIP '{self.args.files[0]}'.")
            with zipfile.ZipFile(self.args.files[0], 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)
        else:
            for file in self.args.files:
                if os.path.isdir(file):  # dirs are copied recursively
                    logger.trace(f"Copying directory '{file}' recursively.")
                    shutil.copytree(file, f'{tmp_dir}/{os.path.basename(file)}', copy_function=shutil.copy)
                else:
                    logger.trace(f"Copying file '{file}'.")
                    shutil.copy(file, tmp_dir)
        return tmp_dir

    @override
    def execute(self) -> None:
        # get the user making the submission
        user = None
        if self.args.user:
            user = self.users[self.args.user]
        if user is None and self.args.user_ext:
            user = self.users.get_by_external_id(self.args.user_ext)
        if user is None:
            logger.error(f"User '{self.args.user or self.args.user_ext}' not found.")
            return

        assignment = self.args.assignment  # TODO assignment ID validation
        # if assignment is not specified and there is exactly one defined, use it

        solution = self._create_solution(user, assignment)
        if not solution:
            logger.error("A solution with given ID (or external ID) already exists.")
            return

        try:
            tmp_dir = self._prepare_temp_dir()  # staging first
            self.workspace.save_solution_dir(tmp_dir, solution)
        except Exception as e:
            # undo the solution creation if something fails
            self.solutions.remove_solution(solution.id)
            if os.path.isdir(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
            raise e

    @override
    def save_state(self) -> None:
        self.solutions.save_json()
