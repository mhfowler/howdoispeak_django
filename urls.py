from django.conf.urls import patterns, include, url
from hdis.views import viewWrapper, home, redirect, user_page, sentiment_page, category_page, \
    frequency_page, unique_page, ajaxAction, abnormal_page
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('',

   (r'^home/$', viewWrapper(home)),
   (r'^ajax/$', viewWrapper(ajaxAction)),
   (r'^sentiment/(\S+)/$', viewWrapper(sentiment_page)),
   (r'^category/(\S+)/$', viewWrapper(category_page)),
   (r'^frequency/(\S+)/$', viewWrapper(frequency_page)),
   (r'^unique/(\S+)/$', viewWrapper(unique_page)),
   (r'^abnormal/(\S+)/$', viewWrapper(abnormal_page)),
   (r'^(\S+)/$', viewWrapper(user_page)),
   (r'.*$',  redirect, {'page':"/home/"}),

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
