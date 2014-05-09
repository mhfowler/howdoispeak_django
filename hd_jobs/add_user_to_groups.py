from hd_jobs.common import *

# takes in a user_pin, and adds user count data to all aggregate counts for every group to which that user belongs
# (for initial version, the only group is the group of all users)
def addUserToGroups(user_pin):
    print "grouping: " + str(user_pin)
    bucket = getHDISBucket()
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    # keep track of which groups user is in
    groups_tracker_key_name = hdis_user.getGroupsTrackerKeyName()
    groups_tracker_key, groups_tracker_list = getOrCreateS3Key(groups_tracker_key_name)

    group_names = getUserGroups(hdis_user)
    for group_name in group_names:
        addUserToGroup(hdis_user, group_name)
        groups_tracker_list.append(group_name)
    groups_tracker_key.set_contents_from_string(json.dumps(groups_tracker_list))


def addUserToGroup(hdis_user, group_folder):
    user_pin = hdis_user.user_pin
    group_key_name = group_folder + "raw.json"
    group_key, group_dict = getOrCreateS3Key(group_key_name)
    group_meta = group_dict.setdefault("group_meta", {"group_name":group_folder})
    group_counts = group_dict.setdefault("counts", {})     # dictionary mapping (hour,day,month,year) to word counts

    # processed users
    group_num_users = group_dict.setdefault("num_users",{}) # dictionary mapping (day,month,year) to number of users who have data from that day
    processed_users = group_meta.setdefault("processed_users",[])
    if user_pin in processed_users:
        print "skipped ... " + group_folder
        return False
    processed_users.append(hdis_user.user_pin)

    # do it
    user_key_name = hdis_user.getRawKeyName()
    bucket = getHDISBucket()
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
    user_vocab = set([])
    for time_tuple, user_data in user_by_time.items():
        time_key = makeTimeKeyFromTimeTuple(time_tuple)
        user_word_counts = user_data["1"]
        user_num_texts = user_data["num_texts"]
        group_data = group_counts.setdefault(time_key, {})
        group_word_counts = group_data.setdefault("1", {})
        group_num_texts = group_data.setdefault("num_texts", 0)
        group_data["num_texts"] = group_num_texts + user_num_texts
        for word,count in user_word_counts.items():
            prev_count = group_word_counts.setdefault(word, 0)
            group_word_counts[word] = prev_count + count
            user_vocab.add(word)

    # group vocab
    group_vocab = group_dict.setdefault("vocab", {"1":[],"2":[],"3":[]})
    one_thresh = group_vocab["1"]
    one_thresh_set = set(one_thresh)
    two_thresh = group_vocab["2"]
    two_thresh_set = set(two_thresh)
    three_thresh = group_vocab["3"]
    three_thresh_set = set(three_thresh)
    user_vocab = list(user_vocab)
    for word in user_vocab:
        if word in two_thresh_set:
            three_thresh_set.add(word)
        elif word in one_thresh_set:
            two_thresh_set.add(word)
        else:
            one_thresh_set.add(word)
    group_vocab["1"] = list(one_thresh_set)
    group_vocab["2"] = list(two_thresh_set)
    group_vocab["3"] = list(three_thresh_set)



    # write json of group back to the key where it came from
    updated_group_json = json.dumps(group_dict)
    group_key.set_contents_from_string(updated_group_json)


def getUserGroups(hdis_user):
    bucket = getHDISBucket()
    group_key_name = "groups/all/"
    return [group_key_name]


def getGroupKeys(group_folder):
    bucket = getHDISBucket()
    keys = bucket.list()
    to_return = []
    for key in keys:
        name = key.name
        result = re.match(group_folder + ".*", name)
        if result:
            to_return.append(key)
    return to_return


def clearGroup(group_folder_name):
    bucket = getHDISBucket()
    group_keys = getGroupKeys(group_folder_name)
    bucket.delete_keys(group_keys)
    # for all users set that they are not included in group anymore
    users = HowDoISpeakUser.objects.all()
    for u in users:
        groups_tracker_key_name = u.getGroupsTrackerKeyName()
        groups_tracker_key, groups_tracker_list = getOrCreateS3Key(groups_tracker_key_name)
        updated_groups_tracker_list = [x for x in groups_tracker_list if x != group_folder_name]
        groups_tracker_key.set_contents_from_string(json.dumps(updated_groups_tracker_list))


if __name__ == "__main__":
    clearGroup("groups/all/")
