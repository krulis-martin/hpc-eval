from slurm.args import SlurmArgs
import subprocess


def is_slurm_available() -> bool:
    '''
    Check whether a slurm client (CLI commands) is available.
    '''
    result = subprocess.run('which sbatch', shell=True, stdout=subprocess.PIPE)
    if result.returncode != 0:
        return False

    result = subprocess.run('which scancel', shell=True, stdout=subprocess.PIPE)
    if result.returncode != 0:
        return False

    result = subprocess.run('which sacct', shell=True, stdout=subprocess.PIPE)
    if result.returncode != 0:
        return False

    return True


def sbatch(args: SlurmArgs, commands: list) -> int:
    '''
    Construct and execute a slurm job via sbatch.
    Slurm args and list of commands (a script) are used as input.
    Job id is returned.
    '''

    # assemble the script
    cmd = ['sbatch << EOF', '#!/bin/sh']
    cmd.extend(args.generate_sbatch_directives())
    cmd.extend(commands)
    cmd.append('EOF')

    # execute and verify sbatch response
    result = subprocess.run('\n'.join(cmd), shell=True, stdout=subprocess.PIPE)
    assert result.returncode == 0, result.stderr
    stdout = result.stdout.decode('utf-8')
    assert 'Submitted batch job' in stdout, result.stderr

    return int(stdout.split(' ')[3])  # return job id


def scancel(job_id: int) -> None:
    result = subprocess.run(
        f'scancel {job_id}', shell=True, stdout=subprocess.PIPE)
    assert result.returncode == 0, result.stderr


def get_job_states(job_ids: list) -> dict:
    '''
    Return state information for given set of jobs.
    Return dict (key is job id), each value is dict containing
    state, running, [exit_code], and [signal]
    '''
    # -b brief (staus+exit code), -n no header, -P parseable output
    # -X only the main job (no steps), -j job id
    cmd = f'sacct -bnPX -j {','.join(map(str, job_ids))}'
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    assert result.returncode == 0, result.stderr

    res = {id: None for id in job_ids}
    output = result.stdout.decode('utf-8').strip().split('\n')
    for line in output:
        if not line:
            continue

        tokens = line.split('|')
        assert len(tokens) == 3, f'Unexpected sacct output "{line}"'
        id, state, exit_code_and_signal = tokens

        # id needs to be converted to int
        if not id.isdigit():
            continue
        id = int(id)

        if id not in res:
            continue

        running = state in ['PENDING', 'RUNNING', 'REQUEUED', 'RESIZING', 'SUSPENDED']

        res_state = {"state": state, "running": running}
        if not running:
            res_state["exit_code"], res_state["signal"] = exit_code_and_signal.split(':')
            if res_state["exit_code"].isdigit():
                res_state["exit_code"] = int(res_state["exit_code"])
            if res_state["signal"].isdigit():
                res_state["signal"] = int(res_state["signal"])

        res[id] = res_state

    return res


def get_job_state(job_id: int) -> dict | None:
    '''
    Shorthand for retrieving state of a single job.
    '''
    res = get_job_states([job_id])
    return res.get(job_id)
