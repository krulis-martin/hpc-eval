import sys
from loguru import logger
import config.descriptors as cd


def sink_postprocessor(path, base_file, _):
    if type(path) is str and path.startswith('@'):
        return path  # avoid normalizing @stdout and @stderr

    return cd._normalize_path(path, base_file, _)


class LogInit:
    '''
    Wrapper that initializes loguru logger globally. The config parameters are directly injected into
    add() method that initializes sinks.
    https://loguru.readthedocs.io/en/stable/api/logger.html
    '''
    _config = cd.List(
        cd.Dictionary({
            'sink': cd.String('@stdout', '@stdout, @stderr, or a path to a file').set_postprocessor(sink_postprocessor),
            'level': cd.String('INFO', 'Logging level filter (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)')
                .enum(['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']),
            'colorize': cd.Bool(True, 'Whether to allow color output.'),
            'format': cd.String('{level}: {message}', 'Formatting pattern.'),
            'serialize': cd.Bool(False, 'Whether to serialize log records into JSON.'),
            'backtrace': cd.Bool(False, 'Whether the exception trace should include stack.'),
            'rotation': cd.String(None, 'Rotation condition for a file sink (only strings are allowed).'),
            'retention': cd.String(None, 'Retention directive for a file sink (only strings are allowed).'),
            'compression': cd.String(None, 'Compression used for a file sink (zip, gz, bz2, ...).'),
        }, {}, 'A conveninet subset of loguru parameters (https://loguru.readthedocs.io/en/stable/api/logger.html)'),
        [], 'List of sinks to be added to logger (if empty, app default will be used).'
    )

    @staticmethod
    def get_config_schema():
        '''
        Return configuration descriptor for this component.
        '''
        return __class__._config

    def _add_default(self):
        cut_level = logger.level('ERROR').no
        logger.add(sys.stdout, format='{message}', level='INFO', filter=lambda r: r['level'].no < cut_level)
        logger.add(sys.stderr, format='<lvl>{level}:</lvl> {message}', level=cut_level, colorize=True)

    def __init__(self, config: list[dict] = {}):
        logger.remove()  # reset first
        if config:
            for cfg in config:
                # each record is one sink
                sink = cfg.pop('sink')
                if not sink or sink == '@stdout':
                    sink = sys.stdout
                elif sink == '@stderr':
                    sink = sys.stderr

                # Remove parameters with None values
                cfg = {key: val for key, val in cfg.items() if val is not None}
                logger.add(sink, **cfg)

        else:
            self._add_default()
