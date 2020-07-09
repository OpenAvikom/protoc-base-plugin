import json

from ..parser import ParserBase


class JsonParser(ParserBase):

    def process_raw(self, data):
        return json.dumps(data, indent=2)


def main():
    parser = JsonParser()
    parser.parse()
