from hd_jobs.common import *

# REGISTER RAW DATA AND MOVE IT TO USER FOLDERS
# ======================================================================================================================

# move all data in raw (that has been recently uploaded) to its own user folders, while tracking these users in the db
def registerAllRawData():
    keys_list = getS3RawKeys()
    for s3_key in keys_list:
        moveAndRegisterRawData(s3_key)

# move data from s3 key to new user folder while registering it in database
def moveAndRegisterRawData(s3_key):
    print "moving: " + str(s3_key.key)
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

    user.enqueued = True
    user.save()

    return user

# return all keys in the raw folder
def getS3RawKeys():
    bucket = getHDISBucket()
    keys = bucket.list()
    keys_list = []
    for key in keys:
        name = key.name
        result = re.match("raw/.+", name)
        if result:
            keys_list.append(key)
    return keys_list