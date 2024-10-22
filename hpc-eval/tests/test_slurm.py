import unittest
import os
import slurm.api as sapi
from slurm.args import SlurmArgs


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

    def test_sbatch(self):
        id = sapi.sbatch(TestSlurm.slurm_args, ['/usr/bin/cat /proc/cpuinfo'])
        while True:
            state = sapi.get_job_state(id)
            if state is not None and not state['running']:
                break
        self.assertEqual(state['exit_code'], 0)
        self.assertEqual(state['signal'], 0)


if __name__ == '__main__':
    unittest.main()
