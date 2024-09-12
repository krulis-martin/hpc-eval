import sys
from loguru import logger
from commands import get_command


def main():
    """
    Main entry point of HPC-eval CLI tool.
    """
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

    # find the selected command object and fill it with args
    args = sys.argv[1:]
    command = get_command(args)
    command.parse_args(args)

    # load configuration and instantiate components (this should also initialize logger)
    command.load_config()  # TODO handle failure

    try:
        logger.debug("Loading current state.")
        command.load_state()

        # Finally, let's do what is expected of us!
        logger.debug(f"Executing command '{command.get_name()}' with args '{args}'")
        command.execute()
    except Exception as e:
        logger.exception(e)

    command.save_state()
