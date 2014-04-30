# takes in a user_pin, and adds user count data to all aggregate counts for every group to which that user belongs
# (for initial version, the only group is the group of all users)
from hdis.models import HowDoISpeakUser
from settings.common import getHDISBucket
from common.text_data import TextData, makeTimeKeyFromTimeTuple, getTimeTupleFromTimeString
from boto.s3.key import Key
import json

def addUserToGroups(user_pin):
    print "grouping: " + str(user_pin)
    bucket = getHDISBucket()
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    # keep track of which groups user is in
    groups_tracker_key_name = hdis_user.getGroupsTrackerKeyName()
    groups_tracker_key = bucket.get_key(groups_tracker_key_name)
    if groups_tracker_key:
        group_json = group_key.get_contents_as_string()
    else:
        groups_tracker_key = Key(bucket)
        group_tracker_key.key = groups_tracker_key_name
        group_json = json.dumps([])
    groups_tracker_list = json.loads(groups_json)

    group_names = getGroupKeys(hdis_user)
    for group_name in group_names:
        addUserToGroup(hdis_user, group_name)
        groups_tracker_list.append(group_name)
    groups_tracker_key.set_contents_from_string(json.dumps(groups_tracker_list))


def addUserToGroup(hdis_user, group_folder):
    bucket = getHDISBucket()
    group_key_name = group_folder + "raw.json"
    group_key = bucket.get_key(group_key_name)
    try:
        group_json = group_key.get_contents_as_string()
    except:
        group_key = Key(bucket)
        group_key.key = group_key_name
    try:
        group_dict = json.loads(group_json)
    except:
        group_dict = {
            "group_meta":
                {
                    "group_name":group_folder
                }
        }
    group_meta = group_dict.get("group_meta")
    group_counts = group_dict.setdefault("counts", {})     # dictionary mapping (hour,day,month,year) to word counts
    group_num_users = group_dict.setdefault("num_users",{}) # dictionary mapping (day,month,year) to number of users who have data from that day
    user_key_name = hdis_user.getRawKeyName()
    user_key = bucket.get_key(user_key_name)
    user_td = TextData()
    user_td.loadFromS3Keys([user_key])
    user_td.calcByTime()
    user_by_time = user_td.getByTime()
    user_days_saved = user_td.getDaysSaved()
    # increment number of people in the count for each day saved
    for day_tuple in user_days_saved:
        day_string = makeTimeKeyFromTimeTuple(day_tuple)
        num_users_prev = group_num_users.setdefault(day_string, 0)
        group_num_users[day_string] = num_users_prev + 1
    # increment word counts
    for time_tuple, user_data in user_by_time.items():
        time_key = makeTimeKeyFromTimeTuple(time_tuple)
        user_word_counts = user_data["1"]
        user_num_texts = user_data["num_texts"]
        user_text_blob = user_data["text_blob"]
        group_data = group_counts.setdefault(time_key, {})
        group_word_counts = group_data.setdefault("1", {})
        group_num_texts = group_data.setdefault("num_texts", 0)
        group_text_blob = group_data.setdefault("text_blob", "")
        group_data["text_blob"] = group_text_blob + " " + user_text_blob
        group_data["num_texts"] = group_num_texts + user_num_texts
        for word,count in user_word_counts.items():
            prev_count = group_word_counts.setdefault(word, 0)
            group_word_counts[word] = prev_count + count
    # write json of group back to the key where it came from
    updated_group_json = json.dumps(group_dict)

    group_key.set_contents_from_string(updated_group_json)


def getGroupKeys(hdis_user):
    bucket = getHDISBucket()
    group_key_name = "groups/all/"
    return [group_key_name]


if __name__ == "__main__":
    addUserToGroup("6996200796") # add max to group