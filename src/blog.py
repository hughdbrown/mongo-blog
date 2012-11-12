from __future__ import print_function

import bottle
from pymongo import DESCENDING

import cgi
import re
import datetime
from itertools import ifilter

from src.database import blog_connection
import src.user as user


# inserts the blog entry and returns a permalink for the entry
def insert_entry(title, post, tags_array, author):
    print("inserting blog entry", title, post)

    db = blog_connection()

    exp = re.compile(r'\W')  # match anything not alphanumeric
    whitespace = re.compile(r'\s')
    temp_title = whitespace.sub("_", title)
    permalink = exp.sub('', temp_title)

    post = {
        "title": title,
        "author": author,
        "body": post,
        "permalink": permalink,
        "tags": tags_array,
        "date": datetime.datetime.utcnow(),
        'comments': [],
    }

    try:
        print("Inserting the post")
        db.posts.insert(post)
    except Exception as err:
        print("Error inserting post: %s" % str(err))

    return permalink


@bottle.route('/')
def blog_index():
    db = blog_connection()

    username = login_check()  # see if user is logged in

    # Find the last ten most recent posts, sorted from newest to oldest
    myposts = [
        {
            'title': post['title'],
            'body': post['body'],
            'post_date': post['date'].strftime("%A, %B %d %Y at %I:%M%p"),
            'permalink': post['permalink'],
            'tags': post.get('tags', []),
            'author': post['author'],
            'comments': post.get('comments', []),
        }
        for post in db.posts.find({'author': username})
                            .sort('date', DESCENDING)
                            .limit(10)
    ]

    return bottle.template('blog_template', {
        'myposts': myposts,
        'username': username,
    })


# gets called both for regular requests and json requests
@bottle.get("/post/<permalink>")
def show_post(permalink="notfound"):
    db = blog_connection()

    username = login_check()  # see if user is logged in
    permalink = cgi.escape(permalink)

    print("about to query on permalink = ", permalink)
    # find a post that has the appropriate permalink

    post = db.posts.find_one({'permalink': permalink})

    # end student work
    if not post:
        bottle.redirect("/post_not_found")

    print("date of entry is ", post['date'])

    # fix up date
    post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")

    # init comment form fields for additional comment
    comment = {
        'name': "",
        'email': "",
        'body': "",
    }

    return bottle.template("entry_template", {
        'post': post,
        'username': username,
        'errors': "",
        'comment': comment,
    })


# used to process a comment on a blog post
@bottle.post('/newcomment')
def post_newcomment():
    name = bottle.request.forms.get("commentName")
    email = bottle.request.forms.get("commentEmail")
    body = bottle.request.forms.get("commentBody")
    permalink = bottle.request.forms.get("permalink")

    # look up the post in question
    db = blog_connection()

    # see if user is logged in
    username = login_check()
    permalink = cgi.escape(permalink)

    post = db.posts.find_one({'permalink': permalink})

    # if post not found, redirct to post not found error
    if not post:
        bottle.redirect("/post_not_found")

    print("post %s was found" % permalink)
    print(post)

    # if values not good, redirect to view with errors
    if not (name and body):
        # fix up date
        post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")

        # init comment
        comment = {
            'name': name,
            'email': email,
            'body': body,
        }

        errors = "Post must contain your name and an actual comment."
        print("newcomment: error in comment..returning form with errors")
        return bottle.template("entry_template", {
            'post': post,
            'username': username,
            'errors': errors,
            'comment': comment,
        })
    else:
        # it all looks good, insert the comment into the blog post and
        # redirect back to the post viewer
        comment = {
            'author': name,
            'body': body,
        }
        if email:
            comment['email'] = email

        try:
            # You will need to update the blog post and add the comment onto
            # the comment array. make sure you only update one document here
            # by updating the one with the right permalink.
            print("about to update a blog post with a comment")
            db.posts.update({'permalink': permalink}, {
                "$set": {'comments': post.get('comments', []) + [comment]}
            })
            #print "num documents updated" + last_error['n']
        except Exception as err:
            print("Could not update the collection: %s" % str(err))

        print("newcomment: added the comment....redirecting to post")
        bottle.redirect("/post/" + permalink)


@bottle.get("/post_not_found")
def post_not_found():
    return "Sorry, post not found"


# how new posts are made. this shows the initial page with the form
@bottle.get('/newpost')
def get_newpost():
    username = login_check()  # see if user is logged in
    if not username:
        bottle.redirect("/login")

    return bottle.template("newpost_template", {
        'subject': "",
        'body': "",
        'errors': "",
        'tags': "",
        'username': username,
    })


# extracts the tag from the tags form element.
# an experience python programmer could do this in fewer lines, no doubt
def extract_tags(tags):
    nowhite = re.sub(r'\s+', "", tags)

    # let's clean it up
    return list(ifilter(None, set(nowhite.split(','))))


