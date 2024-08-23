class SlurmArgs:
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

    def __init__(self, defaults=None):
        '''
        Optionally, the constructor receives default args, which may be
        an instance of SlurmArgs or a dict { name: value }.
        '''
        if defaults and isinstance(defaults, SlurmArgs):
            self.args = defaults.args.copy()
        elif defaults:
            if type(defaults) is not dict:
                raise Exception(
                    "Defaults must be SlurmArgs instance or a dictionary.")
            for name, value in defaults.items():
                self.add_arg(name, value)
        else:
            self.args = {}

    def has_arg(self, name: str) -> bool:
        '''
        Check whether given argument was set.
        '''
        if name in SlurmArgs.short_args:
            name = SlurmArgs.short_args[name]
        return name in self.args

    def get_arg_value(self, name: str):
        '''
        Return value of given argument (None is returned for options).
        '''
        if not self.has_arg(name):
            raise Exception(f"Argument {name} is not set.")

        if name in SlurmArgs.short_args:
            name = SlurmArgs.short_args[name]
        return self.args[name]

    def add_arg(self, name: str, value=None) -> None:
        '''
        Internal method for adding arguments. Supports both short and long
        names. Value is verified based on the known args specification.
        Note that short names are translated to long names immediately.
        '''
        if name in SlurmArgs.short_args:
            name = SlurmArgs.short_args[name]
        if name not in SlurmArgs.known_args:
            raise Exception(
                "SLURM argument '{}' is not recognized".format(name))

        verifier = SlurmArgs.known_args[name]
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

    def generate_sbatch_directives(self) -> list:
        '''
        Generate list of strings (sbatch rows) with directives adding the args.
        '''
        res = []
        for name, value in self.args.items():
            directive = '#SBATCH --' + name
            if value is not None:
                directive += '="{}"'.format(str(value).replace("\\",
                                            "\\\\").replace('"', '\\"'))
            res.append(directive)
        return res
