import bcrypt
import logging

from cubequery import ipaddress_matching

_users = {}


def load_users():
    # TODO: create a real user db that is easier for people to update. This will do for mvp but should be better later.
    # already loaded users don't try again.
    if len(_users) > 0:
        return

    with open("users.cfg", 'r') as f:
        for line in f:
            stripped = line.strip()
            if not stripped.startswith('#'):  # skip comments
                parts = stripped.split(',', 3)
                address_list = []
                if len(parts) > 2:
                    address_list = parts[2].split(';')

                _users[parts[0]] = (bytes(parts[1], "utf-8"), address_list)


def check_user(username, password, ip_address):
    """
    validate a user in the user list

    :param username: the username to check
    :param password: password to check
    :param ip_address: of the incoming connection to check
    :return: true if and only if the user in the password list and the provided password matches.
    """

    load_users()
    try:
        if _users[username]:
            if ipaddress_matching.match_list(_users[username][1], ip_address):
                return bcrypt.checkpw(bytes(password, "utf-8"), _users[username][0])
    except Exception as e:
        logging.warning(f'User validation error :: {e}')
    return False
