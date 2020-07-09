import itertools

from google.protobuf.descriptor_pb2 import DescriptorProto


def collect_definitions(proto_file):
    return itertools.chain(
        traverse(proto_file.package, proto_file.enum_type),
        traverse(proto_file.package, proto_file.message_type),
        traverse(proto_file.package, proto_file.service)
    )


def traverse(package, items):
    for item in items:
        yield item, package

        if isinstance(item, DescriptorProto):
            for enum in item.enum_type:
                yield enum, f'{package}.{item.name}'

            for nested in item.nested_type:
                nested_package = f'{package}.{item.name}'

                for nested_item, _ in traverse(nested_package, [nested]):
                    yield nested_item, nested_package
