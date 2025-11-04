from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('loyalty/', views.loyalty_program, name='loyalty_program'),
]
