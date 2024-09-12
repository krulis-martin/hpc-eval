from commands.add_user import AddUser
from commands.default import Default
from commands.submit import Submit

commands = {
    Default.get_name(): Default(),
    Submit.get_name(): Submit(),
    AddUser.get_name(): AddUser(),
}


def get_command(args: list):
    if len(args) > 0 and args[0] in commands:
        name = args.pop(0)
        return commands[name]

    return Default()


__all__ = [get_command]
