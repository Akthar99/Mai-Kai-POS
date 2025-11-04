from django.contrib import admin
from .models import Payment, Bill, SplitPayment, Refund, Receipt


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'order', 'payment_method', 'amount', 'status')
    list_filter = ('payment_method', 'status')


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'order', 'total_amount', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at')
