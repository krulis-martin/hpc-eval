from commands.submit import Submit
from commands.default import Default

commands = {
    "submit": Submit(),
    # "evaluate": None,
    # "results": None,
}


def get_command(args: list):
    if len(args) > 1 and args[1] in commands:
        name = args[1]
        del args[1]
        return commands[name]

    return Default()


__all__ = [get_command]
