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
import inspect


def task_print(task):
    '''Convert a task tuple into a readable string'''
    return (task[0] + ' ' + task[2] + ': ' + task[1]
            + ' Due: ' + task[3].strftime('%m/%d/%y'))


def scheduled_day_time(day, break_time):
    '''Get the total amount of time currently scheduled in a day.
	This takes a list of task tuples, as well as the break time between them'''
    total_time = datetime.timedelta()
    for task in day:
        if type(task) is datetime.date:
            continue

        total_time += task[5] + break_time  # Add the task attn span to the timedelta
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


def dump_tasks(tasks):
    print "dump_tasks"
    print inspect.stack()[1][3]
    for task in tasks:
        print task_print(task)


def jump_next_date(study_days, days_left_date):
    # Increase days_left_date to next date based on available study days
    days_left_index = study_days.index(days_left_date.weekday())
    if len(study_days) == 1:
        days_left_date += datetime.timedelta(days=7)
    else:
        next_day_index = (days_left_index + 1) % len(study_days)
        date_difference = study_days[next_day_index] - study_days[days_left_index]
        days_left_date += datetime.timedelta(days=(date_difference % 7))
    return days_left_date


def get_first_study_day(current_date, study_days):
    date_index = current_date
    while date_index.weekday() not in study_days:
        date_index += datetime.timedelta(days=1)
    return date_index


def calendar_create(unsortedTasks, request_user):
    '''Create a list of task blocks from a list of unsorted task tuples and a user'''
    # Sort the tasks by priority
    tasks = []
    for newtask in unsortedTasks:
        added = False
        for index, oldtask in enumerate(tasks):
            if task_compare(newtask, oldtask) < 0:
                tasks.insert(index, newtask)
                added = True
                break
        if not added:
            tasks.append(newtask)

    dump_tasks(tasks)

    ########################
    # PARSE PRELIMINARY INFO#
    ########################
    user_info = UserInfo.objects.get(user__pk=request_user.pk)
    current_date = user_info.mock_date
    study_period = (user_info.study_start, user_info.study_end)
    study_days = [day.index for day in user_info.study_days.all()]
    # NOTE: date.weekday(), Monday is 0, Sunday is 6
    break_time = datetime.timedelta(minutes=user_info.break_time)

    #################
    # OUTPUT SCHEDULE#
    #################
    # Get the time available in a day
    day_time = datetime.datetime.combine(datetime.date.today(), study_period[1]) - datetime.datetime.combine(
        datetime.date.today(), study_period[0])
    elapsed_time = 0
    if user_info.mock_time > study_period[0]:
        start = datetime.datetime.combine(datetime.date.today(), study_period[0])
        current = datetime.datetime.combine(datetime.date.today(), user_info.mock_time)
        elapsed_time = (current - start).total_seconds() / 60

    # List of days with their respective activities
    active_days_list = []
    for task in tasks:
        days_left = 0
        days_left_date = get_first_study_day(current_date, study_days)

        while days_left_date < task[3]:
            days_left_date = jump_next_date(study_days, days_left_date)
            days_left += 1
        print(' task %s days_left %d days_left_date %s ' % (task[0], days_left, days_left_date))
        percent_left = 100 - task[6]
        time_left = task[4] * percent_left
        time_left /= 100

        day_index = 0
        # Go the first available study date
        date_index = get_first_study_day(current_date, study_days)
        if date_index == current_date:
            # On current date if the current time is greater than study period,
            # then skip the current day.
            if day_time <= (break_time + datetime.timedelta(minutes=elapsed_time) + task[5]):
                date_index = jump_next_date(study_days, date_index)
                elapsed_time = 0

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
                active_days_list[day_index].append(date_index)

            print('task %s : day_time %s day index %d time left %d date %s' % (task[0], day_time,
                                                                               day_index,
                                                                               time_left.seconds / 60, date_index))
            # If day has available time to fit the task
            # FIXME : on the first day check should be elapsed + attention span <= day_time.
            required_day_time = scheduled_day_time(active_days_list[day_index], break_time) + \
                                break_time + task[5] + \
                                (datetime.timedelta(
                                    minutes=elapsed_time) if date_index == current_date else datetime.timedelta())

            if required_day_time <= day_time:
                active_days_list[day_index].append(task)
                # Subtract time left by attention span
                time_left -= task[5]
            elif day_index not in full_days:
                full_days.append(day_index)
                print("Append date %s:: day index %d" % (date_index, day_index))
                # Go to the next day and date
            date_index = jump_next_date(study_days, date_index)
            day_index += 1
            if date_index > task[3]:
                date_index = get_first_study_day(current_date, study_days)
                day_index = 0

    for day in active_days_list:
        # Assume day is sorted by priority
        task_index = 1
        while task_index < len(day):
            # Intertwine high priority tasks with low priority tasks
            low_priority_task = day.pop(len(day) - 1)
            if type(low_priority_task) is datetime.date:
                continue
            day.insert(task_index, low_priority_task)
            task_index += 1

    ####################
    # CREATE TASK BLOCKS#
    ####################

    # A task block is structured as follows: (Name, Start, End)
    task_blocks = []
    for day in active_days_list:
        # Start tracking time at beginning of study period
        date_index = day[0]
        time_index = (datetime.datetime.combine(timezone.now().date(), study_period[0]) + (
            datetime.timedelta(minutes=elapsed_time) if date_index == current_date else datetime.timedelta())).time()
        for task in day:
            if type(task) is datetime.date:
                continue
            # print(" task %s time index %d:%d:%d" % (task, time_index.hour, time_index.minute, time_index.second))
            # Get the full start time of the task from the current date and item
            task_start = datetime.datetime.combine(date_index, time_index)
            # Create the block with start and end time, factoring in break
            task_blocks.append((task[0] + " " + task[1], task_start, task_start + task[5], task[7]))
            task_blocks.append(("Break", task_start + task[5], task_start + task[5] + break_time))
            # Hack to add timedelta to time index
            time_index = (datetime.datetime.combine(timezone.now().date(), time_index) + task[5] + break_time).time()
        # Remove break at the end of the day
        task_blocks.pop()

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
    task = Task.objects.get(pk=key)  # TODO: Add safety check for task existing
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
    return render(request, 'scheduler/progress.html', {'form': form, 'key': key, 'name': taskname})


