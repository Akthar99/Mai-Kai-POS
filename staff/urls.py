from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('list/', views.staff_list, name='staff_list'),
    path('attendance/', views.attendance_list, name='attendance_list'),
]
