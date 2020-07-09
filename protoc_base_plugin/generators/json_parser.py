import json

from ..parser import ParserBase


class JsonParser(ParserBase):
    def process_raw(self, data):
        return json.dumps(data, indent=2)

    @staticmethod
    def get_filename(proto_name: str) -> str:
        return proto_name.replace(".proto", ".json")


def main():
    JsonParser().parse()
