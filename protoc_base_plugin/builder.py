import re
import sys
from os.path import splitext

from google.protobuf.descriptor_pb2 import DescriptorProto, EnumDescriptorProto, ServiceDescriptorProto

from .collect import collect_definitions
from .utils import parse_options, generate_docs


replacer = re.compile(r'^[\s\/\*]+')


def build_tree(proto_file, with_options=False):        
    definitions = []
    # Parse request
    for item, package_name in collect_definitions(proto_file):
        data = {
            'package': package_name or '&lt;root&gt;',
            'filename': proto_file.name,
            'name': item.name,
        }

        if isinstance(item, DescriptorProto):
            fields = []
            for field_descriptor in item.field:
                field = {
                    'name': field_descriptor.name,
                    'type': str(field_descriptor.Type.keys()[field_descriptor.type - 1]),
                    'label': str(field_descriptor.Label.keys()[field_descriptor.label - 1])}
                if with_options and field_descriptor.options.ByteSize():
                    field['options'] = parse_options(field_descriptor.options)
                fields.append(field)
            data.update({
                'type': 'Message',
                'fields': fields
            })

        elif isinstance(item, EnumDescriptorProto):
            data.update({
                'type': 'Enum',
                'values': [{'name': v.name, 'value': v.number}
                            for v in item.value]
            })

        elif isinstance(item, ServiceDescriptorProto): 
            data.update({
                'type': 'Service',
                'methods': [{'name': v.name, 'input_type': v.input_type[1:], 'output_type': v.output_type[1:] }
                            for v in item.method]
            })

        if with_options and item.options.ByteSize():
            data['options'] = parse_options(item.options)
        definitions.append(data)

    output = { 'definitions': definitions, 'filename': proto_file.name }
    if with_options and proto_file.options.ByteSize():
        output['options'] = parse_options(proto_file.options)
    return output


def inject_docs(proto_file, definitions):
    for comment in generate_docs(proto_file):
        if comment is None:
            continue
        package, message = splitext(comment['name'])
        for elem in definitions:
            if elem['package'] == package and elem['name'] == message[1:]:
                if 'docstring' in comment:
                    elem['comment'] = replacer.sub('', comment['docstring']).strip()
                for name, value in comment.get('fields', {}).items():
                    for target in elem.get('fields', []) or elem.get('values', []) or elem.get('methods', []):
                        if target['name'] == name:
                            target['comment'] = replacer.sub('', value['docstring']).strip()
                    else:
                        ValueError(f"Dont know field '{name}' of '{comment['name']}'")
                break
        else:
            raise ValueError(f"no message '{comment['name']}' has been parsed!")
