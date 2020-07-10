import re

re_capitalize = re.compile(r"(^\s*|\W+)(\w)")
re_camel_case = re.compile(r"_(\w)")
re_underscore_notation = re.compile(r"([a-z])([A-Z])")


def parse_parameters(parameters, assert_key=None):
    key, value = parameters.split("=")
    if assert_key:
        assert key == assert_key
    return value


def Capitalize(input_string):
    return re_capitalize.sub(
        lambda pat: pat.group(1) + pat.group(2).upper(), input_string
    )


def camelCase(input_string):
    return re_camel_case.sub(lambda pat: pat.group(1).upper(), input_string)


def PascalCase(input_string):
    if input_string.upper() == input_string:
        return input_string
    return Capitalize(camelCase(input_string))


def underscore_notation(input_string):
    input_string = input_string[0].lower() + input_string[1:]
    return re_underscore_notation.sub(
        lambda pat: pat.group(1) + "_" + pat.group(2).lower(), input_string
    )
