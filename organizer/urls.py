from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='organizer_dashboard'),
    path('add/', views.task_create, name='task_create'),
    path('edit/<int:task_id>/', views.task_update, name='task_update'),
    path('delete/<int:task_id>/', views.task_delete, name='task_delete'),
    path('complete/<int:task_id>/', views.task_complete, name='task_complete'),
    path('vault/<int:task_id>/', views.task_vault, name='task_vault'),
    path('unvault/<int:task_id>/', views.task_unvault, name='task_unvault'),
    path('vault/', views.vault_view, name='vault_list'),
    path('export/csv/', views.export_tasks_csv, name='export_csv'),
    path('today/', views.today_view, name='today_view'),
    path('update-username/', views.update_username, name='update_username'),
]
