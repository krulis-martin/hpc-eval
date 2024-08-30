import sys
import argparse
from commands import get_command


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assignments', help='')
    return parser.parse_args(sys.argv)


def main():
    """
    Main entry point of HPC-eval CLI tool.
    """
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

    args = sys.argv[:]
    command = get_command(args)
    command.parse_args(args)

    # todo load config

    command.execute()
    # args = parse_args()

    # with open('schema.json') as fp:
    #    schema = json.load(fp)
    # with open('instance.json') as fp:
    #    data = json.load(fp)

    # res = jsonschema.validate(data, schema)
    # print(res)
