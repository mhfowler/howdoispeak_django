from django.http import HttpResponse
from django import shortcuts
import json
from django.shortcuts import render_to_response
from django.template import RequestContext
from hdis.models import HowDoISpeakUser


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

def user_page(request, user_pin):
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    return  html_response(request=request, template="user_page.html", data_dict={"user_pin":user_pin})



