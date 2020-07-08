#!/usr/bin/env python

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

from .builder import build_tree


def generate_code(request, response):
    for proto_file in request.proto_file:
        if proto_file.name not in request.file_to_generate:
            continue
        result = build_tree(proto_file)
        # Fill response
        f = response.file.add()
        f.name = proto_file.name.replace('.proto', '.json')
        f.content = json.dumps(result, indent=2)


def main():
    # # Read request message from stdin
    # data = sys.stdin.buffer.read()
    # request = plugin.CodeGeneratorRequest()
    # request.ParseFromString(data)

    # try:
    #     pb2_root = abspath(parse_parameters(request.parameter))
    #     sys.path.append(pb2_root)
    #     for path in Path(pb2_root).rglob('*pb2.py'):
    #         module_name, _ = splitext(path)
    #         module_name = module_name[len(pb2_root)+1:].replace('/', '.')
    #         spec = importlib.util.spec_from_file_location(module_name, path)
    #         mod = importlib.util.module_from_spec(spec)
    #         spec.loader.exec_module(mod)
    #     # reload 
    #     request.ParseFromString(data)
    # except ValueError:
    #     pass

    # with open('dump.pkl', 'wb') as f:
    #     pickle.dump(request, f)

    sys.path.append('./proto')
    import avikom.generic.options_pb2
    with open('dump.pkl', 'rb') as f:
        request = pickle.load(f)

    # Create response
    response = plugin.CodeGeneratorResponse()

    # Generate code
    generate_code(request, response)

    # Serialise response message
    output = response.SerializeToString()
    # Write to stdout
    sys.stdout.buffer.write(output)

if __name__ == '__main__':
    main()
