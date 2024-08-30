import argparse


class Submit:
    '''
    Submit command that loads new solution into submit queue.
    '''

    def parse_args(self, args: list):
        parser = argparse.ArgumentParser()
        parser.add_argument('--assignments', help='')
        self.args = parser.parse_args(args)

    def execute():
        pass
