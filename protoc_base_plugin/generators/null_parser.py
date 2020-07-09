import sys
import pickle

from ..parser import ParserBase, plugin
from ..utils import parse_parameters


class NullParser(ParserBase):
    def __init__(self):
        super().__init__()

    def parse(self):
        try:
            data = sys.stdin.buffer.read()
            with open("./request.pkl", "wb") as f:
                pickle.dump(data, f)
        except AssertionError:
            pass


def main():
    NullParser().parse()
