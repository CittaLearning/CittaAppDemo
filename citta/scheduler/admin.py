from django.contrib import admin
from .models import UserInfo, Task, Day
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserInline(admin.StackedInline):
	model = UserInfo
	can_delete = False

class UserAdmin(BaseUserAdmin):
	inlines = (UserInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Task)
admin.site.register(Day)
