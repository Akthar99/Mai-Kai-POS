from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Table
from .forms import TableForm


@login_required
def table_list(request):
    tables = Table.objects.filter(is_active=True).order_by('table_number')
    
    # Calculate statistics
    available_count = tables.filter(status='available').count()
    occupied_count = tables.filter(status='occupied').count()
    reserved_count = tables.filter(status='reserved').count()
    
    context = {
        'tables': tables,
        'available_count': available_count,
        'occupied_count': occupied_count,
        'reserved_count': reserved_count,
    }
    
    return render(request, 'tables/table_list.html', context)


@login_required
def table_detail(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    return render(request, 'tables/table_detail.html', {'table': table})


@login_required
def table_create(request):
    """Create a new table - Admin only"""
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to create tables.')
        return redirect('tables:table_list')
    
    if request.method == 'POST':
        form = TableForm(request.POST)
        if form.is_valid():
            table = form.save()
            messages.success(request, f'Table {table.table_number} created successfully!')
            return redirect('tables:table_list')
    else:
        form = TableForm()
    
    return render(request, 'tables/table_form.html', {'form': form, 'action': 'Create'})


@login_required
def table_edit(request, table_id):
    """Edit an existing table - Admin only"""
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to edit tables.')
        return redirect('tables:table_list')
    
    table = get_object_or_404(Table, id=table_id)
    
    if request.method == 'POST':
        form = TableForm(request.POST, instance=table)
        if form.is_valid():
            table = form.save()
            messages.success(request, f'Table {table.table_number} updated successfully!')
            return redirect('tables:table_list')
    else:
        form = TableForm(instance=table)
    
    return render(request, 'tables/table_form.html', {'form': form, 'action': 'Edit', 'table': table})


@login_required
def table_delete(request, table_id):
    """Soft delete a table - Admin only"""
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to delete tables.')
        return redirect('tables:table_list')
    
    table = get_object_or_404(Table, id=table_id)
    
    if request.method == 'POST':
        table.is_active = False
        table.save()
        messages.success(request, f'Table {table.table_number} deleted successfully!')
        return redirect('tables:table_list')
    
    return render(request, 'tables/table_confirm_delete.html', {'table': table})


@login_required
def table_toggle_status(request, table_id):
    """Toggle table status via AJAX - For quick status changes"""
    if request.method == 'POST':
        table = get_object_or_404(Table, id=table_id)
        new_status = request.POST.get('status')
        
        if new_status in ['available', 'occupied', 'reserved', 'cleaning']:
            table.status = new_status
            table.save()
            return JsonResponse({'success': True, 'status': table.get_status_display()})
        
        return JsonResponse({'success': False, 'error': 'Invalid status'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def reservation_list(request):
    from .models import Reservation
    reservations = Reservation.objects.order_by('reservation_date', 'reservation_time')
    return render(request, 'tables/reservation_list.html', {'reservations': reservations})


@login_required
def waitlist_view(request):
    from .models import Waitlist
    waitlist = Waitlist.objects.filter(status='waiting').order_by('created_at')
    return render(request, 'tables/waitlist.html', {'waitlist': waitlist})
