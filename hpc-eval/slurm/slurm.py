from slurm.job import SlurmJob
from slurm.args import SlurmArgs
import slurm.api as api
from helpers.serializable import Serializable
import time


class Slurm(Serializable):
    '''
    Main interface for the Slurm job dispatching. Creates and manages
    SlurmJob objects through which the execution is controlled.
    '''

    def __init__(self, default_args: SlurmArgs | dict | None = None):
        super().__init__()
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

    def get_job(self, name: str) -> SlurmJob | None:
        '''
        Return an object representing a job under given name.
        '''
        return self.jobs.get(name, None)

    def update_jobs(self) -> list:
        '''
        Perform a collective update of all running jobs (more efficient).
        Return list of SlurmJobs that just turned into a non-running state.
        '''
        running = {job.get_id(): job for job in self.jobs.values()
                   if job.running}
        if not running:
            return []
        ids = [job.get_id() for job in running.values()]

        states = api.get_job_states(ids)
        ts = time.time()
        for id, state in states.items():
            self.jobs[id]._process_update(state, ts)

        # return jobs that just terminated
        return [job for job in running if not job.running]

    def release(self, name: str) -> SlurmJob | None:
        '''
        Remove job by its name from internal job list.
        Returns the job removed, or None if no such job exists.
        '''
        return self.jobs.pop(name, None)
