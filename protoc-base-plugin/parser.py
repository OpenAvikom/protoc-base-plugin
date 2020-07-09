import sys
import json
import itertools
import importlib
import pickle
import re
from pathlib import Path
from os.path import splitext, abspath

from google.protobuf.compiler import plugin_pb2 as plugin
from google.protobuf.descriptor_pb2 import DescriptorProto, EnumDescriptorProto, ServiceDescriptorProto

from .builder import build_tree, inject_docs


class ParserBase:

    def __init__(self, comments=False, options=False, skip_dependencies=True):
        self.with_comments = comments
        self.with_options = options
        self.skip_dependencies = skip_dependencies

    def get_filename(self, proto_name):
        raise NotImplementedError("A Parser needs to override 'get_filename' to determine the target file name")

    def process_raw(self, data):
        pass

    def parse(self):
        data = sys.stdin.buffer.read()
        request = plugin.CodeGeneratorRequest()
        request.ParseFromString(data)

        if self.with_options:
            try:
                pb2_root = abspath(parse_parameters(request.parameter))
                sys.path.append(pb2_root)
                for path in Path(pb2_root).rglob('*pb2.py'):
                    module_name, _ = splitext(path)
                    module_name = module_name[len(pb2_root)+1:].replace('/', '.')
                    spec = importlib.util.spec_from_file_location(module_name, path)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                # reload 
                request.ParseFromString(data)
            except ValueError:
                pass

        self.process(request)

    def process(self, request):
        for proto_file in request.proto_file:
            if self.skip_dependencies and proto_file.name not in request.file_to_generate:
                continue
            result = build_tree(proto_file, self.with_options)
            if self.with_comments:
                inject_docs(proto_file, result['definitions'])

            result = self.process_raw(result)
            response = plugin.CodeGeneratorResponse()

            # Fill response
            f = response.file.add()
            f.name = self.get_filename(proto_file.name)
            f.content = result
            # f.content = json.dumps(result, indent=2)
