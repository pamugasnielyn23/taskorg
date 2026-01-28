import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskorg.settings')
django.setup()

from organizer.models import Task
from django.contrib.auth.models import User

print("--- TASK LIST ---")
for t in Task.objects.all():
    print(f"ID: {t.id}, Title: {t.title}, User: {t.user.username}")

print("\n--- USER LIST ---")
for u in User.objects.all():
    print(f"Username: {u.username}")
