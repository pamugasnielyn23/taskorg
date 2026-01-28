import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskorg.settings')
django.setup()

from organizer.models import Task
ids = list(Task.objects.values_list('id', flat=True))
print(f"EXISTING_IDS: {ids}")
