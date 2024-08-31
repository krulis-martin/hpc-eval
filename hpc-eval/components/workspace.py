import os
import config.descriptors as cd


class Workspace:
    '''
    Component that manages paths, directories, and files.
    '''
    _config = cd.Dictionary({
        'root': cd.String(os.getcwd(), 'Path to the root project directory').path(),
        'submit_dir': cd.String('submits', 'A subdir for new submissions (_ prefix is added automatically)'),
        'solutions_dir': cd.String('solutions', 'Solutions archive subdir (_ prefix is added automatically)'),
        'jobs_dir': cd.String('jobs', 'Name of the SLURM jobs subdir (_ prefix is added automatically)'),
        'results_dir': cd.String('results', 'Results archive subdir (_ prefix is added automatically)'),
    })

    @staticmethod
    def get_config_schema():
        '''
        '''
        return __class__._config

    def __init__(self, config: dict = {}):
        self.root = os.path.abspath(config.get('root', os.getcwd()))
        if not os.path.isdir(self.root):
            raise Exception(f"Path {self.root} is not an existing directory.")

        self.slurm_jobs_dir = os.path.abspath(
            self.root + '/_' + config.get('jobs_dir', 'jobs'))

    def get_slurm_job_dir(self, job_name):
        '''
        Return path to a working directory of a particular slurm job.
        '''
        dir = self.slurm_jobs_dir + '/' + job_name
        os.makedirs(dir)
        return dir
