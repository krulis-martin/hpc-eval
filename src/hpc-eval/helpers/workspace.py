import os


class Workspace:
    '''
    Component that manages paths, directories, and files.
    '''

    def __init__(self, root: str = None, config: dict = {}):
        self.root = os.path.abspath(root or os.getcwd())
        if not os.path.isdir(self.root):
            raise Exception(f"Path {self.root} is not an existing directory.")

        self.slurm_jobs_dir = os.path.abspath(
            self.root + '/_' + config.get('slurm_jobs', 'jobs'))

    def get_slurm_job_dir(self, job_name):
        '''
        Return path to a working directory of a particular slurm job.
        '''
        dir = self.slurm_jobs_dir + '/' + job_name
        os.makedirs(dir)
        return dir
