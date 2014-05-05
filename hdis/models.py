from django.db import models
from settings.common import getHDISBucket
from boto.s3.connection import Key

#-----------------------------------------------------------------------------------------------------------------------
# Useful manager for all models.
#-----------------------------------------------------------------------------------------------------------------------
class XManager(models.Manager):
    """Adds get_or_none method to objects
    """
    def get_or_none(self, **kwargs):
        to_return = self.filter(**kwargs)
        if to_return:
            return to_return[0]
        else:
            return to_return

#-----------------------------------------------------------------------------------------------------------------------
# All models inherit from this
#-----------------------------------------------------------------------------------------------------------------------
class XModel(models.Model):
    x = XManager()
    objects = models.Manager()
    class Meta:
        abstract = True


# ------------------------------------------------------------------------
# User Object keeps track of users pins, as well as where they are in the processing pipeline
# ------------------------------------------------------------------------

class HowDoISpeakUser(XModel):
    email = models.CharField(max_length=500)
    enqueued = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    created_when = models.DateTimeField(auto_now_add=True, blank=True)
    user_pin = models.CharField(max_length=100)

    def getS3Folder(self):
        return "users/" + str(self.user_pin) + "/"

    def getRawKeyName(self):
        return self.getS3Folder() + "raw.json"

    def getFreqKeyName(self):
        return self.getS3Folder() + "freq.json"

    def getByTimeKeyName(self):
        return self.getS3Folder() + "by_time.json"

    def getCategoriesKeyName(self):
        return self.getS3Folder() + "categories.json"

    def getGroupsTrackerKeyName(self):
        return self.getS3Folder() + "groups.json"

    def getSentimentByPersonKeyName(self):
        return self.getS3Folder() + "sentiment_by_person.txt"

    def getSentimentByHourName(self):
        return self.getS3Folder() + "sentiment_by_hour.txt"

    def getGroupsTrackerKey(self):
        groups_tracker_key_name = self.getGroupsTrackerKeyName()
        bucket = getHDISBucket()
        groups_tracker_key = bucket.get_key(groups_tracker_key_name)
        if not groups_tracker_key:
            groups_tracker_key = Key(bucket)
            groups_tracker_key.key = groups_tracker_key_name
        return groups_tracker_key
