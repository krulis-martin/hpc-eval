from slurm.args import SlurmArgs
import slurm.api as api

from typing import Self
import time


class SlurmJob:
    '''
    Wraps a job executed by the SLURM sbatch utility.
    It enables polling the state via sacct utility.
    '''

    def __init__(self, name: str, args: SlurmArgs | None = None):
        self.name = name
        self.args = SlurmArgs(args)
        self.commands = []

        # running/termination state
        self.id = None  # assigned by sbatch when the job is started
        self.running = False
        self.state = None  # raw SLURM state string
        self.last_update = None  # when the state was last read from SLURM
        self.exit_code = None  # exit code of the terminated sbatch script
        self.signal = None  # signal that terminted the sbatch script

    def _update_state(self, state_timeout: int = 5) -> bool:
        '''
        Use sacct tool to load current state of the job.
        '''
        if self.id is None:
            return False

        ts = time.time()
        if (self.last_update is None or ts-self.last_update > state_timeout):
            result = api.get_job_state(self.id)
            if result is not None:
                # copy the resutl to internal properties
                for key in ['state', 'running', 'exit_code', 'signal']:
                    self.key = result.get(key)
            elif self.state is None or self.state == '_STARTING_':
                self.state = '_STARTING_'

            self.last_update = ts
            return True  # state updated

        return False  # no update, timeout has not passed yet

    #
    # Public interface
    #

    def get_name(self) -> str:
        '''
        Return local name of the job (unique identifier assigned on creation).
        '''
        return self.name

    def get_id(self) -> int | None:
        '''
        Return ID of the running SLURM job.
        '''
        return self.id

    def add_args(self, name_or_args: str | dict | SlurmArgs, value=None
                 ) -> Self:
        '''
        Add argument (name, value) or multiple arguments as dict or SlurmArgs
        instance.
        '''
        if type(name_or_args) is dict or isinstance(name_or_args, SlurmArgs):
            assert value is None, 'Unexpected value argument.'
            self.args.add_args(name_or_args)
        else:
            self.args.add_arg(name_or_args, value)
        return self

    def add_command(self, cmd: str | list) -> Self:
        '''
        Add one or more commands (string or a list of strings).
        '''
        if type(cmd) is list:
            self.commands.extend(cmd)
        else:
            self.commands.append(cmd)
        return self

    def run(self) -> int:
        '''
        Execute the job via sbatch and return the job ID.
        '''
        if self.id is not None:
            raise Exception("Sbatch job was already submitted.")

        self.id = api.sbatch(self.args, self.commands)
        self.running = True
        return self.id

    def cancel(self) -> bool:
        '''
        Try to cancel a running job by scancel.
        '''
        if self.id is None:
            raise Exception("The job has not been started yet.")
        if not self.is_running():
            return False  # cannot cancel anymore

        api.scancel(self.id)
        return True  # scancel was called

    def is_running(self, state_timeout: int = 5) -> bool:
        '''
        Is the job currently running?
        The state_timeout [s] defines how old state from cache is acceptable.
        If the state in cache is older, state is refreshed.
        '''
        if self.id is None:
            return False

        self._update_state(state_timeout)
        return self.running

    def get_state(self, state_timeout: int = 5) -> str | None:
        '''
        Return raw string representing SLURM state.
        The state_timeout [s] defines how old state from cache is acceptable.
        If the state in cache is older, state is refreshed.
        https://slurm.schedmd.com/sacct.html#SECTION_JOB-STATE-CODES
        '''
        self._update_state(state_timeout)
        return self.state

    def failed(self) -> bool:
        '''
        Checks whether the completion of the job was ok or not.
        Always returns False before the job terminates.
        '''
        if self.id is None or self.is_running():
            return False

        return self.state != 'COMPLETED'
