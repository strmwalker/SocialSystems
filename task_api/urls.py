"""task_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from mobile_api.views import admin_add_task, admin_list_tasks, admin_delete_task, \
    user_list_tasks, user_show_task_steps, user_complete_task_step, get_task

urlpatterns = {
    path('tasks/task', get_task),
    path('admin/add', admin_add_task),
    path('admin/list', admin_list_tasks),
    path('admin/delete', admin_delete_task),
    path('user/list', user_list_tasks),
    path('user/task', user_show_task_steps),
    path('user/do', user_complete_task_step),
}
