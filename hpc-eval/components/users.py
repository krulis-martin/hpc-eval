from typing import override
import config.descriptors as cd
from helpers.serializable import Serializable


class User(Serializable):
    '''
    Entity representing a record of a single user that can submit solutions.
    '''

    def __init__(self, id: str | None = None, **kwargs):
        '''
        Empty ID is allowed to support deserialization and when new user is being added
        (ID is then assigned by seq. generator). Other data should be passed as named args.
        '''
        self.id = id.strip() if id else None
        for k in ['external_id', 'first_name', 'last_name', 'email']:
            self.__dict__[k] = kwargs.get(k)

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        for k in ['id', 'external_id', 'first_name', 'last_name', 'email']:
            if self.__dict__[k] != other.__dict__[k]:
                return False
        return True

    def update(self, **kwargs):
        for k in ['external_id', 'first_name', 'last_name', 'email']:
            if k in kwargs:  # update only if key is present
                self.__dict__[k] = kwargs.get(k)


class Users(Serializable):
    _config = cd.Dictionary({
        'file': cd.String('_users.json', 'Path to the JSON file where user records are stored.').path(),
    })

    @staticmethod
    def get_config_schema():
        '''
        Return configuration descriptor for this component.
        '''
        return __class__._config

    def __init__(self, config: dict = {}):
        super().__init__(config.get('file'))
        self.users = {}  # the main container
        self._ext_index = {}  # additional index external ID -> user ID
        self._max_id = 0

    def __getitem__(self, id) -> User | None:
        '''
        Safe access to users by ids. None is returned if user is not there.
        '''
        return self.users.get(id)

    def __len__(self) -> int:
        return len(self.users)

    def _update(self, user: User) -> None:
        if user.external_id:
            self._ext_index[user.external_id] = user.id
        if user.id.isdigit():
            numid = int(user.id)
            self._max_id = max(self._max_id, numid)

    @override
    def deserialize(self, data: dict) -> None:
        super().deserialize(data)

        # rebuild external ID index
        self._ext_index = {}
        for user in self.users.values():
            self._update(user)

    def get_by_external_id(self, ext_id) -> User | None:
        '''
        Use an external ID to fetch a user. Return None if not present.
        '''
        id = self._ext_index.get(ext_id)
        return self.users.get(id) if id is not None else None

    def add_user(self, user: User) -> str:
        '''
        Add a new user to the container. Returns ID of the user.
        '''
        if (user.id is not None and user.id in self.users) or user.external_id in self._ext_index:
            return user.id  # already exists

        # assign generated seq. ID if no ID is explicitly given
        if user.id is None:
            while str(self._max_id) in self.users:
                self._max_id += 1
            user.id = str(self._max_id)

        self.users[user.id] = user
        self._update(user)
        return user.id

    def update_user(self, id, **kwargs) -> None:
        '''
        Update user internal data (except for ID, which remains fixed).
        Error is raised if the user does not exist.
        '''
        user = self.users.get(id)
        if not user:
            raise RuntimeError(f"User with ID '{id}' does not exist.")
        if user.external_id:
            del self._ext_index[user.external_id]
        user.update(**kwargs)
        self._update(user)

    def remove_user(self, id) -> User | None:
        '''
        Remove user by ID. Returns object of the removed user or None if no such user exists.
        '''
        if id not in self.users:
            return None

        user = self.users[id]
        if user.external_id:
            del self._ext_index[user.external_id]
        del self.users[id]
        return user
