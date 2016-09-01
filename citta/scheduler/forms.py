from django.forms import ModelForm, CheckboxSelectMultiple
from .models import UserInfo, Task

class UserInfoForm(ModelForm):
	class Meta:
		model = UserInfo
		fields = [
			'break_time',
			'study_start',
			'study_end',
			'study_days'
		]

class TaskForm(ModelForm):
	class Meta:
		model = Task
		fields = [
			'subject',
			'content',
			'category',
			'due_date',
			'total_time',
			'attention_span'
		]
