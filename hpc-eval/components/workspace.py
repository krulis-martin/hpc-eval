import os
from loguru import logger
import config.descriptors as cd
from components.solutions import Solution


class Workspace:
    '''
    Component that manages paths, directories, and files.
    '''
    _config = cd.Dictionary({
        'root': cd.String(os.getcwd(), 'Path to the root project directory').path(),
        'solutions_dir': cd.String('solutions', 'Solutions archive subdir (_ prefix is added automatically)'),
        'jobs_dir': cd.String('jobs', 'Name of the SLURM jobs subdir (_ prefix is added automatically)'),
        'results_dir': cd.String('results', 'Results archive subdir (_ prefix is added automatically)'),
        'tmp_dir': cd.String('tmp', 'Directory for temporary data staging (_ prefix is added automatically)'),
    })
    _dir_mode = 0o770

    @staticmethod
    def get_config_schema():
        '''
        Return configuration descriptor for this component.
        '''
        return __class__._config

    def __init__(self, config: dict = {}):
        logger.trace(f'Workspace.__init__({config})')

        root = os.path.abspath(config.get('root', os.getcwd()))
        if not os.path.isdir(self.root):
            raise Exception(f"Path {self.root} is not an existing directory.")

        # lets make sure itelisense remembers properties (and so we can iterate them)
        self.solutions_dir = None
        self.jobs_dir = None
        self.results_dir = None
        self.tmp_dir = None

        for dir in self.__dict__:  # lets fill previously declared properties from config
            default = __class__._config.items[dir].default
            self.__dict__[dir] = os.path.abspath(self.root + '/_' + config.get(dir, default))

        self.root = root

    def create_tmp_dir(self, prefix: str = '') -> str:
        '''
        Create a new unique tmp dir (as a subdir of our temp-dir zone).
        Prefix can be used to differentiate various reasons for temp creation.
        Full path to the temp dir is returned after creation.
        '''
        prefix = prefix or 'tmp'
        counter = 0
        tries = 0
        while True:
            counter += 1
            path = f'{self.tmp_dir}/{prefix}{counter}'
            if not os.path.exists(path):
                try:
                    os.makedirs(path, mode=__class__._dir_mode)
                    return path
                except OSError as e:
                    tries += 1
                    if tries > 3:
                        raise e

    def save_solution_dir(self, tmp_dir: str, solution: Solution) -> None:
        '''
        Take a staged tmp dir and move it as a new solution.
        '''
        assert os.path.dirname(tmp_dir) == self.tmp_dir, f"Given tmp_dir '{
            tmp_dir}' is not located in the local temp area."

        base = f'{self.solutions_dir}/{solution.assignment_id}/{solution.user_id}'
        os.makedirs(base, mode=__class__._dir_mode, exit_ok=True)

        # we intentionally do not use shutil.move() to ensure the move will work only on the same fs
        # (this operation should be atomic according to POSIX)
        os.rename(tmp_dir, f'{base}/{solution.get_dir()}')

    def get_slurm_job_dir(self, job_name):
        '''
        Return path to a working directory of a particular slurm job.
        '''
        dir = self.slurm_jobs_dir + '/' + job_name
        os.makedirs(dir)
        return dir
