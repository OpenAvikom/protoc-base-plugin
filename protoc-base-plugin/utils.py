

def parse_options(options):
    if hasattr(options, "ListFields"):
        return {extension.name: parse_options(option) for extension, option in options.ListFields()}
    else:
        return options


def parse_parameters(parameters):
    key, value = parameters.split('=')
    assert(key == 'pb2_root')
    return value


def generate_docs(proto_file):
    if proto_file.source_code_info.ByteSize():
        import textwrap
        info = proto_file.source_code_info
        for loc in info.location:
            if not loc.trailing_comments and not loc.leading_comments:
                continue
            if loc.path[0] not in [4, 5, 6]:  # parses messages (4), enums (5), services (6)
                continue
            comment = textwrap.dedent(f'{loc.leading_comments}\n{loc.trailing_comments}')
            yield parse_path(docstring=comment, path=list(loc.path), struct=proto_file)


def parse_path(struct, path, docstring, message_structure=None):
    # The first two ints in the path represent what kind of thing
    # the comment is attached to (message, enum, or service) and the
    # order of declaration in the file.
    #
    # e.g. [4, 0, ...] would refer to the *first* message, [4, 1, ...] to
    # the second, etc.
    field_name = ''
    for field in [i[0] for i in struct.ListFields()]:
        if field.number == path[0]:
            field_name = field.name
            break

    # Comments over message options don't have a well-defined meaning in
    # terms of generated documentation, and parsing them is difficult,
    # so we just don't try.
    try:
        child = getattr(struct, field_name)[path[1]]
    except TypeError:  # pragma: NO COVER
        return         # pragma: NO COVER

    path = path[2:]

    # # Ignore enums.
    # #
    # # We ignore enums because there is no valid insertion point for them,
    # # and protoc will not write anything if we offer any invalid
    # # insertion point, and there does not seem to be any graceful
    # # fallback available (nor is there a way to get a list of insertion
    # # points to check against).
    # if child.DESCRIPTOR.name == 'EnumDescriptorProto':
    #     return

    # If applicable, create the MessageStructure object for this.
    if not message_structure:
        message_structure = dict(
            name='{pkg}.{name}'.format(
                name=child.name,
                pkg=struct.package,
            ))

    # If the length of the path is 2 or greater, call this method
    # recursively.
    if len(path) >= 2:
        # Nested types are possible.
        #
        # In this case, we need to ensure that we do not lose
        # the outer layers of the nested type name; otherwise the
        # insertion point name will be wrong.
        if not message_structure['name'].endswith(child.name):
            message_structure = dict(
                name='{parent}.{child}'.format(
                    child=child.name,
                    parent=message_structure['name'],
                ))
        return parse_path(child, path, docstring, message_structure)

    # Write the documentation to the appropriate spot.
    # This entails figuring out what the Message (basically the "class")
    # is, and then whether this is class-level or property-level
    # documentation.
    if message_structure['name'].endswith(child.name):
        message_structure['docstring'] = docstring
    elif _is_mixed_case(child.name) and not hasattr(child, 'input_type'):
        message_structure = dict(
            name='{parent}.{name}'.format(
                name=child.name,
                parent=message_structure['name'],
            ))
        message_structure['docstring'] = docstring
    else:
        if 'fields' not in message_structure:
            message_structure['fields'] = {}
        message_structure['fields'][child.name] = {'docstring': docstring}

    # If the length of the path is now 1...
    #
    # This seems to be a corner case situation. I am not sure what
    # to do for these, and the documentation for odd-numbered paths
    # does not match my observations.
    #
    # Punting. Most of the docs are better than none of them, which was
    # the status quo ante before I wrote this.
    if len(path) == 1:
        return message_structure

    # Done! Return the message structure.
    return message_structure

def _is_mixed_case(string):
    return not (string == string.lower() or string == string.upper())
