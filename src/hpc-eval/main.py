import sys
import json
import jsonschema


def parse_args(args):
    print(args)


def main():
    """
    Main entry point of HPC-eval CLI tool.
    """
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

    parse_args(sys.argv)

    # with open('schema.json') as fp:
    #    schema = json.load(fp)
    # with open('instance.json') as fp:
    #    data = json.load(fp)

    # res = jsonschema.validate(data, schema)
    # print(res)
