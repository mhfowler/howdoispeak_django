from django.db import models

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