# put handler for setting up a new post
@bottle.post('/newpost')
def post_newpost():
    username = login_check()  # see if user is logged in
    if not username:
        bottle.redirect("/login")

    title = bottle.request.forms.get("subject")
    post = bottle.request.forms.get("body")
    tags = bottle.request.forms.get("tags")

    if not (title and post):
        errors = "Post must contain a title and blog entry"
        return bottle.template("newpost_template", {
            'subject': cgi.escape(title, quote=True),
            'username': username,
            'body': cgi.escape(post, quote=True),
            'tags': tags,
            'errors': errors,
        })

    # extract tags
    tags = cgi.escape(tags)
    tags_array = extract_tags(tags)

    # looks like a good entry, insert it escaped
    escaped_post = cgi.escape(post, quote=True)

    # substitute some <p> for the paragraph breaks
    newline = re.compile('\r?\n')
    formatted_post = newline.sub("<p>", escaped_post)

    permalink = insert_entry(title, formatted_post, tags_array, username)

    # now bottle.redirect to the blog permalink
    bottle.redirect("/post/" + permalink)


# displays the initial blog signup form
@bottle.get('/signup')
def present_signup():
    return bottle.template("signup", {
        'username': "",
        'password': "",
        'password_error': "",
        'email': "",
        'username_error': "",
        'email_error': "",
        'verify_error': ""
    })


# displays the initial blog login form
@bottle.get('/login')
def present_login():
    return bottle.template("login", {
        'username': "",
        'password': "",
        'login_error': ""
    })


# handles a login request
@bottle.post('/login')
def process_login():
    db = blog_connection()

    username = bottle.request.forms.get("username")
    password = bottle.request.forms.get("password")

    print("user submitted ", username, "pass ", password)

    userRecord = {}
    if user.validate_login(db, username, password, userRecord):
        session_id = user.start_session(db, username)
        if session_id == -1:
            bottle.redirect("/internal_error")

        cookie = user.make_secure_val(session_id)

        # Warning, if you are running into a problem whereby the cookie
        # being set here is not getting set on the redirct, you are
        # probably using the experimental version of bottle (.12).
        # revert to .11 to solve the problem.
        bottle.response.set_cookie("session", cookie)
        bottle.redirect("/welcome")
    else:
        return bottle.template("login", {
            'username': cgi.escape(username),
            'password': "",
            'login_error': "Invalid Login"
        })


@bottle.get('/internal_error')
@bottle.view('error_template')
def present_internal_error():
    return ({'error': "System has encountered a DB error"})


@bottle.get('/logout')
def process_logout():
    cookie = bottle.request.get_cookie("session")

    if not cookie:
        print("no cookie...")
        bottle.redirect("/signup")
    else:
        session_id = user.check_secure_val(cookie)
        if not session_id:
            print("no secure session_id")
            bottle.redirect("/signup")
        else:
            db = blog_connection()

            # remove the session
            user.end_session(db, session_id)
            print("clearing the cookie")
            bottle.response.set_cookie("session", "")
            bottle.redirect("/signup")


@bottle.post('/signup')
def process_signup():
    db = blog_connection()

    keys = ["email", "username", "password", "verify"]
    fn = bottle.request.forms.get
    email, username, password, verify = [fn(k) for k in keys]

    # set these up in case we have an error case
    errors = {
        'username': cgi.escape(username),
        'email': cgi.escape(email)
    }
    if user.validate_signup(username, password, verify, email, errors):
        if not user.newuser(db, username, password, email):
            # this was a duplicate
            errors['username_error'] = \
                "Username already in use. Please choose another"
            return bottle.template("signup", errors)

        session_id = user.start_session(db, username)
        print("Session id %s" % session_id)
        cookie = user.make_secure_val(session_id)
        bottle.response.set_cookie("session", cookie)
        bottle.redirect("/welcome")
    else:
        print("user '%s' did not validate" % username)
        return bottle.template("signup", errors)


# will check if the user is logged in and if so, return the username.
# otherwise, it returns None
def login_check():
    cookie = bottle.request.get_cookie("session")

    if not cookie:
        print("no cookie...")
    else:
        session_id = user.check_secure_val(cookie)
        if not session_id:
            print("no secure session_id")
        else:
            # look up username record
            db = blog_connection()
            print("Look up session id %s" % session_id)
            session = user.get_session(db, session_id)
            return session and session['username']


@bottle.get("/welcome")
def present_welcome():
    # check for a cookie, if present, then extract value
    username = login_check()
    if not username:
        print("welcome: can't identify user...redirecting to signup")
        bottle.redirect("/signup")
    return bottle.template("welcome", {'username': username})


def main():
    bottle.debug(True)
    bottle.run(host='localhost', port=8082)


if __name__ == '__main__':
    main()
