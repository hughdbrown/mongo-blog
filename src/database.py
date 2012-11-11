import pymongo

CONNECTION = "mongodb://localhost"
connection = None


#pylint: disable=W0603
def blog_connection():
    global connection
    if not connection:
        connection = pymongo.Connection(CONNECTION, safe=True)
    return connection.blog
