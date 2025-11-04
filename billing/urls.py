from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('bill/<int:order_id>/', views.generate_bill, name='generate_bill'),
    path('payment/<int:bill_id>/', views.process_payment, name='process_payment'),
    path('receipt/<int:bill_id>/', views.generate_receipt, name='generate_receipt'),
]
