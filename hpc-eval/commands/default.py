import argparse


class Default:
    '''
    Default command performs all the steps of evaluation (download, build, test, save results).
    '''

    def __init__(self):
        pass

    def parse_args(self, args: list):
        parser = argparse.ArgumentParser()
        parser.add_argument('--assignments', help='')
        self.args = parser.parse_args(args)

    def execute():
        pass
