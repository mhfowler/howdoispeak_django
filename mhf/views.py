from django.http import HttpResponse
from django import shortcuts


def redirect(request, page='/home'):
    return shortcuts.redirect(page)


def viewWrapper(view):
    def new_view(request, *args, **kwargs):
        return view(request,*args,**kwargs)
    return new_view


def home(request):
    return HttpResponse("Miley do what she want doe")