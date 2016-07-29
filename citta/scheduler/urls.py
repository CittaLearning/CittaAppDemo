from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.home, name='home'),
	url(r'tasksFeed', views.tasksFeed, name='tasksFeed')
]