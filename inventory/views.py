from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F
from decimal import Decimal
import json


@login_required
def inventory_list(request):
    from .models import StockItem
    
    # Get filter parameters
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    
    items = StockItem.objects.all().select_related('vendor', 'location')
    
    # Apply filters
    if search:
        items = items.filter(Q(name__icontains=search) | Q(sku__icontains=search))
    if category:
        items = items.filter(category=category)
    if status == 'low':
        items = [item for item in items if item.is_low_stock]
    elif status == 'out':
        items = [item for item in items if item.current_quantity == 0]
    
    # Calculate statistics
    all_items = StockItem.objects.all()
    low_stock_count = sum(1 for item in all_items if item.is_low_stock)
    out_of_stock_count = sum(1 for item in all_items if item.current_quantity == 0)
    in_stock_count = sum(1 for item in all_items if item.current_quantity > 0)
    total_value = sum(item.stock_value for item in all_items)
    
    # Get unique categories
    categories = StockItem.objects.values_list('category', flat=True).distinct()
    
    context = {
        'items': items,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'in_stock_count': in_stock_count,
        'total_value': total_value,
        'categories': categories,
        'current_search': search,
        'current_category': category,
        'current_status': status,
    }
    
    return render(request, 'inventory/inventory_list.html', context)


@login_required
def stock_items(request):
    """Main stock items management page"""
    return inventory_list(request)


@login_required
def stock_alerts(request):
    from .models import StockAlert, StockItem
    
    alerts = StockAlert.objects.filter(is_resolved=False).select_related('stock_item').order_by('-created_at')
    
    # Get low stock items
    all_items = StockItem.objects.all()
    low_stock_items = [item for item in all_items if item.is_low_stock]
    out_of_stock_items = [item for item in all_items if item.current_quantity == 0]
    
    context = {
        'alerts': alerts,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
    }
    
    return render(request, 'inventory/stock_alerts.html', context)


@login_required
def purchase_orders(request):
    from .models import PurchaseOrder
    
    status_filter = request.GET.get('status', 'all')
    
    pos = PurchaseOrder.objects.all().select_related('vendor', 'created_by').prefetch_related('items')
    
    if status_filter != 'all':
        pos = pos.filter(status=status_filter)
    
    # Calculate statistics
    draft_count = PurchaseOrder.objects.filter(status='draft').count()
    sent_count = PurchaseOrder.objects.filter(status='sent').count()
    received_count = PurchaseOrder.objects.filter(status='received').count()
    
    context = {
        'purchase_orders': pos,
        'draft_count': draft_count,
        'sent_count': sent_count,
        'received_count': received_count,
        'status_filter': status_filter,
    }
    
    return render(request, 'inventory/purchase_orders.html', context)


@login_required
def stock_movements(request):
    """View all stock movements"""
    from .models import StockMovement
    
    movements = StockMovement.objects.all().select_related('stock_item', 'created_by', 'from_location', 'to_location').order_by('-created_at')[:100]
    
    context = {
        'movements': movements,
    }
    
    return render(request, 'inventory/stock_movements.html', context)


@login_required
def add_stock_item(request):
    """Add new stock item"""
    from .models import StockItem, Vendor, StockLocation
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            item = StockItem.objects.create(
                name=data['name'],
                sku=data['sku'],
                category=data.get('category', 'General'),
                unit=data['unit'],
                current_quantity=Decimal(data.get('current_quantity', 0)),
                min_quantity=Decimal(data['min_quantity']),
                unit_cost=Decimal(data['unit_cost']),
            )
            
            # Optional fields
            if data.get('vendor_id'):
                item.vendor_id = data['vendor_id']
            if data.get('location_id'):
                item.location_id = data['location_id']
            if data.get('max_quantity'):
                item.max_quantity = Decimal(data['max_quantity'])
            
            item.save()
            
            return JsonResponse({'success': True, 'message': 'Stock item added successfully', 'item_id': item.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    # GET request - show form
    vendors = Vendor.objects.filter(is_active=True)
    locations = StockLocation.objects.filter(is_active=True)
    
    context = {
        'vendors': vendors,
        'locations': locations,
    }
    
    return render(request, 'inventory/add_stock_item.html', context)


@login_required
def update_stock(request, item_id):
    """Update stock quantity"""
    from .models import StockItem, StockMovement
    
    if request.method == 'POST':
        try:
            item = get_object_or_404(StockItem, id=item_id)
            data = json.loads(request.body)
            
            movement_type = data['movement_type']
            quantity = Decimal(data['quantity'])
            
            # Create stock movement
            movement = StockMovement.objects.create(
                stock_item=item,
                movement_type=movement_type,
                quantity=quantity,
                unit_cost=item.unit_cost,
                reference=data.get('reference', ''),
                notes=data.get('notes', ''),
                created_by=request.user
            )
            
            # Update stock quantity
            if movement_type in ['purchase', 'adjustment']:
                item.current_quantity += quantity
            elif movement_type in ['sale', 'waste']:
                item.current_quantity -= quantity
                
            item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Stock updated successfully',
                'new_quantity': float(item.current_quantity)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
