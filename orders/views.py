from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def order_list(request):
    from .models import Order
    
    # Get status filter from query parameter
    status_filter = request.GET.get('status', 'all')
    
    # Filter orders based on status
    orders = Order.objects.select_related('table', 'customer').order_by('-created_at')
    
    if status_filter and status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    orders = orders[:50]
    
    # Calculate order statistics
    pending_count = Order.objects.filter(status='pending').count()
    preparing_count = Order.objects.filter(status='preparing').count()
    ready_count = Order.objects.filter(status='ready').count()
    completed_count = Order.objects.filter(status='completed').count()
    
    context = {
        'orders': orders,
        'pending_count': pending_count,
        'preparing_count': preparing_count,
        'ready_count': ready_count,
        'completed_count': completed_count,
        'current_status': status_filter,
    }
    
    # If HTMX request, return only the table content
    if request.headers.get('HX-Request'):
        return render(request, 'orders/order_list_table.html', context)
    
    return render(request, 'orders/order_list.html', context)


@login_required
def create_order(request):
    # Order creation logic with HTMX
    return render(request, 'orders/create_order.html')


@login_required
def order_detail(request, order_id):
    from .models import Order
    from django.shortcuts import get_object_or_404
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def update_order(request, order_id):
    # Order update logic
    return render(request, 'orders/update_order.html')


@login_required
def cancel_order(request, order_id):
    # Order cancellation logic
    return render(request, 'orders/cancel_order.html')
