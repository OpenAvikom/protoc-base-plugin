import sys
import json
import itertools
import importlib
import pickle
import re
import select
from pathlib import Path
from os.path import splitext, abspath, exists

from google.protobuf.compiler import plugin_pb2 as plugin
from google.protobuf.descriptor_pb2 import DescriptorProto, EnumDescriptorProto, ServiceDescriptorProto

from .builder import build_tree, inject_docs
from .utils import parse_parameters


class ParserBase:

    def __init__(self, comments=False, options=False, skip_dependencies=True, test_request='request.pkl'):
        self.with_comments = comments
        self.with_options = options
        self.skip_dependencies = skip_dependencies
        self.test_request = test_request

    @staticmethod
    def get_filename(proto_name: str) -> str:
        raise NotImplementedError("A Parser needs to override 'get_filename' to determine the target file name")

    def process_raw(self, data):        
        return data

    def load_request(self):        
        if select.select([sys.stdin,], [], [], 0.1)[0]:
            data = sys.stdin.buffer.read()
        else:
            if self.test_request and exists(self.test_request):
                with open(self.test_request, 'rb') as f:
                    return pickle.load(f)
            raise RuntimeError("No data to process since test_request does not exist "
                               "and no data provided on stdin.")
 
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

        return request

    def parse(self):
        request = self.load_request()
        self.process(request)

    def process(self, request):
        response = plugin.CodeGeneratorResponse()
        for proto_file in request.proto_file:
            if self.skip_dependencies and proto_file.name not in request.file_to_generate:
                continue
            result = build_tree(proto_file, self.with_options)
            if self.with_comments:
                inject_docs(proto_file, result['definitions'])

            result = self.process_raw(result)

            # Fill response
            f = response.file.add()
            f.name = self.get_filename(proto_file.name)
            f.content = result
        output = response.SerializeToString()
        sys.stdout.buffer.write(output)
