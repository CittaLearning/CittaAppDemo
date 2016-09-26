from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout as userlogout
from django.utils import timezone
from .models import UserInfo, Task
from .forms import TaskForm, UserInfoForm, ProgressForm, EditTaskForm
import datetime
import json
import re

def task_print(task):
	'''Convert a task tuple into a readable string'''
	return (task[0] + ' ' + task[2] + ': ' + task[1]
		+ ' Due: ' + task[3].strftime('%m/%d/%y'))

def scheduled_day_time(day, break_time):
	'''Get the total amount of time currently scheduled in a day.
	This takes a list of task tuples, as well as the break time between them'''
	total_time = datetime.timedelta()
	for task in day:
		total_time += task[5] + break_time # Add the task attn span to the timedelta
	return total_time

# Comparator for task objects
def task_compare(task1, task2):
	'''Comparator for task tuples'''
	current_date = timezone.now().date()
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
	'''Create a list of task blocks from a list of unsorted task tuples and a user'''
	# Sort the tasks by priority
	tasks=[]
	for newtask in unsortedTasks:
		added=False
		for index, oldtask in enumerate(tasks):
			if task_compare(newtask, oldtask) < 0:
				tasks.insert(index, newtask)
				added=True
				break
		if not added:
			tasks.append(newtask)

	########################
	#PARSE PRELIMINARY INFO#
	########################
	user_info = UserInfo.objects.get(user__pk=request_user.pk)
	current_date = user_info.mock_date
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
	elapsed_time = 0
	print study_period[0], user_info.mock_time
	if study_period[0] < user_info.mock_time:
		start = datetime.datetime.combine(datetime.date.today(), study_period[0])
		current = datetime.datetime.combine(datetime.date.today(), user_info.mock_time)
		elapsed_time = (current - start).total_seconds() / 60
		print elapsed_time
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
		percent_left = 100 - task[6]
		time_left = task[4] * percent_left
		time_left /= 100
		print task[0], task[4], time_left
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
			# Calculate time elapsed from day start to mock time if date is current day
			current_elapsed = datetime.timedelta()
			if date_index == current_date:
				current_elapsed = datetime.timedelta(minutes=elapsed_time)
			# If day has available time to fit the task
			if scheduled_day_time(active_days_list[day_index], break_time)+task[5]+break_time+current_elapsed <= day_time:
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
		time_index = (datetime.datetime.combine(timezone.now().date(),study_period[0]) + (datetime.timedelta(minutes=elapsed_time) if date_index == current_date else datetime.timedelta())).time()
		for task in day:
			# Get the full start time of the task from the current date and tiem
			task_start = datetime.datetime.combine(date_index, time_index)
			# Create the block with start and end time, factoring in break
			task_blocks.append((task[0] + " " + task[1], task_start, task_start + task[5], task[7]))
			task_blocks.append(("Break", task_start+task[5], task_start+task[5]+break_time))
			# Hack to add timedelta to time index
			time_index = (datetime.datetime.combine(timezone.now().date(), time_index) + task[5] + break_time).time()
		#Remove break at the end of the day
		task_blocks.pop()
		# Go to the next day and date
		date_index_index = study_days.index(date_index.weekday())
		next_day_index = (date_index_index + 1) % len(study_days)
		date_difference = study_days[next_day_index] - study_days[date_index_index]
		date_index += datetime.timedelta(days=(date_difference % 7))

	# Return the list of individual task blocks
	return task_blocks

def getTasks(request_user):
	'''Get the relevant tasks for the current user'''
	tasks_from_sql = Task.objects.filter(user__pk=request_user.pk)
	# Tasks are represented as ( Subject, Content, Category, Due Date, Total Time, Attention Span, Amount Done)
	tasks = []
	for task in tasks_from_sql:
		tasks.append((
			task.subject,
			task.content,
			task.category,
			task.due_date,
			datetime.timedelta(minutes=task.total_time),
			datetime.timedelta(minutes=task.attention_span),
			task.amount_done,
			task.pk
			))
	return tasks

def tasksFeed(request):
	'''Get the json calendar for the current user'''
	userinfo = UserInfo.objects.get(user__pk=request.user.pk)
	return HttpResponse(userinfo.json_calendar, content_type='application/json')

@login_required
def progress(request, key):
	'''View for updating the progress of a task'''
	task = Task.objects.get(pk=key) #TODO: Add safety check for task existing
	if task.user.pk != request.user.pk:
		return redirect('home', permanent=True)
	if request.method == 'GET':
		form = ProgressForm(instance=task)
	else:
		form = ProgressForm(request.POST)
		if form.is_valid():
			task.amount_done = form.cleaned_data['amount_done']
			task.save()
			return redirect('home', permanent=True)
	taskname = task.subject + " " + task.category + ": " + task.content
	return render(request, 'scheduler/progress.html', {'form':form, 'key':key, 'name':taskname})

