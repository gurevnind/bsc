from django.conf.urls import url
from django.views.generic.base import RedirectView

from blog.views import *
import blog.views
from django.contrib.auth import views as auth_views

urlpatterns = [url(r'^$', PostsView.as_view(), name='list'),
               url(r'^signup/$', signup, name='signup'),
               url(r'^login/$', auth_views.LoginView.as_view(), name='login'),
               url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
               url(r'^email_change/$', update_profile, name='email'),
               url(r'^password_change/$',
                   auth_views.PasswordChangeView.as_view(template_name='registration/change_password.html'),
                   name='change_password'),
               url(r'^accounts/password_change/done/$', RedirectView.as_view(url='/', permanent=False),
                   name='index'),
               url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
                   activate, name='activate'),
               url(r'^(?P<pk>\d+)/$', ArticleDetailView.as_view()),
               url(r'^like/(?P<pk>[0-9]+)/$', add_like, name='add_like'),
               url(r'^dislike/(?P<pk>[0-9]+)/$', add_dislike, name='add_dislike'),
               url(r'^comment/(?P<pk>[0-9]+)/$', add_comment, name='add_comment'),
               url(r'^post/$', add_post, name='add_post'),
               url(r'posts/', ListPostView.as_view(), name='posts-all')
               ]
handler404 = 'views.handle_page_not_found_404'
