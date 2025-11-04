from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Attendance, Shift, TipDistribution


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active_duty')
    list_filter = ('role', 'is_active', 'is_active_duty')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Staff Information', {'fields': ('role', 'phone', 'employee_id', 'is_active_duty', 'profile_picture')}),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'check_in', 'check_out', 'duration')
    list_filter = ('check_in',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'shift_type', 'start_time', 'end_time', 'is_active')
    list_filter = ('shift_type', 'is_active')
    filter_horizontal = ('assigned_users',)


@admin.register(TipDistribution)
class TipDistributionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'amount', 'total_tips')
    list_filter = ('date',)
    search_fields = ('user__username',)
