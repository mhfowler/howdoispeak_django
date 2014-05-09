from django.http import HttpResponse
from django import shortcuts
import json
from django.shortcuts import render_to_response
from django.template import RequestContext
from hdis.models import HowDoISpeakUser
from hd_jobs.common import getOrCreateS3Key, aggregateByTime, makeTimeKeyFromTimeTuple, makeTimeKeyFromPythonDate
from settings.common import getHDISBucket
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
import datetime


def redirect(request, page='/home'):
    return shortcuts.redirect(page)

def viewWrapper(view):
    def new_view(request, *args, **kwargs):
        return view(request,*args,**kwargs)
    return new_view

def json_response(res):
    return HttpResponse(json.dumps(res),content_type="application/json")

def html_response(request, template, data_dict=None):
    return render_to_response(template,
                              data_dict,
                              context_instance=RequestContext(request))

def home(request):
    return  html_response(request=request, template="landing.html")

@ensure_csrf_cookie
def user_page(request, user_pin):
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    return  html_response(request=request, template="user_page.html", data_dict={"user_pin":user_pin})

@ensure_csrf_cookie
def sentiment_page(request, user_pin):
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    return  html_response(request=request, template="sentiment_page.html", data_dict={"user_pin":user_pin})

@ensure_csrf_cookie
def category_page(request, user_pin):
    user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    bucket = getHDISBucket()
    categories_key_name = user.getCategoriesTotalKeyName()
    categories_key = bucket.get_key(categories_key_name)
    avgdata = categories_key.get_contents_as_string()
    categories_by_person_key_name = user.getCategoriesByPersonKeyName()
    categories_by_person_key = bucket.get_key(categories_by_person_key_name)
    persondata = categories_by_person_key.get_contents_as_string()
    return  html_response(request=request, template="categories_page.html", data_dict={"user_pin":user_pin,"persondata":persondata,"avgdata":avgdata})

@ensure_csrf_cookie
def frequency_page(request, user_pin):
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    return  html_response(request=request, template="frequency_page.html", data_dict={"user_pin":user_pin})

@ensure_csrf_cookie
def unique_page(request, user_pin):
    user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    abnormal_key_name = user.getAbnormalKeyName()
    abnormal_key, abnormal_key_dict = getOrCreateS3Key(abnormal_key_name)
    unique_words = abnormal_key_dict["unique"]
    return  html_response(request=request, template="unique_page.html", data_dict={"user_pin":user_pin,"unique_words":unique_words})

@ensure_csrf_cookie
def abnormal_page(request, user_pin):
    user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    abnormal_key_name = user.getAbnormalKeyName()
    abnormal_key, abnormal_key_dict = getOrCreateS3Key(abnormal_key_name)
    abnormal_words = abnormal_key_dict["abnormal"] # these are tuples of word, usage_ratio
    return  html_response(request=request, template="abnormal_page.html", data_dict={"user_pin":user_pin,"abnormal_words":abnormal_words})

######### ajax actions ###################
@csrf_exempt
def ajaxAction(request):
    action = request.POST["action"]
    action_map = {
        "getAbnormalRatio":getAbnormalRatio,
        "getWordFreqDataByTime":getWordFreqDataByTime,
        "getSentimentByHourData":getSentimentByHourData,
        "getSentimentByPersonData":getSentimentByPersonData
    }
    return action_map[action](request)

def getAbnormalRatio(request):
    user_pin = request.POST["user_pin"]
    word = request.POST["word"]
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    bucket = getHDISBucket()
    abnormal_key_name = hdis_user.getAbnormalKeyName()
    abnormal_key, abnormal_key_dict = getOrCreateS3Key(abnormal_key_name)
    abnormal_ratio = abnormal_key_dict.setdefault(word, 0)
    to_return = {"abnormal":abnormal_ratio}
    return json_response(to_return)

def getWordFreqDataByTime(request):
    user_pin = request.POST["user_pin"]
    word = request.POST["word"]
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    bucket = getHDISBucket()
    freq_key_name = hdis_user.getFreqKeyName()
    freq_key = bucket.get_key(freq_key_name)
    freq_json = freq_key.get_contents_as_string()
    freq_dict = json.loads(freq_json)

    resolution = "month"

    if resolution == "month":
        # for list of months get freq fo reach month
        dates_list = getListOfMonths()
        freq_by_date = freq_dict["month_freqs"]
    else:
        dates_list = getListOfDays()
        dates_list = map(makeTimeKeyFromPythonDate, dates_list)
        freq_by_date = freq_dict["day_freqs"]

    to_return = []
    first = False
    for index,date_key in enumerate(dates_list):
        date_freqs = freq_by_date.get(date_key)
        if date_freqs:
            first = True
            word_freq = date_freqs.setdefault(word, 0)
        else:
            word_freq = 0
        # don't write anything until we find the first data point
        if first:
            to_return.append({"date":date_key, "freq":word_freq})

    # return json response
    return json_response(to_return)


def getSentimentByHourData(request):
    user_pin = request.POST["user_pin"]
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    bucket = getHDISBucket()
    sentiment_by_hour_key_name = hdis_user.getSentimentByHourKeyName()
    s_key = bucket.get_key(sentiment_by_hour_key_name)
    s_data = s_key.get_contents_as_string()
    return HttpResponse(s_data)

def getSentimentByPersonData(request):
    user_pin = request.POST["user_pin"]
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    bucket = getHDISBucket()
    sentiment_by_person_key_name = hdis_user.getSentimentByPersonKeyName()
    s_key = bucket.get_key(sentiment_by_person_key_name)
    s_data = s_key.get_contents_as_string()
    return HttpResponse(s_data)


# returns a list of dates from beginning of time until today
def getListOfDays(base=None,totalnum=None,direction="backwards"):
    if not base: base = datetime.datetime.today()
    if not totalnum: totalnum = 365 * 10
    def genDate(x):
        return datetime.timedelta(days=x)
    if direction == "backwards":
        date_list = [base - genDate(x) for x in range(0, totalnum)]
    else:
        date_list = [base + genDate(x) for x in range(0, totalnum)]
    date_list.sort(reverse=True)
    return date_list

def getListOfMonths():
    months_list = []
    for year in range(2005,2015):
        for month in range(1,13):
            months_list.append(str(month) + "|" + str(year))
    return months_list

