from django.conf.urls import patterns, include, url
from hdis.views import viewWrapper, home, redirect, user_page, sentiment_page, category_page, \
    frequency_page, unique_page, ajaxAction, abnormal_page
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('',

   (r'^home/$', viewWrapper(home)),
   (r'^ajax/$', viewWrapper(ajaxAction)),
   (r'^user/(\S+)/sentiment/$', viewWrapper(sentiment_page)),
   (r'^user/(\S+)/category/$', viewWrapper(category_page)),
   (r'^user/(\S+)/frequency/$', viewWrapper(frequency_page)),
   (r'^user/(\S+)/unique/$', viewWrapper(unique_page)),
   (r'^user/(\S+)/abnormal/$', viewWrapper(abnormal_page)),
   (r'^user/(\S+)/$', viewWrapper(user_page)),
   (r'.*$',  redirect, {'page':"/home/"}),

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
