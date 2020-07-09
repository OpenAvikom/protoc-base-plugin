import textwrap


def extract_comments(proto_file):
    if proto_file.source_code_info.ByteSize():
        info = proto_file.source_code_info
        for loc in info.location:
            if loc.trailing_comments or loc.leading_comments:
                if loc.path[0] not in [
                    4,
                    5,
                    6,
                ]:  # parses messages (4), enums (5), services (6)
                    continue
                comment = textwrap.dedent(
                    f"{loc.leading_comments}\n{loc.trailing_comments}"
                )
                yield parse_path(
                    docstring=comment, path=list(loc.path), proto_file=proto_file
                )


def parse_path(proto_file, path, docstring, data=None):
    """
    Resolves path and find the related proto file field.
    Args:
        proto_file (FileDescriptorProto): The currently processed proto file.
        path (list[int]): The field path of the found docstring
        docstring (str): The docstring to attach
    Returns:
        dict: A map data structure with resolved element names and docstrings
    """
    field_name = ""
    for field in [i[0] for i in proto_file.ListFields()]:
        if field.number == path[0]:
            field_name = field.name
            break
    else:
        raise AttributeError(
            f"Cannot find field with number {path[0]} in {proto_file.fields}."
        )

    # The pattern is usually [Class, field, Class, field].
    # path[1] should refere to the field that needs to be investigated.
    # If we cannot find the field, we give up silently.
    try:
        field = getattr(proto_file, field_name)[path[1]]
    except TypeError:  # pragma: NO COVER
        return  # pragma: NO COVER

    path = path[2:]

    # during the initial run, define a new data object
    if not data:
        data = dict(
            name="{pkg}.{name}".format(name=field.name, pkg=proto_file.package,)
        )

    # if the path refere to a nested element of the current
    if len(path) >= 2:

        # For nested definitions wee need to add the current element's name for the package name.
        if not data["name"].endswith(field.name):
            data = dict(
                name="{parent}.{child}".format(child=field.name, parent=data["name"],)
            )
        return parse_path(field, path, docstring, data)

    # Attach docstring to the data object. The position depends on whether the path
    # ends at a class (Message, Enum, Service) or a field/value/method of it.
    # For fields/values and enums we assume no mixed case.
    if data["name"].endswith(field.name):
        data["docstring"] = docstring
    elif _is_mixed_case(field.name) and not hasattr(field, "input_type"):
        data = dict(
            name="{parent}.{name}".format(name=field.name, parent=data["name"],)
        )
        data["docstring"] = docstring
    else:
        if "fields" not in data:
            data["fields"] = {}
        data["fields"][field.name] = {"docstring": docstring}

    return data


def _is_mixed_case(string):
    return not (string == string.lower() or string == string.upper())
