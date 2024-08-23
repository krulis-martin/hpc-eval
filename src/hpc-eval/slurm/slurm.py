from .slurm_job import SlurmJob
from .slurm_args import SlurmArgs


class Slurm:
    def __init__(self, default_args):
        self.jobs = {}
        self.default_args = SlurmArgs(default_args)

    def create_job(self, name: str) -> SlurmJob:
        '''
        Create a new job and register it under given name.
        '''
        if name in self.jobs:
            raise Exception(f"Job with name {name} already exists.")
        job = SlurmJob(name)
        self.jobs[name] = job
        return job

    def get_job(self, name: str):
        '''
        Return an object representing a job under given name.
        '''
        return self.jobs.get(name)