@login_required
def editTask(request, key):
    '''View for editing a task'''
    task = Task.objects.get(pk=key)  # TODO: Add safety check for task existing
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
    return render(request, 'scheduler/edittask.html', {'form': form, 'key': key, 'name': taskname})


@login_required
def deleteTask(request, key):
    '''View for deleting a task'''
    task = Task.objects.get(pk=key)  # TODO: Add safety check for task existing
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
    return render(request, 'scheduler/newtask.html', {'form': form})


def logout(request):
    '''View for logging a user out'''
    userlogout(request)
    return redirect('login', permanent=True)


def login(request):
    '''View for logging a user in'''
    return render(request, 'scheduler/login.html', {'request': request})


@login_required
def setUser(request):
    '''View for setting up a user'''
    if request.method == 'GET':
        userinfo = UserInfo.objects.filter(user__pk=request.user.pk)
        if len(userinfo) == 0:
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
    return render(request, 'scheduler/setuser.html', {'form': form})


@login_required
def reschedule(request):
    '''View for rescheduling a user's clanedar'''
    print "Reschedule"
    userinfo = UserInfo.objects.get(user__pk=request.user.pk)
    userinfo.mock_date = timezone.now().date()
    userinfo.mock_time = timezone.now().time()
    userinfo.save()
    task_blocks = calendar_create(getTasks(request.user), request.user)
    # Save the calculated data into the user data
    json_list = []
    for task_block in task_blocks:
        title = task_block[0]
        color = "Light blue" if title == "Break" else "Yellow"
        start = task_block[1].strftime("%Y-%m-%dT%H:%M:%S")
        end = task_block[2].strftime("%Y-%m-%dT%H:%M:%S")
        allDay = False
        pk = task_block[3] if len(task_block) == 4 else None

        json_entry = {'title': title, 'start': start, 'end': end, 'allDay': allDay, 'color': color, 'pk': pk}
        json_list.append(json_entry)
    userinfo.json_calendar = json.dumps(json_list)
    userinfo.save()
    print('userinfo.jsoncalendar %s' % json.dumps(json_list))
    return redirect('home', permanent=True)


@login_required
def home(request):
    '''Home view'''
    # Check if user has associated userinfo
    if not list(UserInfo.objects.filter(user__pk=request.user.pk)):
        return redirect('setuser', permanent=True)
    tasks = getTasks(request.user)
    userinfo = UserInfo.objects.get(user__pk=request.user.pk)
    # Tasks are listed in order, so get the first two
    blocks = calendar_create(tasks, request.user)
    current = None
    nextT = None
    now = timezone.now()

    print('number of blocks %d' % len(blocks))
    # Case: No tasks or no tasks that end after current time
    if len(blocks) == 0 || blocks[-1][2] > now:
        current = None
        nextT = None
        onBreak = True
        timer = False
        timing = 0
    else:
        # There is at least one task ending after the current time
        # Find the first such task
        index = 0
        while blocks[index][2] <= now:
            index += 1
        first = blocks[index] # First block ending after now

        # Case: Only one task ending after now
        if index == len(blocks) - 1:
            # Check if task is current task or future task
            if first[1] < now:
                current = first
                timer = True # Show timer
                onBreak = (current[0] == "Break") # Check if currently on break, should be false
                timing = (current[2] - now).total_seconds() # Time until end of current task
            else:
                nextT = first
                timer = False # No current task for timer
                timing = 0
                onBreak = True

        else: # At least two tasks ending after current time
            # Check if task is current task or future task
            if first[1] < now:
                current = first
                nextT = blocks[index + 1] # Get the task after the current task
                timer = True
                onBreak = (current[0] == "Break") # Check if currently on break
                timing = (current[2] - now).total_seconds() # Time until end of current task
            else:
                nextT = first
                timer = False # No current task for timer
                timing = 0
                onBreak = True

    # Reduce tasks to necessary data
    tasks = [(task[0], task[1], task[2], task[3], task[7], task[6] - 100) for task in tasks]
    context = {'tasks': tasks, 'current': current, 'next': nextT, 'onBreak': onBreak, 'timing': timing, 'timer': timer}
    return render(request, 'scheduler/home.html', context)
