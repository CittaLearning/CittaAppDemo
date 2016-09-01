from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserInfo, Task
from .forms import TaskForm
import datetime
import json

def task_print(task):
	return (task[0] + ' ' + task[2] + ': ' + task[1]
		+ ' Due: ' + task[3].strftime('%m/%d/%y'))

def scheduled_day_time(day):
	total_time = datetime.timedelta()
	for task in day:
		total_time += task[5] # Add the task attn span to the timedelta
	return total_time

# Comparator for task objects
def task_compare(task1, task2):
	current_date = datetime.date.today()
	days_remaining_1 = (task1[3] - current_date).days
	days_remaining_2 = (task2[3] - current_date).days
	one_week_1 = days_remaining_1 <= 7
	one_week_2 = days_remaining_2 <= 7
	# If one is during this week, and the next isn't
	if one_week_1 and not one_week_2:
		return -1
	if one_week_2 and not one_week_1:
		return 1
	# If they are both during the same week, but different categories
	category_priority = ['Test', 'HW', 'Extracurricular']
	if category_priority.index(task1[2]) != category_priority.index(task2[2]):
		return (category_priority.index(task1[2])
			- category_priority.index(task2[2]))
	return days_remaining_1 - days_remaining_2

def calendar_create(unsortedTasks, request_user):
	# Sort the tasks by priority
	tasks=[]
	for newtask in unsortedTasks:
		for index, oldtask in enumerate(tasks):
			if task_compare(newtask, oldtask) < 0:
				tasks.insert(index, newtask)
				break
		tasks.append(newtask)

	########################
	#PARSE PRELIMINARY INFO#
	########################
	user_info = UserInfo.objects.get(user__pk=request_user.pk)
	current_date = datetime.date.today()
	study_period = (user_info.study_start, user_info.study_end)
	study_days = [day.index for day in user_info.study_days.all()]
	#NOTE: date.weekday(), Monday is 0, Sunday is 6
	break_time = datetime.timedelta(minutes=user_info.break_time)

	#################
	#OUTPUT SCHEDULE#
	#################
	max_days = 0
	# Get the time available in a day
	day_time = datetime.datetime.combine(datetime.date.today(), study_period[1]) - datetime.datetime.combine(datetime.date.today(), study_period[0])
	# List of days with their respective activities
	active_days_list = []
	for task in tasks:
		days_left = 0
		days_left_date = current_date
		# Find the first available day to study
		while days_left_date.weekday() not in study_days:
			days_left_date += datetime.timedelta(days=1)
		# Count the number of available days to study
		while days_left_date < task[3]:
			# Increase days_left_date to next date based on available study days
			days_left_index = study_days.index(days_left_date.weekday())
			next_day_index = (days_left_index + 1) % len(study_days)
			date_difference = study_days[next_day_index] - study_days[days_left_index]
			days_left_date += datetime.timedelta(days=(date_difference % 7))
			days_left += 1
		# Copy the task timedelta into time_left
		time_left = +task[4]
		day_index = 0
		date_index = current_date
		# Go the first available study date
		while date_index.weekday() not in study_days:
			date_index += datetime.timedelta(days=1)
		full_days = []
		# while the time_left is greater than the default timedelta, 0
		while time_left > datetime.timedelta():
			if len(full_days) == days_left:
				# TODO: TASK CANNOT BE ALLOTTED
				break
			# If array for this day has not been created yet, create it
			if len(active_days_list) <= day_index:
				new_day = []
				active_days_list.append(new_day)
			# If day has available time to fit the task
			if scheduled_day_time(active_days_list[day_index])+task[5]+break_time <= day_time:
				active_days_list[day_index].append(task)
				# Subtract time left by attention span
				time_left -= task[5]
			elif day_index not in full_days:
				full_days.append(day_index)
			# Go to the next day and date
			date_index_index = study_days.index(date_index.weekday())
			next_day_index = (date_index_index + 1) % len(study_days)
			date_difference = study_days[next_day_index] - study_days[date_index_index]
			date_index += datetime.timedelta(days=(date_difference % 7))
			day_index += 1
			if date_index >= task[3]:
				# Reset day and date index
				date_index = current_date
				while date_index.weekday() not in study_days:
					date_index += datetime.timedelta(days=1)
				day_index = 0

	for day in active_days_list:
		# Assume day is sorted by priority
		task_index = 1
		while task_index < len(day):
			# Intertwine high priority tasks with low priority tasks
			low_priority_task = day.pop(len(day)-1)
			day.insert(task_index, low_priority_task)
			task_index += 1

	####################
	#CREATE TASK BLOCKS#
	####################

	# A task block is structured as follows: (Name, Start, End)
	task_blocks = []
	date_index = current_date
	# Go to the first study day
	while date_index.weekday() not in study_days:
		date_index += datetime.timedelta(days=1)
	for day in active_days_list:
		# Start tracking time at beginning of study period
		time_index = study_period[0]
		for task in day:
			# Get the full start time of the task from the current date and tiem
			task_start = datetime.datetime.combine(date_index, time_index)
			# Create the block with start and end time, factoring in break
			task_blocks.append((task_print(task), task_start, task_start + task[5] + break_time))
			# Hack to add timedelta to time index
			time_index = (datetime.datetime.combine(datetime.date.today(), time_index) + task[5] + break_time).time()
		# Go to the next day and date
		date_index_index = study_days.index(date_index.weekday())
		next_day_index = (date_index_index + 1) % len(study_days)
		date_difference = study_days[next_day_index] - study_days[date_index_index]
		date_index += datetime.timedelta(days=(date_difference % 7))

	# Return the list of individual task blocks
	return task_blocks

