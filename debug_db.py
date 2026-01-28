import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskorg.settings')
django.setup()

from organizer.models import Task
from django.contrib.auth.models import User

print("--- START DEBUG ---")
try:
    tasks = list(Task.objects.all())
    print(f"Total tasks in DB: {len(tasks)}")
    for t in tasks:
        try:
            print(f"ID: {t.id}, Title: {t.title}, User: {t.user.username if t.user else 'NULL'}")
        except Exception as e:
            print(f"ID: {t.id}, Error accessing user: {e}")
except Exception as e:
    print(f"Global error: {e}")
print("--- END DEBUG ---")
