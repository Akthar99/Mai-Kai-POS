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


@login_required
def create_purchase_order(request):
    """Create new purchase order"""
    from .models import PurchaseOrder, PurchaseOrderItem, Vendor, StockItem
    from datetime import datetime, timedelta
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Generate PO number
            from django.utils import timezone
            po_count = PurchaseOrder.objects.filter(order_date__year=timezone.now().year).count()
            po_number = f"PO-{timezone.now().year}-{str(po_count + 1).zfill(4)}"
            
            # Create purchase order
            po = PurchaseOrder.objects.create(
                po_number=po_number,
                vendor_id=data['vendor_id'],
                expected_delivery=data['expected_delivery'],
                notes=data.get('notes', ''),
                created_by=request.user,
                status='draft'
            )
            
            # Add items
            subtotal = Decimal('0')
            for item_data in data['items']:
                quantity = Decimal(item_data['quantity'])
                unit_cost = Decimal(item_data['unit_cost'])
                total_cost = quantity * unit_cost
                
                PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    stock_item_id=item_data['stock_item_id'],
                    quantity=quantity,
                    unit_cost=unit_cost,
                    total_cost=total_cost
                )
                
                subtotal += total_cost
            
            # Calculate totals
            tax_rate = Decimal(data.get('tax_rate', '0.10'))  # Default 10%
            po.subtotal = subtotal
            po.tax_amount = subtotal * tax_rate
            po.total_amount = po.subtotal + po.tax_amount
            po.save()
            
            messages.success(request, f'Purchase Order {po.po_number} created successfully')
            return JsonResponse({
                'success': True,
                'message': f'Purchase Order {po.po_number} created',
                'po_id': po.id,
                'po_number': po.po_number
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    # GET request - show form
    vendors = Vendor.objects.filter(is_active=True)
    stock_items = StockItem.objects.all().order_by('name')
    
    context = {
        'vendors': vendors,
        'stock_items': stock_items,
    }
    
    return render(request, 'inventory/create_purchase_order.html', context)


@login_required
def view_purchase_order(request, po_id):
    """View purchase order details"""
    from .models import PurchaseOrder
    
    po = get_object_or_404(PurchaseOrder.objects.select_related('vendor', 'created_by').prefetch_related('items__stock_item'), id=po_id)
    
    context = {
        'po': po,
    }
    
    return render(request, 'inventory/view_purchase_order.html', context)


@login_required
def edit_purchase_order(request, po_id):
    """Edit purchase order (only if status is draft)"""
    from .models import PurchaseOrder, PurchaseOrderItem, Vendor, StockItem
    
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    if po.status != 'draft':
        messages.error(request, 'Only draft purchase orders can be edited')
        return redirect('inventory:purchase_orders')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Update purchase order
            po.vendor_id = data['vendor_id']
            po.expected_delivery = data['expected_delivery']
            po.notes = data.get('notes', '')
            
            # Delete existing items
            po.items.all().delete()
            
            # Add new items
            subtotal = Decimal('0')
            for item_data in data['items']:
                quantity = Decimal(item_data['quantity'])
                unit_cost = Decimal(item_data['unit_cost'])
                total_cost = quantity * unit_cost
                
                PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    stock_item_id=item_data['stock_item_id'],
                    quantity=quantity,
                    unit_cost=unit_cost,
                    total_cost=total_cost
                )
                
                subtotal += total_cost
            
            # Calculate totals
            tax_rate = Decimal(data.get('tax_rate', '0.10'))
            po.subtotal = subtotal
            po.tax_amount = subtotal * tax_rate
            po.total_amount = po.subtotal + po.tax_amount
            po.save()
            
            messages.success(request, f'Purchase Order {po.po_number} updated successfully')
            return JsonResponse({
                'success': True,
                'message': f'Purchase Order {po.po_number} updated'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    # GET request
    vendors = Vendor.objects.filter(is_active=True)
    stock_items = StockItem.objects.all().order_by('name')
    
    context = {
        'po': po,
        'vendors': vendors,
        'stock_items': stock_items,
    }
    
    return render(request, 'inventory/edit_purchase_order.html', context)


@login_required
def delete_purchase_order(request, po_id):
    """Delete purchase order (only if status is draft)"""
    from .models import PurchaseOrder
    
    if request.method == 'POST':
        try:
            po = get_object_or_404(PurchaseOrder, id=po_id)
            
            if po.status != 'draft':
                return JsonResponse({
                    'success': False,
                    'error': 'Only draft purchase orders can be deleted'
                }, status=400)
            
            po_number = po.po_number
            po.delete()
            
            messages.success(request, f'Purchase Order {po_number} deleted successfully')
            return JsonResponse({
                'success': True,
                'message': f'Purchase Order {po_number} deleted'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
def send_purchase_order(request, po_id):
    """Mark purchase order as sent"""
    from .models import PurchaseOrder
    
    if request.method == 'POST':
        try:
            po = get_object_or_404(PurchaseOrder, id=po_id)
            
            if po.status != 'draft':
                return JsonResponse({
                    'success': False,
                    'error': 'Only draft purchase orders can be sent'
                }, status=400)
            
            po.status = 'sent'
            po.save()
            
            messages.success(request, f'Purchase Order {po.po_number} marked as sent')
            return JsonResponse({
                'success': True,
                'message': f'Purchase Order {po.po_number} sent'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
def receive_purchase_order(request, po_id):
    """Receive purchase order and update stock"""
    from .models import PurchaseOrder, StockMovement, StockItem
    from django.utils import timezone
    
    if request.method == 'POST':
        try:
            po = get_object_or_404(PurchaseOrder.objects.prefetch_related('items__stock_item'), id=po_id)
            
            if po.status == 'received':
                return JsonResponse({
                    'success': False,
                    'error': 'This purchase order has already been received'
                }, status=400)
            
            if po.status == 'cancelled':
                return JsonResponse({
                    'success': False,
                    'error': 'Cancelled purchase orders cannot be received'
                }, status=400)
            
            # Update stock for each item
            for item in po.items.all():
                stock_item = item.stock_item
                
                # Create stock movement
                StockMovement.objects.create(
                    stock_item=stock_item,
                    movement_type='purchase',
                    quantity=item.quantity,
                    unit_cost=item.unit_cost,
                    reference=f"PO #{po.po_number}",
                    notes=f"Received from {po.vendor.name}",
                    created_by=request.user
                )
                
                # Update stock quantity
                stock_item.current_quantity += item.quantity
                stock_item.unit_cost = item.unit_cost  # Update unit cost
                stock_item.save()
                
                # Mark as received in PO item
                item.received_quantity = item.quantity
                item.save()
            
            # Update PO status
            po.status = 'received'
            po.received_date = timezone.now().date()
            po.save()
            
            messages.success(request, f'Purchase Order {po.po_number} received and stock updated')
            return JsonResponse({
                'success': True,
                'message': f'Purchase Order {po.po_number} received'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
def vendors_list(request):
    """List all vendors"""
    from .models import Vendor
    
    vendors = Vendor.objects.all().order_by('-is_active', 'name')
    
    active_count = vendors.filter(is_active=True).count()
    inactive_count = vendors.filter(is_active=False).count()
    
    context = {
        'vendors': vendors,
        'active_count': active_count,
        'inactive_count': inactive_count,
    }
    
    return render(request, 'inventory/vendors_list.html', context)


@login_required
def add_vendor(request):
    """Add new vendor"""
    from .models import Vendor
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            vendor = Vendor.objects.create(
                name=data['name'],
                contact_person=data.get('contact_person', ''),
                phone=data['phone'],
                email=data.get('email', ''),
                address=data.get('address', ''),
                is_active=data.get('is_active', True)
            )
            
            messages.success(request, f'Vendor "{vendor.name}" added successfully')
            return JsonResponse({
                'success': True,
                'message': f'Vendor "{vendor.name}" added',
                'vendor_id': vendor.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
def edit_vendor(request, vendor_id):
    """Edit vendor"""
    from .models import Vendor
    
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            vendor.name = data['name']
            vendor.contact_person = data.get('contact_person', '')
            vendor.phone = data['phone']
            vendor.email = data.get('email', '')
            vendor.address = data.get('address', '')
            vendor.is_active = data.get('is_active', True)
            vendor.save()
            
            messages.success(request, f'Vendor "{vendor.name}" updated successfully')
            return JsonResponse({
                'success': True,
                'message': f'Vendor "{vendor.name}" updated'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
def delete_vendor(request, vendor_id):
    """Delete vendor"""
    from .models import Vendor
    
    if request.method == 'POST':
        try:
            vendor = get_object_or_404(Vendor, id=vendor_id)
            vendor_name = vendor.name
            vendor.delete()
            
            messages.success(request, f'Vendor "{vendor_name}" deleted successfully')
            return JsonResponse({
                'success': True,
                'message': f'Vendor "{vendor_name}" deleted'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
