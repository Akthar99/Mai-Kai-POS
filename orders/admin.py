from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'order_type', 'status', 'table', 'total', 'created_at')
    list_filter = ('order_type', 'status', 'created_at')
    search_fields = ('order_number',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'combo', 'quantity', 'total_price')


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'changed_by', 'created_at')
    list_filter = ('status', 'created_at')
