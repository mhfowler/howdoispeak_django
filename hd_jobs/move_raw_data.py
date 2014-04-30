# this job takes in a file name from s3
# gives them a unique id, stores this user in the database with their email and user_pin,
# creates an s3 folder with the name of their user_pin, then deletes the users file from /raw/ (wherever it was)
from settings.common import getHDISBucket
from hdis.models import HowDoISpeakUser
import json, random, re
from boto.s3.connection import S3Connection
from boto.s3.key import Key


def moveRawData(s3_key):
    print "moving"
    bucket = getHDISBucket()

    json_string = s3_key.get_contents_as_string()
    user_data = json.loads(json_string)

    user_email = str(user_data["user_meta"].get("user_name"))

    id_found = False
    user_pin = None
    user = None
    while not id_found:
        user_pin = random.randint(0,10000000000)
        user = HowDoISpeakUser.x.get_or_none(user_pin=user_pin)
        if not user:
            id_found = True
            # create new user object
            user = HowDoISpeakUser(email=user_email, user_pin=user_pin)
            user.save()

    new_key_name = "users/" + str(user_pin) + "/" + "raw.json"

    new_key = Key(bucket)
    new_key.key = new_key_name
    new_key.set_contents_from_string(json_string)
    print "user_pin: " + str(user_pin)

    # delete old key
    bucket.delete_key(s3_key.name)

    return user


if __name__ == "__main__":
    # enqueuAll()
    print "move"
