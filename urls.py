from django.conf.urls import patterns, include, url
from hdis.views import viewWrapper, home, redirect, user_page, ajaxAction
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('',

   (r'^home/$', viewWrapper(home)),
   (r'^ajax/$', viewWrapper(ajaxAction)),
   (r'^user/(\S+)/$', viewWrapper(user_page)),
   (r'.*$',  redirect, {'page':"/home/"}),

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
