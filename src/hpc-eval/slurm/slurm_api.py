import subprocess
import time


class SlurmJob:
    '''
    Wraps a job executed by SLURM sbatch utility.
    It enables polling the state via sacct utility.
    '''

    # the sbatch subset of known args will be extended as needed
    known_args = {
        'account': str,
        'cpus-per-task': int,
        'exclusive': None,
        'gpus': int,
        'gres': str,
        'mem': str,
        'nodelist': str,
        'ntasks': int,
        'output': str,
        'partition': str,
        'time': str,
    }
    short_args = {
        'A': 'account',
        'c': 'cpus-per-task',
        'G': 'gpus',
        'n': 'ntasks',
        'w': 'nodelist',
        'o': 'output',
        'p': 'partition',
        't': 'time',
    }

    def __init__(self):
        self.id = None
        self.running = False
        self.status = None
        self.last_status_load = None
        self.args = {}
        self.commands = []
        pass

    def _add_arg(self, name, value):
        '''
        Internal method for adding arguments. Supports both short and long
        names. Value is verified based on the known args specification.
        Note that short names are translated to long names immediately.
        '''
        if name in SlurmJob.short_args:
            name = SlurmJob.short_args[name]
        if name not in SlurmJob.known_args:
            raise Exception(
                "SLURM argument '{}' is not recognized".format(name))

        verifier = SlurmJob.known_args[name]
        if isinstance(verifier, type):
            if not isinstance(value, verifier):
                raise Exception("Invalid type for argument '{}' is not valid \
                                ({} expected, {} given)".format(name, verifier,
                                                                type(value)))
        elif callable(verifier):
            value = verifier(value, name)  # raises exception on error
        elif value is not None:
            raise Exception(
                "SLURM argument '{}' should have no value".format(name))

        self.args[name] = value

    def _generate_sbatch(self):
        '''
        Internal method that generates sbatch execution command for shell.
        '''
        cmd = ['sbatch << EOF', '#!/bin/sh']
        for name, value in self.args.items():
            directive = '#SBATCH --' + name
            if value is not None:
                directive += '="{}"'.format(str(value).replace("\\",
                                            "\\\\").replace('"', '\\"'))
            cmd.append(directive)

        cmd.extend(self.commands)
        cmd.append('EOF')
        return '\n'.join(cmd)

    def _update_status(self, status_timeout=5):
        '''
        Use sacct tool to load current status of the job.
        '''
        if self.id is None:
            return False

        ts = time.time()
        if (self.last_status_load is None
                or ts-self.last_status_load > status_timeout):

            # -P parseable output, -n no header, -X only the main job
            # (no steps), -j job id, --format=state columns in output
            cmd = 'sacct -PnX -j {} --format=state'.format(self.id)
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)

            assert result.returncode == 0, result.stderr
            new_status = result.stdout.decode('utf-8').strip()
            if new_status == '':
                if self.status is None or self.status == '_STARTING_':
                    self.status = '_STARTING_'
                else:
                    self.status = '_UNKNOWN_'
            else:
                self.status = new_status
                self.last_status_load = ts

            self.running = self.status in ['_STARTING_', 'PENDING', 'RUNNING',
                                           'REQUEUED', 'RESIZING', 'SUSPENDED']
            return True  # status updated

        return False  # no update

    #
    # Public interface
    #

    def add_args(self, name, value=None):
        # TODO better interface
        self._add_arg(name, value)

    def add_command(self, cmd):
        # TODO
        self.commands.append(cmd)

    def run(self):
        '''
        Execute the job via sbatch and return job ID.
        '''
        if self.id is not None:
            raise Exception("Sbatch job was already submitted.")

        result = subprocess.run(self._generate_sbatch(),
                                shell=True, stdout=subprocess.PIPE)

        assert result.returncode == 0, result.stderr
        stdout = result.stdout.decode('utf-8')
        assert 'Submitted batch job' in stdout, result.stderr

        self.id = int(stdout.split(' ')[3])  # job id
        self.running = True
        return self.id

    def cancel(self):
        '''
        Try to cancel a running job by scancel.
        '''
        if self.id is None:
            raise Exception("The job has not been started yet.")
        if not self.is_running():
            return False  # cannot cancel anymore

        cmd = 'scancel {}'.format(self.id)
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
        assert result.returncode == 0, result.stderr
        return True  # scancel was called

    def is_running(self, status_timeout=5):
        '''
        Is the job currently running?
        The status_timeout [s] defines how old status from cache is acceptable.
        If the status in cache is older, status is refreshed.
        '''
        if self.id is None:
            return False

        self._update_status(status_timeout)
        return self.running

    def get_status(self, status_timeout=5):
        '''
        Return raw string status.
        The status_timeout [s] defines how old status from cache is acceptable.
        If the status in cache is older, status is refreshed.
        '''
        self._update_status(status_timeout)
        return self.status

    def failed(self, unknow_is_failure=True):
        '''
        Checks whether the completion of the job was ok or not.
        Always returns False before the job terminates.
        '''
        if self.id is None or self.is_running():
            return False

        if self.status == '_UNKNOWN_':
            return unknow_is_failure
        return self.status != 'COMPLETED'
