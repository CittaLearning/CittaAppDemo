from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.home,name='home'),
	url(r'tasksFeed/$', views.tasksFeed, name='tasksFeed'),
	url(r'newtask/$', views.newTask, name='newtask'),
	url(r'login/$', views.login, name='login'),
	url(r'logout/$', views.logout, name='logout'),
	url(r'setuser/$', views.setUser, name='setuser'),
	url(r'reschedule/$', views.reschedule, name='reschedule'),
	url(r'progress/(?P<key>[0-9]+)/$', views.progress, name='progress'),
	url(r'edittask/(?P<key>[0-9]+)/$', views.editTask, name='edittask'),
	url(r'deletetask/(?P<key>[0-9]+)/$', views.deleteTask, name='deletetask'),
]
