from django.conf.urls import patterns, include, url
from mhf.views import viewWrapper, home, redirect

urlpatterns = patterns('',

   (r'^home/$', viewWrapper(home)),
   (r'.*$',  redirect, {'page':"/home/"}),

)
