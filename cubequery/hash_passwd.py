import sys
import bcrypt
"""
A simple tool to bcrypt a password passed as arg 1 
This can be used to create the password to put into the user.cfg file
"""
if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("need a string to hash")
        sys.exit(1)

    password = bytes(sys.argv[1], "utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)

    print(hashed.decode("utf-8"))
