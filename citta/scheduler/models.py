from django.db import models
from django.contrib.auth.models import User


class Day(models.Model):
    index = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    break_time = models.IntegerField()
    study_start = models.TimeField()
    study_end = models.TimeField()
    break_time = models.IntegerField()
    study_days = models.ManyToManyField(Day)
    mock_date = models.DateField(auto_now=True)
    mock_time = models.TimeField(auto_now=True)
    json_calendar = models.TextField(default="")


class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=20)
    content = models.CharField(max_length=100)
    category = models.CharField(
        max_length=20,
        choices=[
            ('HW', 'HW'),
            ('Test', 'Test'),
            ('Extracurricular', 'Extracurricular')
        ],
        default='HW'
    )
    due_date = models.DateField()
    total_time = models.IntegerField()
    attention_span = models.IntegerField()
    amount_done = models.IntegerField(default=0)

    def __str__(self):
        return self.subject + " " + self.category + ": " + self.content
