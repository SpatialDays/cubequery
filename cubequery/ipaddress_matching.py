

def match(pattern, address):
    """
    Match ip address patterns.
    This is not regex.
    A star at the end of a ip address string does prefix matching.
    None or a blank string matches any address

    match('192.168.0.1', '192.168.0.1') == True
    match('192.168.0.2', '192.168.0.1') == False
    match('192.168.*', '192.168.23.56') == True
    match('192.168.0.*', '192.168.0.1') == True
    match('192.168.0.*', '192.168.0.35') == True
    match('193.*', '192.168.0.1') == False

    :param pattern: pattern to match against.
    :param address: the address to check
    :return: True if the address matches the pattern.
    """
    if not pattern or pattern == "":
        return True

    if pattern.endswith('*'):
        return address.startswith(pattern[:-1])
    else:
        return pattern == address


def match_list(patterns, address):
    """
    Match an address against a list of patterns.

    See match(pattern, address) for details of matching

    :param patterns: a list of patterns to match against.
    :param address: the address to check
    :return: True if the provided address matches any of the patterns.
    """
    for p in patterns:
        if match(p, address):
            return True
    return False
