import sys
import pickle

from ..parser import ParserBase, plugin
from ..utils import parse_parameters


class NullParser(ParserBase):

    def __init__(self):
        super().__init__()

    def parse(self):
        request = self.load_request()
        try:
            pkl_path = parse_parameters(request.parameter, 'pkl_path')
            with open(pkl_path, 'wb') as f:
                pickle.dump(request, f)
        except AssertionError:
            pass


def main():
    NullParser().parse()
