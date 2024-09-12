import argparse
from loguru import logger
from typing import override
from commands.base import BaseCommand
from components.users import User


class AddUser(BaseCommand):
    '''
    Introduce a new user into the internal database manually.
    '''
    @staticmethod
    def get_name() -> str:
        return 'add_user'

    @override
    def _prepare_args_parser(self) -> argparse.ArgumentParser:
        parser = super()._prepare_args_parser()
        parser.add_argument('--id', type=str, help='Identification of the user. If missing, ID is generated.')
        parser.add_argument('--external_id', type=str, help='Optional external (another) identification of the user.')
        parser.add_argument('--first_name', type=str, required=True)
        parser.add_argument('--last_name', type=str, required=True)
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--update', default=False, action="store_true",
                            help='Allows updates (if a user record with the same ID exists).')
        return parser

    @override
    def _validate_args(self) -> bool:
        if not self.args.id and not self.args.external_id:
            print("Either --id or --external_id needs to be specified.")
            return False
        for key in ['first_name', 'last_name', 'email']:
            if not self.args.__dict__[key]:
                print(f"Argument --{key} must have non-empty value.")
                return False
        return True

    @override
    def load_state(self) -> None:
        if self.users.serialization_file_exists():
            self.users.load_json(keep_open=True, exclusive=True)  # for update

    @override
    def execute(self) -> None:
        # Prepare user record to be added/updated
        id = self.args.id or None
        external_id = self.args.external_id or None
        user_data = {'external_id': external_id}
        for key in ['first_name', 'last_name', 'email']:
            user_data[key] = self.args.__dict__[key]
        user = User(id, **user_data)

        # find if record with matching ID exists
        existing = self.users[id] if id else None
        if not existing and external_id:
            existing = self.users.get_by_external_id(external_id)

        # user already exist
        if existing:
            if user == existing:
                logger.info("User already exists and the data match, nothing to do.")
                return  # nothing to do
            if not self.args.update:
                logger.error("User already exists, but unable to update data. Use --update option.")
                return

            self.users.update_user(existing.id, **user_data)
            logger.success(f"User '{existing.id}' was updated.")
        else:
            id = self.users.add_user(user)
            logger.success(f"New user with ID '{id}' was created.")

    @override
    def save_state(self) -> None:
        self.users.save_json()
