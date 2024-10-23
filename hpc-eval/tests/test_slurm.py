import unittest
import os
import tempfile
import time
import slurm.api as sapi
from slurm.args import SlurmArgs
from slurm.slurm import Slurm


@unittest.skipIf(not sapi.is_slurm_available(), "SLURM client not available")
class TestSlurm(unittest.TestCase):
    slurm_args = None

    def setUp(self) -> None:
        TestSlurm.slurm_args = SlurmArgs({
            "output": "/dev/null",
            "error": "/dev/null",
        })
        account = os.environ.get('ACCOUNT', None)
        if account:
            TestSlurm.slurm_args.add_arg('A', account)
        partition = os.environ.get('PARTITION', None)
        if partition:
            TestSlurm.slurm_args.add_arg('p', partition)

    def xxx_test_sbatch(self):
        id = sapi.sbatch(TestSlurm.slurm_args, ['/usr/bin/cat /proc/cpuinfo'])
        while True:
            state = sapi.get_job_state(id)
            if state is not None and not state['running']:
                break
        self.assertEqual(state['exit_code'], 0)
        self.assertEqual(state['signal'], 0)

    def test_jobs(self):
        slurm = Slurm(TestSlurm.slurm_args)
        job = slurm.create_job("foo")
        job.add_command('/usr/bin/cat /proc/cpuinfo')
        job.run()
        self.assertIsNotNone(job.get_id())

        while job.is_running(state_timeout=1):
            time.sleep(0.1)

        self.assertFalse(job.is_running())
        self.assertFalse(job.failed())

    def test_jobs_with_serialization(self):
        tmpdir = tempfile.TemporaryDirectory()
        tmpfile = tmpdir.name + '/slurm.json'

        slurm = Slurm(TestSlurm.slurm_args)
        slurm.set_serialization_file(tmpfile)
        job = slurm.create_job("foo")
        job.add_command('/usr/bin/cat /proc/cpuinfo')
        job.run()
        slurm.save_json()

        slurm2 = Slurm()
        slurm2.set_serialization_file(tmpfile)
        slurm2.load_json()
        job2 = slurm2.get_job("foo")
        self.assertIsNotNone(job2)
        self.assertEqual(job2.get_name(), "foo")
        self.assertEqual(job2.get_id(), job.get_id())

        while job2.is_running(state_timeout=1):
            time.sleep(0.1)

        self.assertFalse(job2.is_running())
        self.assertFalse(job2.failed())

        tmpdir.cleanup()


if __name__ == '__main__':
    unittest.main()
