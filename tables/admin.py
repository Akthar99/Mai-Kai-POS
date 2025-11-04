from django.contrib import admin
from .models import Table, TableCombination, Reservation, Waitlist


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'capacity', 'status', 'location', 'assigned_server')
    list_filter = ('status', 'location')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('reservation_number', 'customer_name', 'table', 'reservation_date', 'reservation_time', 'status')
    list_filter = ('status', 'reservation_date')


@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'party_size', 'status', 'created_at')
    list_filter = ('status',)
