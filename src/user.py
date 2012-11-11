from __future__ import print_function

import re
import hmac
from random import choice
#pylint: disable=W0402
from string import ascii_letters
from hashlib import sha256

import pymongo
import bson


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

INVALID_USERNAME = "Invalid username; try just letters and numbers"
INVALID_PASSOWORD = "Invalid password"
INVALID_EMAIL = "Invalid email address"
PASSWORD_MISMATCH = "Password must match"
INVALID_PASSWORD = "Invalid password"


# implement the function make_pw_hash(name, pw) that returns
# a hashed password of the format:
# HASH(pw + salt),salt
def make_pw_hash(pw, salt=None):
    def make_salt(length=5):
        return "".join(choice(ascii_letters) for _ in range(length))
    salt = salt or make_salt()
    return sha256(pw + salt).hexdigest() + "," + salt


# validates that the user information is valid, return True of False
# and fills in the error codes
def validate_signup(username, password, verify, email, errors):
    keys = ['username_error', 'password_error', 'verify_error', 'email_error']
    errors.update({k: "" for k in keys})

    if not USER_RE.match(username):
        errors['username_error'] = INVALID_USERNAME
        return False

    elif not PASS_RE.match(password):
        errors['password_error'] = INVALID_PASSWORD
        return False

    elif password != verify:
        errors['verify_error'] = PASSWORD_MISMATCH
        return False

    elif email and not EMAIL_RE.match(email):
        errors['email_error'] = INVALID_EMAIL
        return False

    return True


# validates the login, returns True if it's a valid user login. false otherwise
# to validate a login, the blog must pull the user document and
# the hashed password and compare the password that the user has provided
# with the hashed password. to do the compare we must hash the password
# that the user is typing now on the login screen
def validate_login(db, username, password, user_record):
    try:
        print("retrieving username '%s'" % username)
        user = db.users.find_one({'_id': username})
    except Exception:
        print("Unable to query database for user %s" % username)

    if not user:
        print("User '%s' not in database" % username)
        return False

    salt = user['password'].split(',')[1]

    if user['password'] != make_pw_hash(password, salt):
        print("user password is not a match")
        return False

    user_record.update(user)
    return True


# will start a new session id by adding a new document to the
# sessions collection
def start_session(db, username):
    session = {'username': username}
    try:
        db.sessions.insert(session)
        return str(session['_id'])
    except Exception as err:
        print("Unexpected error on start_session: %s" % str(err))
        return -1


# will end a new user session by deleting from sessions table
def end_session(db, session_id):
    # this may fail because the string may not be a valid bson objectid
    try:
        object_id = bson.objectid.ObjectId(session_id)
        db.sessions.remove({'_id': object_id})
    except Exception:
        pass


# if there is a valid session, it is returned
def get_session(db, session_id):
    # this may fail because the string may not be a valid bson objectid
    try:
        object_id = bson.objectid.ObjectId(session_id)
        print("returning a session or none")
        return db.sessions.find_one({'_id': object_id})
    except Exception:
        print("bad sessionid passed in")


# creates a new user in the database
def newuser(db, username, password, email):
    tuples = (
        ('_id', username),
        ('password', make_pw_hash(password)),
        ('email', email)
    )
    user = {k: v for k, v in tuples if v}

    try:
        print("about to insert a user")
        db.users.insert(user)
        return True

    except pymongo.errors.DuplicateKeyError:
        print("oops, username is already taken")
        return False

    except pymongo.errors.OperationFailure:
        print("oops, mongo error")
        return False


SECRET = 'thisisnotsecret'


def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()


# call this to hash a cookie value
def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))


# call this to make sure that the cookie is still secure
def check_secure_val(h):
    print("check_secure_val(%s)" % h)
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val
