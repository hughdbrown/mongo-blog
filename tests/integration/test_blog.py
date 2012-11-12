
from random import choice
import re
# pylint: disable: W0402
from string import ascii_letters

from unittest2 import TestCase
from nose.tools import assert_true

import pymongo
import requests


# this is a validation program to make sure that the blog works correctly.
def create_user(username, password):
    try:
        print("Trying to create a test user %s" % username)
        url = "http://localhost:8082/signup"
        
        payload = {'email': '', 'username': username, 'password': password, 'verify': password}
        response = requests.post(url=url, data=payload)

        # check that the user is in the user table
        with pymongo.Connection("mongodb://localhost", safe=True) as connection:
            users = connection.blog.users
            user = users.find_one({'_id': username})

        if not user:
            print "Could not find the test user %s in the users collection." % username
        else:
            print "Found the test user %s in the users collection" % username
    
            # check that the user has been built
            if re.search(r"Welcome\s+%s" % username, response.text):
                return True
            
            print "When we tried to create a user, here is the output we got\n"
            print response.text
    except Exception:
        print "the request to ", url, " failed, so your blog may not be running."
    return False


def try_to_login(username, password):
    try:
        print "Trying to login for test user ", username
        url = "http://localhost:8082/login"

        payload = {"username": username, "password": password}
        response = requests.post(url=url, data=payload)

        # check for successful login
        if re.search(r"Welcome\s+%s" % username, response.text):
            return True
        else:
            print "When we tried to login, here is the output we got\n"
            print response.text
    except Exception:
        print "the request to ", url, " failed, so your blog may not be running."
    return False


class BlogTest(TestCase):
    def setUp(self):
        def make_salt(n):
            return "".join(choice(ascii_letters) for _ in range(n))
        print("Making username and password")
        self.username = make_salt(7)
        self.password = make_salt(8)

    def test_create_and_login(self):
        print("creating user")
        assert_true(create_user(self.username, self.password))
        print("logging in as user")
        assert_true(try_to_login(self.username, self.password))

