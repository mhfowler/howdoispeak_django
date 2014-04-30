from django.http import HttpResponse
from django import shortcuts
import json
from django.shortcuts import render_to_response
from django.template import RequestContext
from hdis.models import HowDoISpeakUser
from settings.common import getHDISBucket
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie


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

######### ajax actions ###################
@csrf_exempt
def ajaxAction(request):
    action = request.POST["action"]
    action_map = {
        "getWordFreq":getWordFreq
    }
    return action_map[action](request)


def getWordFreq(request):
    user_pin = request.POST["user_pin"]
    word = request.POST["word"]
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    bucket = getHDISBucket()
    freq_key_name = hdis_user.getFreqKeyName()
    freq_key = bucket.get_key(freq_key_name)
    freq_json = freq_key.get_contents_as_string()
    freq_dict = json.loads(freq_json)["total_freq"]
    word_freq = freq_dict.setdefault(word, 0)
    to_return = {"freq":word_freq}
    return json_response(to_return)






