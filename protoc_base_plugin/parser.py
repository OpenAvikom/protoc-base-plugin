import sys
import json
import itertools
import importlib
import pickle
import re
import select
from textwrap import indent
from pathlib import Path
from os.path import splitext, abspath, exists

from google.protobuf.compiler import plugin_pb2 as plugin
from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    EnumDescriptorProto,
    ServiceDescriptorProto,
)

from .builder import build_tree, inject_docs
from .utils import parse_parameters


class ParserBase:

    field_comment_template = ""
    field_option_template = ""
    field_template = ""
    value_template = ""
    method_template = ""
    definition_comment_template = ""
    definition_option_template = ""
    message_template = ""
    service_template = ""
    enum_template = ""
    meta_comment_template = ""
    meta_option_template = ""
    meta_template = ""
    indent_level = 4
    indent_char = " "

    def __init__(
        self,
        comments=False,
        options=False,
        skip_dependencies=True,
        test_request="request.pkl",
    ):
        self.with_comments = comments
        self.with_options = options
        self.skip_dependencies = skip_dependencies
        self.test_request = test_request
        self._definition_template_map = dict(
            Enum=self.enum_template,
            Message=self.message_template,
            Service=self.service_template,
        )
        self._field_template_map = dict(
            Enum=self.value_template,
            Message=self.field_template,
            Service=self.method_template,
        )

    @staticmethod
    def get_filename(proto_name: str) -> str:
        return None

    def process_raw(self, data):
        meta = {"filename": data.get("filename"), "options": data.get("options", {})}
        definitions_output = []
        for definition in data.get("definitions", []):
            current_definition = {
                "package": definition.get("package"),
                "filename": definition.get("filename"),
                "name": definition.get("name"),
                "type": definition.get("type"),
            }
            fields_output = []
            for field in definition.get(
                "fields", definition.get("values", definition.get("methods", []))
            ):
                field["type"] = field.get("type", None)
                fields_output.append(
                    self.process_field(
                        field,
                        current_definition,
                        meta,
                        self._field_template_map[definition.get("type")],
                    )
                )

            definitions_output.append(
                self.process_definition(
                    definition,
                    meta,
                    fields_output,
                    self._definition_template_map[definition.get("type")],
                )
            )

        return self.process_meta(meta, definitions_output)

    def process_field_options(self, options):
        parsed_options = []
        for option in flat_dict(options):
            if isinstance(option["value"], dict):
                continue
            parsed_options.append(self.field_option_template.format(**option))
        return parsed_options

    def process_field(self, field, definition, meta, template):
        parsed_options = self.process_field_options(field.get("options", {}))
        comment = field.get("comment")
        comment = self.field_comment_template.format(comment=comment) if comment else ""
        return template.format(
            parsed_options=indent(
                "\n".join(parsed_options), self.indent_char * self.indent_level * 2
            ),
            parsed_comment=comment,
            **field,
        )

    def process_definition_options(self, options):
        parsed_options = []
        for option in flat_dict(options):
            parsed_options.append(self.definition_option_template.format(**option))
        return parsed_options

    def process_definition(self, definition, meta, parsed_fields, template):
        parsed_options = self.process_definition_options(definition.get("options", {}))
        comment = definition.get("comment")
        comment = (
            self.definition_comment_template.format(comment=comment) if comment else ""
        )
        return template.format(
            parsed_fields=indent(
                "\n".join(parsed_fields), self.indent_char * self.indent_level
            ),
            parsed_options=indent(
                "\n".join(parsed_options), self.indent_char * self.indent_level * 2
            ),
            parsed_comment=comment,
            **definition,
        )

    def process_meta_options(self, options):
        parsed_options = []
        for option in flat_dict(options):
            parsed_options.append(self.meta_option_template.format(**option))
        return parsed_options

    def process_meta(self, meta, parsed_definitions):
        parsed_options = self.process_meta_options(meta.get("options", {}))
        comment = meta.get("comment")
        comment = self.meta_comment_template.format(comment=comment) if comment else ""
        return self.meta_template.format(
            parsed_definitions=indent(
                "\n".join(parsed_definitions), self.indent_char * self.indent_level
            ),
            parsed_options=indent(
                "\n".join(parsed_options), self.indent_char * self.indent_level * 2
            ),
            parsed_comment=comment,
            **meta,
        )

    def load_request(self):
        if select.select([sys.stdin,], [], [], 0.1)[0]:
            data = sys.stdin.buffer.read()
        else:
            if self.test_request and exists(self.test_request):
                with open(self.test_request, "rb") as f:
                    data = pickle.load(f)
            else:
                raise RuntimeError(
                    "No data to process since test_request does not exist "
                    "and no data provided on stdin."
                )

        request = plugin.CodeGeneratorRequest()
        request.ParseFromString(data)

        if self.with_options:
            try:
                pb2_root = abspath(parse_parameters(request.parameter))
                sys.path.append(pb2_root)
                for path in Path(pb2_root).rglob("*pb2.py"):
                    module_name, _ = splitext(path)
                    module_name = module_name[len(pb2_root) + 1 :].replace("/", ".")
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
            if (
                self.skip_dependencies
                and proto_file.name not in request.file_to_generate
            ):
                continue
            result = build_tree(proto_file, self.with_options)
            if self.with_comments:
                inject_docs(proto_file, result["definitions"])

            result = self.process_raw(result)

            # Fill response
            file_name = self.get_filename(proto_file.name)
            if file_name and result:
                f = response.file.add()
                f.name = file_name
                f.content = result

            output = response.SerializeToString()
            self.process_output(output)

    @staticmethod
    def process_output(output):
        sys.stdout.buffer.write(output)


def flat_dict(dictionary, prefix=[]):
    res = []
    for key, value in dictionary.items():
        pre = prefix + [key]
        res.append({"name": "_".join(pre), "value": value})
        if isinstance(value, dict):
            res.extend(flat_dict(value, pre))
    return res
