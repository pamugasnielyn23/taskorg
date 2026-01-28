from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

PRIORITY_CHOICES = [
    ('Low', 'Low'),
    ('Medium', 'Medium'),
    ('High', 'High'),
]

STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('In Progress', 'In Progress'),
    ('Completed', 'Completed'),
]

RECURRENCE_CHOICES = [
    ('none', 'No Repeat'),
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
]

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    due_date = models.DateTimeField(null=True, blank=True)
    reminder_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New fields
    is_archived = models.BooleanField(default=False)
    recurrence = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, default='none')
    
    @property
    def is_due_soon(self):
        if self.due_date:
            now = timezone.now()
            return now <= self.due_date <= now + timedelta(hours=24)
        return False
    
    @property
    def is_overdue(self):
        if self.due_date and self.status != 'Completed':
            return timezone.now() > self.due_date
        return False
    
    @property
    def is_today(self):
        if self.due_date:
            return self.due_date.date() == timezone.now().date()
        return False

    @property
    def subtask_stats(self):
        total = self.subtasks.count()
        completed = self.subtasks.filter(is_completed=True).count()
        return {
            'total': total,
            'completed': completed,
            'percent': int(completed / total * 100) if total > 0 else 0
        }

    def __str__(self):
        return self.title


class Subtask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
