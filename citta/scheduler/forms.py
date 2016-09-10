from django.forms import ModelForm, CheckboxSelectMultiple, ValidationError
from .models import UserInfo, Task

class UserInfoForm(ModelForm):
	def clean_study_days(self):
		data = self.cleaned_data['study_days']
		#Check that at least one day has been selected
		if len(data) == 0:
			raise ValidationError("Please select at least one day")
		return data

	def clean(self):
		cleaned_data = super(UserInfoForm, self).clean()
		start = cleaned_data.get('study_start')
		end = cleaned_data.get('study_end')

		if start and end and end < start:
			raise ValidationError("End time must be after start time")
		return cleaned_data
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
			'attention_span',
		]

class EditTaskForm(ModelForm):
	class Meta:
		model = Task
		fields = [
			'subject',
			'content',
			'category',
			'due_date',
			'total_time',
			'attention_span',
			'amount_done',
		]

class ProgressForm(ModelForm):
	def clean_amount_done(self):
		data = self.cleaned_data['amount_done']
		if data < 0 or data > 100:
			raise ValidationError("Please choose a value between 0 and 100")
		return data

	class Meta:
		model = Task
		fields = [
			'amount_done'
		]
