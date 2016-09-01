from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.home, name='home'),
	url(r'tasksFeed', views.tasksFeed, name='tasksFeed'),
	url(r'newtask', views.newTask, name='newtask'),
	url(r'login', views.login, name='login'),
]
