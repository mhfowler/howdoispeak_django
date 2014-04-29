# this job takes in a file name from s3
# gives them a unique id, stores this user in the database with their email and user_pin,
# creates an s3 folder with the name of their user_pin, then deletes the users file from /raw/ (wherever it was)
from settings.common import getS3Credentials
from hdis.models import HowDoISpeakUser
import json, random
from boto.s3.connection import S3Connection
from boto.s3.key import Key

def enqueuRawData(s3_key_name):
    aws_access_key_id, aws_secret_access_key = getS3Credentials()
    conn = S3Connection(aws_access_key_id, aws_secret_access_key)
    bucket = conn.get_bucket('howdoispeak')

    k = bucket.get_key(s3_key_name)

    json_string = k.get_contents_as_string()
    user_data = json.loads(json_string)

    user_email = str(user_data["user_meta"].get("user_name"))

    id_found = False
    user_pin = None
    while not id_found:
        user_pin = random.randint(0,10000000000)
        already = HowDoISpeakUser.objects.get(user_pin=user_pin)
        if not already:
            id_found = True
            # create new user object
            user = HowDoISpeakUser(email=user_email, user_pin=user_pin)
            user.save()

    new_key_name = "users/" + str(user_pin) + "/" + "raw.json"

    new_key = Key(bucket)
    k.key = new_key_name
    new_key.set_contents_from_string(json_string)
    print "user_pin: " + str(user_pin)
    return user_pin
