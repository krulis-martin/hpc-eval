from commands.submit import Submit
from commands.default import Default

commands = {
    Default.get_name(): Default(),
    Submit.get_name(): Submit(),
}


def get_command(args: list):
    if len(args) > 0 and args[0] in commands:
        name = args.pop(0)
        return commands[name]

    return Default()


__all__ = [get_command]
