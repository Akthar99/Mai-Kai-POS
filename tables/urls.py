from django.urls import path
from . import views

app_name = 'tables'

urlpatterns = [
    path('', views.table_list, name='table_list'),
    path('create/', views.table_create, name='table_create'),
    path('<int:table_id>/', views.table_detail, name='table_detail'),
    path('<int:table_id>/edit/', views.table_edit, name='table_edit'),
    path('<int:table_id>/delete/', views.table_delete, name='table_delete'),
    path('<int:table_id>/toggle-status/', views.table_toggle_status, name='table_toggle_status'),
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('waitlist/', views.waitlist_view, name='waitlist'),
]
