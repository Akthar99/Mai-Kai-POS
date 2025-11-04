from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Attendance


def user_login(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Mark user as on duty
            user.is_active_duty = True
            user.save()
            # Create attendance record
            Attendance.objects.create(user=user)
            messages.success(request, f'Welcome back, {user.get_display_name()}!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'staff/login.html')


@login_required
def user_logout(request):
    """Logout view"""
    # Mark user as off duty
    request.user.is_active_duty = False
    request.user.save()
    
    # Update attendance checkout time
    last_attendance = Attendance.objects.filter(
        user=request.user,
        check_out__isnull=True
    ).first()
    if last_attendance:
        from django.utils import timezone
        last_attendance.check_out = timezone.now()
        last_attendance.save()
    
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('staff:login')


@login_required
def staff_list(request):
    """List all staff members"""
    staff = User.objects.all()
    return render(request, 'staff/staff_list.html', {'staff': staff})


@login_required
def attendance_list(request):
    """List attendance records"""
    attendances = Attendance.objects.select_related('user').order_by('-check_in')[:50]
    return render(request, 'staff/attendance_list.html', {'attendances': attendances})