@login_required
def editTask(request, key):
	'''View for editing a task'''
	task = Task.objects.get(pk=key) #TODO: Add safety check for task existing
	userinfo = UserInfo.objects.get(user__pk=request.user.pk)
	if task.user.pk != request.user.pk:
		return redirect('home', permanent=True)
	if request.method == 'GET':
		form = EditTaskForm(instance=task)
	else:
		form = EditTaskForm(request.POST)
		if form.is_valid():
			task = form.save(commit=False)
			task.user = request.user
			task.pk = key
			task.save()
		return redirect('reschedule', permanent=True)
	taskname = task.subject + " " + task.category + ": " + task.content
	return render(request, 'scheduler/edittask.html', {'form':form, 'key':key, 'name':taskname})

@login_required
def deleteTask(request, key):
	'''View for deleting a task'''
	task = Task.objects.get(pk=key) #TODO: Add safety check for task existing
	if task.user.pk != request.user.pk:
		return redirect('home', permanent=True)
	task.delete()
	return redirect('reschedule', permanent=True)

@login_required
def newTask(request):
	'''View for creating a task'''
	if request.method == 'GET':
		form = TaskForm()
	else:
		form = TaskForm(request.POST)
		if form.is_valid():
			task = form.save(commit=False)
			task.user = request.user
			task.save()
			return redirect('reschedule', permanent=True)
	return render(request, 'scheduler/newtask.html', {'form':form})

def logout(request):
	'''View for logging a user out'''
	userlogout(request)
	return redirect('login', permanent=True)

def login(request):
	'''View for logging a user in'''
	return render(request, 'scheduler/login.html', {'request':request})

@login_required
def setUser(request):
	'''View for setting up a user'''
	if request.method == 'GET':
		userinfo = UserInfo.objects.filter(user__pk=request.user.pk)
		if len(userinfo)==0:
			form = UserInfoForm()
		else:
			form = UserInfoForm(instance=userinfo[0])
	else:
		form = UserInfoForm(request.POST)
		if form.is_valid():
			userinfoF = form.save(commit=False)
			userinfoF.user = request.user
			userinfoF.save()
			userinfoF.study_days = form.cleaned_data['study_days']
			userinfoF.save()
			return redirect('reschedule', permanent=True)
	return render(request, 'scheduler/setuser.html', {'form':form})

@login_required
def reschedule(request):
	'''View for rescheduling a user's clanedar'''
	print "Reschedule"
	userinfo = UserInfo.objects.get(user__pk=request.user.pk)
	userinfo.mock_date = timezone.now().date()
	userinfo.mock_time = timezone.now().time()
	userinfo.save()
	task_blocks = calendar_create(getTasks(request.user), request.user)
	#Save the calculated data into the user data
	json_list = []
	for task_block in task_blocks:
		title = task_block[0]
		color = "Light blue" if title == "Break" else "Yellow"
		start = task_block[1].strftime("%Y-%m-%dT%H:%M:%S")
		end = task_block[2].strftime("%Y-%m-%dT%H:%M:%S")
		allDay = False
		pk = task_block[3] if len(task_block) == 4 else None

		json_entry = {'title':title, 'start':start, 'end':end, 'allDay': allDay, 'color':color, 'pk':pk}
		json_list.append(json_entry)
	userinfo.json_calendar = json.dumps(json_list)
	userinfo.save()
	return redirect('home', permanent=True)

@login_required
def home(request):
	'''Home view'''
	#Check if user has associated userinfo
	if not list(UserInfo.objects.filter(user__pk=request.user.pk)):
		return redirect('setuser', permanent=True)
	tasks = getTasks(request.user)
	userinfo = UserInfo.objects.get(user__pk=request.user.pk)
	#Tasks are listed in order, so get the first two
	blocks = calendar_create(tasks, request.user)
	current = None
	nextT = None
	now = timezone.now()
	#Find the first task that ends after the current time
	index=0
	if len(blocks) == 0:
		current = None
		nextT = None
		onBreak = True
		timer = False
		timing = 0
	elif len(blocks) == 1:
		current = None
		nextT = blocks[0]
		onBreak = True
		timer = False
		timing = 0
	else:
		while blocks[index][2] <= now:
			index += 1
		first = blocks[index]
		second = blocks[index+1]
		#Case1: First task starts after now
		if first[1] > now:
			nextT = first
		#Case2: First task already started
		else:
			current = first
			nextT = second
		#Check if user is current in a break or not
		onBreak = nextT[0] != "Break"
		timer = True
		#Determine whether to countdown to end of current task or beginning of next task
		if onBreak:
			#Count down to beginning of next task
			timing = (nextT[1] - now).total_seconds()
		else:
			#Count down to end of current task
			timing = (current[2] - now).total_seconds()
	#Reduce tasks to necessary data
	tasks = [(task[0], task[1], task[2], task[3], task[7], task[6]-100) for task in tasks]
	context = {'tasks':tasks, 'current':current, 'next':nextT, 'onBreak':onBreak, 'timing':timing, 'timer':timer}
	return render(request, 'scheduler/home.html', context)
