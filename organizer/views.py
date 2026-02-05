from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import json
from django.contrib.auth.models import User
from .models import Task, Subtask
from .forms import TaskForm

@login_required
def update_username(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_username = data.get('username')
            if new_username:
                # Check if username already exists
                if User.objects.filter(username=new_username).exclude(pk=request.user.pk).exists():
                    return JsonResponse({'status': 'error', 'message': 'Username already taken'}, status=400)
                
                request.user.username = new_username
                request.user.save()
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def dashboard(request):
    view = request.GET.get('view', 'all')
    tasks = Task.objects.filter(user=request.user, is_archived=False)
    
    if view == 'today':
        today = timezone.now().date()
        tasks = tasks.filter(due_date__date=today)
    elif view == 'overdue':
        tasks = tasks.filter(due_date__lt=timezone.now(), status__in=['Pending', 'In Progress'])
    
    tasks = tasks.order_by('-created_at')
    
    # Weekly Analytics Data (Monday to Sunday)
    today = timezone.localdate()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)         # Sunday
    
    # Get completions for the current week
    completions = Task.objects.filter(
        user=request.user,
        status='Completed',
        completed_at__date__gte=start_of_week,
        completed_at__date__lte=end_of_week
    )
    
    # Build chart data (always 7 days Mon-Sun)
    chart_data = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        count = completions.filter(completed_at__date=day).count()
        chart_data.append({
            'label': day.strftime('%a'),
            'count': count,
            'percent': 0 # Will calculate relative to max below
        })
    
    # Find max to calculate relative heights
    max_count = max([d['count'] for d in chart_data]) if chart_data else 0
    if max_count > 0:
        for d in chart_data:
            d['percent'] = int((d['count'] / max_count) * 100)
    else:
        # Default fallback if no data
        for d in chart_data:
            d['percent'] = 5
            
    # Determine greeting based on session flag set during login
    greeting = "Welcome" if request.session.get('is_first_login') else "Welcome back"
    
    context = {
        'tasks': tasks,
        'view': view,
        'greeting': greeting,
        'chart_data': chart_data,
        'weekly_total': completions.count()
    }
    
    return render(request, 'organizer/dashboard.html', context)

@login_required
def vault_view(request):
    tasks = Task.objects.filter(user=request.user, is_archived=True).order_by('-created_at')
    return render(request, 'organizer/archived.html', {'tasks': tasks})

@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            
            # Handle subtasks
            subtask_titles = request.POST.getlist('subtasks[]')
            subtask_completes = request.POST.getlist('subtask_completed[]')
            
            for i, title in enumerate(subtask_titles):
                if title.strip():
                    Subtask.objects.create(
                        task=task,
                        title=title.strip(),
                        is_completed=subtask_completes[i] == 'true'
                    )
            
            messages.success(request, 'Task created successfully!')
            return redirect('organizer_dashboard')
    else:
        initial_data = {}
        due_date_str = request.GET.get('due_date')
        if due_date_str:
            initial_data['due_date'] = due_date_str
        form = TaskForm(initial=initial_data)
    return render(request, 'organizer/task_form.html', {'form': form})

@login_required
def task_update(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            
            # Update subtasks: Simplest way is to remove old and add new
            task.subtasks.all().delete()
            subtask_titles = request.POST.getlist('subtasks[]')
            subtask_completes = request.POST.getlist('subtask_completed[]')
            
            for i, title in enumerate(subtask_titles):
                if title.strip():
                    Subtask.objects.create(
                        task=task,
                        title=title.strip(),
                        is_completed=subtask_completes[i] == 'true'
                    )
                    
            messages.success(request, 'Task updated successfully!')
            return redirect('organizer_dashboard')
    else:
        form = TaskForm(instance=task)
    return render(request, 'organizer/task_form.html', {'form': form, 'task': task})

@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect('organizer_dashboard')
    return render(request, 'organizer/task_confirm_delete.html', {'task': task})

@login_required
def task_complete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.status = 'Completed'
    task.completed_at = timezone.now()
    task.save()
    
    # Handle Recurrence
    if task.recurrence != 'none' and task.due_date:
        next_due = task.due_date
        if task.recurrence == 'daily':
            next_due += timedelta(days=1)
        elif task.recurrence == 'weekly':
            next_due += timedelta(weeks=1)
        elif task.recurrence == 'monthly':
            # Basic month increment
            month = next_due.month
            year = next_due.year + (month // 12)
            month = (month % 12) + 1
            day = min(next_due.day, 28)
            next_due = next_due.replace(year=year, month=month, day=day)
            
        new_task = Task.objects.create(
            user=task.user,
            title=task.title,
            description=task.description,
            category=task.category,
            priority=task.priority,
            status='Pending',
            due_date=next_due,
            recurrence=task.recurrence
        )
        
        # Clone subtasks
        for sub in task.subtasks.all():
            Subtask.objects.create(task=new_task, title=sub.title, is_completed=False)
            
        messages.success(request, f'Task completed! Next occurrence scheduled for {next_due.strftime("%b %d")}.')
    else:
        messages.success(request, f'Task "{task.title}" marked as complete!')
        
    return redirect('organizer_dashboard')

@login_required
def task_vault(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_archived = True
    task.save()
    messages.success(request, f'Task "{task.title}" archived successfully.')
    return redirect('organizer_dashboard')

@login_required
def task_unvault(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_archived = False
    task.save()
    messages.success(request, f'Task "{task.title}" restored from archives.')
    return redirect('organizer_dashboard')

@login_required
def export_tasks_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tasks.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Title', 'Description', 'Priority', 'Status', 'Category', 'Due Date', 'Created At'])
    
    tasks = Task.objects.filter(user=request.user, is_archived=False)
    for task in tasks:
        writer.writerow([
            task.title,
            task.description,
            task.priority,
            task.status,
            task.category,
            task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
            task.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response

@login_required
def today_view(request):
    today = timezone.localdate()
    tasks = Task.objects.filter(
        Q(created_at__date=today) | Q(due_date__date=today) | ~Q(status='Completed'),
        user=request.user, 
        is_archived=False
    ).distinct().order_by('priority')
    return render(request, 'organizer/today.html', {'tasks': tasks})

# @login_required
# def calendar_view(request):
#     tasks = Task.objects.filter(
#         user=request.user, 
#         is_archived=False,
#         due_date__isnull=False
#     ).order_by('due_date')
#     return render(request, 'organizer/calendar.html', {'tasks': tasks})
