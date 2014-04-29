from django.conf.urls import patterns, include, url
from hdis.views import viewWrapper, home, redirect, user_page

urlpatterns = patterns('',

   (r'^home/$', viewWrapper(home)),
   (r'^user/(\S+)/$', viewWrapper(user_page)),
   (r'.*$',  redirect, {'page':"/home/"}),

)
