from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import timedelta
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)


@login_required
def sales(request):
    """Main POS/Sales page - Table selection"""
    from tables.models import Table
    
    tables = Table.objects.filter(is_active=True).order_by('table_number')
    
    # Calculate table statistics
    available_count = tables.filter(status='available').count()
    occupied_count = tables.filter(status='occupied').count()
    reserved_count = tables.filter(status='reserved').count()
    
    context = {
        'tables': tables,
        'available_count': available_count,
        'occupied_count': occupied_count,
        'reserved_count': reserved_count,
    }
    
    return render(request, 'core/sales.html', context)


@login_required
def dashboard(request):
    """Main dashboard view"""
    from orders.models import Order
    from tables.models import Table
    from billing.models import Payment
    from inventory.models import StockItem
    from datetime import datetime
    
    # Get today's date in the local timezone
    now = timezone.now()
    today = now.date()
    
    # Today's statistics
    today_orders = Order.objects.filter(created_at__date=today)
    
    # Calculate revenue from completed payments today
    # Use timezone-aware comparison to avoid date mismatch issues
    today_revenue = Payment.objects.filter(
        status='completed',
        completed_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Table status
    occupied_tables = Table.objects.filter(status='occupied').count()
    total_tables = Table.objects.filter(is_active=True).count()
    
    # Recent orders
    recent_orders = Order.objects.select_related(
        'table', 'customer', 'created_by'
    ).order_by('-created_at')[:10]
    
    # Low stock items
    from django.db.models import F
    low_stock_items = StockItem.objects.filter(
        current_quantity__lte=F('min_quantity')
    )[:10]
    
    # Weekly revenue chart data (last 7 days)
    week_ago = today - timedelta(days=6)
    daily_revenue = []
    for i in range(7):
        day = week_ago + timedelta(days=i)
        revenue = Payment.objects.filter(
            status='completed'
        ).filter(
            Q(completed_at__date=day) | Q(created_at__date=day)
        ).aggregate(total=Sum('amount'))['total'] or 0
        daily_revenue.append({
            'date': day.strftime('%a'),
            'revenue': float(revenue)
        })
    
    context = {
        'today_orders_count': today_orders.count(),
        'today_revenue': today_revenue,
        'occupied_tables': occupied_tables,
        'total_tables': total_tables,
        'recent_orders': recent_orders,
        'low_stock_items': low_stock_items,
        'daily_revenue': daily_revenue,
    }
    
    # Return partial templates for HTMX requests
    if request.headers.get('HX-Request'):
        section = request.GET.get('section')
        if section == 'stats':
            return render(request, 'core/partials/dashboard_stats.html', context)
        elif section == 'recent_orders':
            return render(request, 'core/partials/dashboard_recent_orders.html', context)
        elif section == 'low_stock':
            return render(request, 'core/partials/dashboard_low_stock.html', context)
    
    return render(request, 'core/dashboard.html', context)


def home(request):
    """Home page - redirects to dashboard if logged in"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return redirect('staff:login')


@login_required
def order_entry(request, table_id):
    """Order entry interface for a specific table"""
    from tables.models import Table
    from orders.models import Order
    from menu.models import MenuItem, Category
    
    table = get_object_or_404(Table, id=table_id, is_active=True)
    
    # Get or create order for this table
    order = Order.objects.filter(
        table=table,
        status__in=['pending', 'confirmed', 'preparing']
    ).first()
    
    # Get order items if order exists
    order_items = []
    if order:
        order_items = order.items.select_related('menu_item').all()
    
    # Get all menu items and categories
    categories = Category.objects.filter(is_active=True).order_by('name')
    menu_items = MenuItem.objects.filter(is_available=True).select_related('category')
    
    context = {
        'table': table,
        'order': order,
        'order_items': order_items,
        'categories': categories,
        'menu_items': menu_items,
    }
    
    return render(request, 'core/order_entry.html', context)


@login_required
def get_order_items(request, table_id):
    """Get order items for AJAX refresh without page reload"""
    from tables.models import Table
    from orders.models import Order
    
    table = get_object_or_404(Table, id=table_id, is_active=True)
    
    # Get order for this table
    order = Order.objects.filter(
        table=table,
        status__in=['pending', 'confirmed', 'preparing']
    ).first()
    
    # Get order items if order exists
    order_items = []
    if order:
        order_items = order.items.select_related('menu_item').all()
    
    context = {
        'table': table,
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'core/order_items_partial.html', context)


@login_required
@require_POST
def create_order(request, table_id):
    """Create a new order for a table"""
    from tables.models import Table
    from orders.models import Order
    import random
    
    try:
        logger.info(f"Creating order for table {table_id} by user {request.user}")
        
        table = get_object_or_404(Table, id=table_id, is_active=True)
        
        # Check if table already has an active order
        existing_order = Order.objects.filter(
            table=table,
            status__in=['pending', 'confirmed', 'preparing']
        ).first()
        
        if existing_order:
            logger.info(f"Existing order found: {existing_order.order_number}")
            return JsonResponse({
                'success': True,
                'order_id': existing_order.id,
                'message': 'Existing order found'
            })
        
        # Generate unique order number
        order_number = f"ORD{timezone.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        while Order.objects.filter(order_number=order_number).exists():
            order_number = f"ORD{timezone.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        
        # Create new order
        order = Order.objects.create(
            order_number=order_number,
            order_type='dine_in',
            table=table,
            created_by=request.user,
            assigned_to=request.user,
            status='pending'
        )
        
        # Update table status
        table.status = 'occupied'
        table.occupied_since = timezone.now()
        table.save()
        
        logger.info(f"Order created successfully: {order.order_number}")
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'order_number': order.order_number,
            'message': 'Order created successfully'
        })
    except Exception as e:
        logger.error(f"Error creating order for table {table_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def add_order_item(request, table_id):
    """Add item to order via AJAX"""
    from tables.models import Table
    from orders.models import Order, OrderItem
    from menu.models import MenuItem
    
    try:
        table = get_object_or_404(Table, id=table_id, is_active=True)
        
        # Get or create order
        order = Order.objects.filter(
            table=table,
            status__in=['pending', 'confirmed', 'preparing']
        ).first()
        
        if not order:
            # Create new order if doesn't exist
            import random
            order_number = f"ORD{timezone.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
            while Order.objects.filter(order_number=order_number).exists():
                order_number = f"ORD{timezone.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
            
            order = Order.objects.create(
                order_number=order_number,
                order_type='dine_in',
                table=table,
                created_by=request.user,
                assigned_to=request.user,
                status='pending'
            )
            table.status = 'occupied'
            table.occupied_since = timezone.now()
            table.save()
        
        # Get menu item
        data = json.loads(request.body)
        menu_item_id = data.get('menu_item_id')
        quantity = int(data.get('quantity', 1))
        
        menu_item = get_object_or_404(MenuItem, id=menu_item_id, is_available=True)
        
        # Check if item already exists in order
        order_item = OrderItem.objects.filter(
            order=order,
            menu_item=menu_item
        ).first()
        
        if order_item:
            # Update quantity
            order_item.quantity += quantity
            order_item.total_price = order_item.unit_price * order_item.quantity
            order_item.save()
        else:
            # Create new order item
            order_item = OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=quantity,
                unit_price=menu_item.price,
                total_price=menu_item.price * quantity
            )
        
        # Recalculate order totals
        order.calculate_totals()
        
        return JsonResponse({
            'success': True,
            'order_item_id': order_item.id,
            'quantity': order_item.quantity,
            'subtotal': float(order.subtotal),
            'service_charge': float(order.service_charge),
            'total': float(order.total),
            'message': f'{menu_item.name} added to order'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def update_order_item(request, item_id):
    """Update order item quantity via AJAX"""
    from orders.models import OrderItem
    
    try:
        order_item = get_object_or_404(OrderItem, id=item_id)
        
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        if quantity <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Quantity must be greater than 0'
            }, status=400)
        
        order_item.quantity = quantity
        order_item.total_price = order_item.unit_price * quantity
        order_item.save()
        
        # Recalculate order totals
        order_item.order.calculate_totals()
        
        return JsonResponse({
            'success': True,
            'quantity': order_item.quantity,
            'item_total': float(order_item.total_price),
            'subtotal': float(order_item.order.subtotal),
            'service_charge': float(order_item.order.service_charge),
            'total': float(order_item.order.total),
            'message': 'Quantity updated'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def remove_order_item(request, item_id):
    """Remove item from order via AJAX"""
    from orders.models import OrderItem
    
    try:
        order_item = get_object_or_404(OrderItem, id=item_id)
        order = order_item.order
        
        order_item.delete()
        
        # Recalculate order totals
        order.calculate_totals()
        
        return JsonResponse({
            'success': True,
            'subtotal': float(order.subtotal),
            'service_charge': float(order.service_charge),
            'total': float(order.total),
            'message': 'Item removed from order'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def cancel_order(request, table_id):
    """Cancel and delete the current order for a table"""
    from tables.models import Table
    from orders.models import Order
    
    try:
        table = get_object_or_404(Table, id=table_id, is_active=True)
        
        order = Order.objects.filter(
            table=table,
            status__in=['pending', 'confirmed', 'preparing']
        ).first()
        
        if not order:
            return JsonResponse({
                'success': False,
                'error': 'No active order found'
            }, status=404)
        
        # Delete the order completely (including all order items)
        order_number = order.order_number
        order.delete()
        
        # Update table status
        table.status = 'available'
        table.occupied_since = None
        table.save()
        
        logger.info(f'Order {order_number} deleted by {request.user.username}')
        
        return JsonResponse({
            'success': True,
            'message': 'Order cancelled and removed successfully'
        })
        
    except Exception as e:
        logger.error(f'Error cancelling order: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def change_table(request, table_id):
    """Move order from current table to a new table"""
    from tables.models import Table
    from orders.models import Order
    
    try:
        # Get current table and order
        current_table = get_object_or_404(Table, id=table_id, is_active=True)
        
        order = Order.objects.filter(
            table=current_table,
            status__in=['pending', 'confirmed', 'preparing']
        ).first()
        
        if not order:
            return JsonResponse({
                'success': False,
                'error': 'No active order found on this table'
            }, status=404)
        
        # Get new table ID from request
        data = json.loads(request.body)
        new_table_id = data.get('new_table_id')
        
        if not new_table_id:
            return JsonResponse({
                'success': False,
                'error': 'New table ID is required'
            }, status=400)
        
        # Get new table
        new_table = get_object_or_404(Table, id=new_table_id, is_active=True)
        
        # Check if new table is available
        if new_table.status != 'available':
            return JsonResponse({
                'success': False,
                'error': f'Table {new_table.table_number} is not available'
            }, status=400)
        
        # Move order to new table
        order.table = new_table
        order.save()
        
        # Update old table status
        current_table.status = 'available'
        current_table.occupied_since = None
        current_table.save()
        
        # Update new table status
        new_table.status = 'occupied'
        new_table.occupied_since = timezone.now()
        new_table.save()
        
        logger.info(f'Order {order.order_number} moved from Table {current_table.table_number} to Table {new_table.table_number} by {request.user.username}')
        
        return JsonResponse({
            'success': True,
            'message': f'Order moved to Table {new_table.table_number}',
            'new_table_number': new_table.table_number,
            'new_table_id': new_table.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f'Error changing table: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def print_kot(request, table_id):
    """Print Kitchen Order Ticket"""
    from tables.models import Table
    from orders.models import Order
    
    table = get_object_or_404(Table, id=table_id, is_active=True)
    
    order = Order.objects.filter(
        table=table,
        status__in=['pending', 'confirmed', 'preparing']
    ).first()
    
    if not order:
        messages.error(request, 'No active order found for this table.')
        return redirect('core:order_entry', table_id=table_id)
    
    # Update order status to confirmed
    if order.status == 'pending':
        order.status = 'confirmed'
        order.save()
    
    # Get order items
    order_items = order.items.select_related('menu_item').all()
    
    context = {
        'order': order,
        'table': table,
        'order_items': order_items,
        'print_time': timezone.now(),
    }
    
    return render(request, 'core/kot_print.html', context)


@login_required
def payment_page(request, table_id):
    """Payment processing page"""
    from tables.models import Table
    from orders.models import Order
    
    table = get_object_or_404(Table, id=table_id, is_active=True)
    
    order = Order.objects.filter(
        table=table,
        status__in=['pending', 'confirmed', 'preparing', 'ready']
    ).first()
    
    if not order:
        messages.error(request, 'No active order found for this table.')
        return redirect('core:sales')
    
    # Get order items
    order_items = order.items.select_related('menu_item').all()
    
    context = {
        'order': order,
        'table': table,
        'order_items': order_items,
    }
    
    return render(request, 'core/payment.html', context)


@login_required
@require_POST
def process_payment(request, table_id):
    """Process payment and complete order"""
    from tables.models import Table
    from orders.models import Order
    from billing.models import Payment, Bill
    
    try:
        table = get_object_or_404(Table, id=table_id, is_active=True)
        
        order = Order.objects.filter(
            table=table,
            status__in=['pending', 'confirmed', 'preparing', 'ready']
        ).first()
        
        if not order:
            messages.error(request, 'No active order found for this table.')
            return redirect('core:sales')
        
        # Get payment details from form
        payment_method = request.POST.get('payment_method')
        amount_received = request.POST.get('amount_received', order.total)
        
        # Validate payment method
        if payment_method not in ['cash', 'card', 'mobile', 'other']:
            messages.error(request, 'Invalid payment method selected.')
            return redirect('core:payment_page', table_id=table_id)
        
        # Generate unique bill number
        import random
        bill_number = f"BILL{timezone.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        while Bill.objects.filter(bill_number=bill_number).exists():
            bill_number = f"BILL{timezone.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        
        # Create Bill
        bill = Bill.objects.create(
            bill_number=bill_number,
            order=order,
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            tax_amount=order.tax_amount,
            service_charge=order.service_charge,
            total_amount=order.total,
            paid_amount=order.total,
            balance=0,
            is_paid=True,
            created_by=request.user,
            paid_at=timezone.now()
        )
        
        # Generate unique payment number
        payment_number = f"PAY{timezone.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        while Payment.objects.filter(payment_number=payment_number).exists():
            payment_number = f"PAY{timezone.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        
        # Create Payment record
        payment = Payment.objects.create(
            payment_number=payment_number,
            order=order,
            payment_method=payment_method,
            amount=order.total,
            status='completed',
            processed_by=request.user,
            completed_at=timezone.now()
        )
        
        # Update order status
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save()
        
        # Clear table
        table.status = 'available'
        table.occupied_since = None
        table.save()
        
        messages.success(request, f'Payment completed successfully! Order #{order.order_number}')
        
        # Redirect to receipt print page
        return redirect('core:print_receipt', table_id=table_id, order_id=order.id)
        
    except Exception as e:
        messages.error(request, f'Payment failed: {str(e)}')
        return redirect('core:payment_page', table_id=table_id)


@login_required
def print_receipt(request, table_id, order_id):
    """Print customer receipt"""
    from tables.models import Table
    from orders.models import Order
    from billing.models import Bill, Payment
    
    order = get_object_or_404(Order, id=order_id)
    table = get_object_or_404(Table, id=table_id, is_active=True)
    
    # Get bill and payment
    bill = Bill.objects.filter(order=order).first()
    payment = Payment.objects.filter(order=order).first()  # Payment links to order, not bill
    
    # Get order items
    order_items = order.items.select_related('menu_item').all()
    
    context = {
        'order': order,
        'table': table,
        'bill': bill,
        'payment': payment,
        'order_items': order_items,
        'print_time': timezone.now(),
    }
    
    return render(request, 'core/receipt_print.html', context)