def getTasks(request_user):
	tasks_from_sql = Task.objects.filter(user__pk=request_user.pk)
	# Tasks are represented as ( Subject, Content, Category, Due Date, Total Time, Attention Span)
	tasks = []
	for task in tasks_from_sql:
		tasks.append((
			task.subject,
			task.content,
			task.category,
			task.due_date,
			datetime.timedelta(minutes=task.total_time),
			datetime.timedelta(minutes=task.attention_span)
			))
	return tasks

def tasksFeed(request):
	task_blocks = calendar_create(getTasks(request.user), request.user)
	json_list = []
	for task_block in task_blocks:
		title = task_block[0]
		start = task_block[1].strftime("%Y-%m-%dT%H:%M:%S")
		end = task_block[2].strftime("%Y-%m-%dT%H:%M:%S")
		allDay = False

		json_entry = {'title':title, 'start':start, 'end':end, 'allDay': allDay}
		json_list.append(json_entry)

	return HttpResponse(json.dumps(json_list), content_type='application/json')

@login_required
def newTask(request):
	if request.method == 'GET':
		form = TaskForm()
	else:
		form = TaskForm(request.POST)
		if form.is_valid():
			task = form.save(commit=False)
			task.user = request.user
			task.save()
			return redirect('/scheduler', permament=True)
	return render(request, 'scheduler/newtask.html', {'form':form})

def login(request):
	return render(request, 'scheduler/login.html', {'request':request})

@login_required
def home(request):
	tasks = getTasks(request.user)
	task_blocks = calendar_create(tasks, request.user)
	now = datetime.datetime.today()
	index = 0
	# Go until you reach the end of the list or find the current task
	while index < len(task_blocks) and task_blocks[index][2] < now:
		index += 1
	prev = "No Previous Task"
	if index > 0:
		prev = task_blocks[index-1][0]
	current = "No Current Task"
	next = "No Next Task"
	# Did the task at index start before now. We know it must end after now, so this means it is happening now
	if index < len(task_blocks) and task_blocks[index][1] < now:
		current = task_blocks[index][0]
		if index + 1 < len(task_blocks):
			next = task_blocks[index+1][0]
	elif index < len(task_blocks):
		next = task_blocks[index][0]

	context = {'tasks':tasks, 'prev':prev, 'current':current, 'next':next }
	return render(request, 'scheduler/home.html', context)
