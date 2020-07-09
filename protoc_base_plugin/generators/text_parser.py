from ..parser import ParserBase


class TextParser(ParserBase):

    field_template = """
FIELD: {parsed_comment}
    name={name}
    type={type}

    OPTIONS:
{parsed_options}"""

    value_template = """
VALUE: {parsed_comment}
    name={name}"""

    method_template = """
METHOD: {parsed_comment}
    name={name}
    receives={input_type}
    returns={output_type}"""

    message_template = """
{parsed_comment}
MESSAGE:
    name={name}
    OPTIONS [
{parsed_options}
]
{parsed_fields}
"""

    enum_template = """
{parsed_comment}
ENUM:
    name={name}
{parsed_fields}
"""

    service_template = """
{parsed_comment}
SERVICE:
    name={name}
{parsed_fields}
"""

    meta_template = """
DESCRIPTION: {parsed_comment}
    file={filename}

    OPTIONS:
{parsed_options}
{parsed_definitions}
"""

    field_comment_template = "<-- {comment}"
    definition_comment_template = "/**\n{comment}\n*/"
    meta_comment_template = "<-- {comment}"

    field_option_template = "{name}={value}"
    definition_option_template = "{name}={value}"
    meta_option_template = "{name}={value}"
