from typing import override
from loguru import logger
import time
import datetime
import config.descriptors as cd
from helpers.serializable import Serializable


class Solution(Serializable):
    '''
    Entity representing a single solution record (one submission addressing one assignment by one student).
    '''

    def __init__(self, id: str | None = None, **kwargs):
        '''
        '''
        self.external_id = None
        self.user_id = None
        self.assignment_id = None

        # autoloading from named arguments
        for k in self.__dict__:
            self.__dict__[k] = kwargs.get(k)

        self.id = id.strip() if id else None
        self.submitted_at = int(time.time())
        self.dir = None

    def get_dir(self) -> str:
        '''
        Return a directory name used to store solution data in the assignment-user designated box.
        The dirname comprise submission time and solution ID(s).
        '''
        if self.dir is None:
            assert self.id, "The solution does not have an ID yet!"
            ext = ('-' + self.external_id) if self.external_id else ''
            dt = datetime.datetime.fromtimestamp(self.submitted_at)
            self.dir = f"{dt.strftime('%Y%m%d-%H%M%S')}-{self.id}{ext}"

        return self.dir


class Solutions(Serializable):
    '''
    Container for solutions. Manages serialization, lookups, ...
    '''
    _config = cd.Dictionary({
        'file': cd.String('_solutions/solutions.json', 'Path to the JSON file where solution records are stored.'
                          ).path(),
    })

    @staticmethod
    def get_config_schema():
        '''
        Return configuration descriptor for this component.
        '''
        return __class__._config

    def __init__(self, config: dict = {}):
        logger.trace(f'Solutions.__init__({config})')
        super().__init__(config.get('file'))

        self.solutions = {}  # the main container
        self._ext_index = {}  # additional index external ID -> solution ID
        self._max_id = 0

    def __getitem__(self, id) -> Solution | None:
        '''
        Safe access to solutions by ids. None is returned if solution does not exist.
        '''
        return self.solutions.get(id)

    def __len__(self) -> int:
        return len(self.solutions)

    def _update(self, solution: Solution) -> None:
        if solution.external_id:
            self._ext_index[solution.external_id] = solution.id
        if solution.id.isdigit():
            numid = int(solution.id)
            self._max_id = max(self._max_id, numid)

    @override
    def deserialize(self, data: dict) -> None:
        super().deserialize(data)

        # rebuild external ID index
        self._ext_index = {}
        for solution in self.solutions.values():
            self._update(solution)

    def get_by_external_id(self, ext_id) -> Solution | None:
        '''
        Use an external ID to fetch a solution. Return None if not present.
        '''
        id = self._ext_index.get(ext_id)
        return self.solutions.get(id) if id is not None else None

    def add_solution(self, solution: Solution) -> str | None:
        '''
        Add a new solution to the container. Returns ID of the solution, None if solution already exists.
        '''
        assert solution.user_id and solution.assignment_id, "Solution must have user and assignment references."

        if (solution.id is not None and solution.id in self.solutions) or solution.external_id in self._ext_index:
            return None  # already exists

        # assign generated seq. ID if no ID is explicitly given
        if solution.id is None:
            while str(self._max_id) in self.solutions:
                self._max_id += 1
            solution.id = str(self._max_id)

        self.solutions[solution.id] = solution
        self._update(solution)
        return solution.id

    def remove_solution(self, id: str) -> Solution | None:
        '''
        This is a rare operation that removes solution from the database.
        Solutions are removed only when something bad happens.
        Returns the solution object being removed or None if no such solution exists.
        '''
        if id not in self.solutions:
            return None

        solution = self.solutions[id]
        if solution.external_id:
            del self._ext_index[solution.external_id]
        del self.solutions[id]
        return solution
