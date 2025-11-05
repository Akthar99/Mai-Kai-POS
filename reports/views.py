from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal


@login_required
def reports_home(request):
    return render(request, 'reports/reports_home.html')


@login_required
def sales_report(request):
    from orders.models import Order, OrderItem
    from billing.models import Payment
    from menu.models import MenuItem, Category
    
    # Get date range from request or default to this month
    date_range = request.GET.get('range', 'this_month')
    today = timezone.now().date()
    
    if date_range == 'today':
        start_date = today
        end_date = today
    elif date_range == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif date_range == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif date_range == 'last_week':
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = today - timedelta(days=today.weekday() + 1)
    elif date_range == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif date_range == 'last_month':
        last_month = today.replace(day=1) - timedelta(days=1)
        start_date = last_month.replace(day=1)
        end_date = last_month
    else:  # custom
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            start_date = today.replace(day=1)
            end_date = today
    
    # Calculate previous period for comparison
    period_days = (end_date - start_date).days + 1
    prev_start_date = start_date - timedelta(days=period_days)
    prev_end_date = start_date - timedelta(days=1)
    
    # Current period orders
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        status__in=['confirmed', 'preparing', 'ready', 'completed']
    )
    
    # Previous period orders
    prev_orders = Order.objects.filter(
        created_at__date__gte=prev_start_date,
        created_at__date__lte=prev_end_date,
        status__in=['confirmed', 'preparing', 'ready', 'completed']
    )
    
    # Total Revenue - use completed_at date for accuracy
    total_revenue = Payment.objects.filter(
        status='completed',
        completed_at__date__gte=start_date,
        completed_at__date__lte=end_date
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    prev_revenue = Payment.objects.filter(
        status='completed',
        completed_at__date__gte=prev_start_date,
        completed_at__date__lte=prev_end_date
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    revenue_change = calculate_percentage_change(total_revenue, prev_revenue)
    
    # Total Orders
    total_orders = orders.count()
    prev_total_orders = prev_orders.count()
    orders_change = calculate_percentage_change(total_orders, prev_total_orders)
    
    # Average Order Value
    avg_order_value = orders.aggregate(avg=Avg('total'))['avg'] or Decimal('0')
    prev_avg_order_value = prev_orders.aggregate(avg=Avg('total'))['avg'] or Decimal('0')
    avg_change = calculate_percentage_change(avg_order_value, prev_avg_order_value)
    
    # Total Customers (unique)
    total_customers = orders.filter(customer__isnull=False).values('customer').distinct().count()
    prev_total_customers = prev_orders.filter(customer__isnull=False).values('customer').distinct().count()
    customers_change = calculate_percentage_change(total_customers, prev_total_customers)
    
    # Daily sales for chart (last 7 days)
    daily_sales = []
    for i in range(7):
        day = today - timedelta(days=6-i)
        day_revenue = Payment.objects.filter(
            status='completed',
            completed_at__date=day
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        daily_sales.append({
            'day': day.strftime('%a'),
            'revenue': float(day_revenue)
        })
    
    # Payment methods breakdown
    payment_methods = Payment.objects.filter(
        status='completed',
        completed_at__date__gte=start_date,
        completed_at__date__lte=end_date
    ).values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Calculate payment method percentages
    payment_data = []
    for pm in payment_methods:
        percentage = (float(pm['total']) / float(total_revenue) * 100) if total_revenue > 0 else 0
        payment_data.append({
            'method': pm['payment_method'].replace('_', ' ').title(),
            'total': pm['total'],
            'count': pm['count'],
            'percentage': round(percentage, 1)
        })
    
    # Category-wise sales
    category_sales = []
    categories = Category.objects.filter(is_active=True)
    
    for category in categories:
        items_in_category = OrderItem.objects.filter(
            order__in=orders,
            menu_item__category=category
        )
        
        items_sold = items_in_category.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0
        category_revenue = items_in_category.aggregate(total=Sum('total_price'))['total'] or Decimal('0')
        
        # Previous period for this category
        prev_items = OrderItem.objects.filter(
            order__in=prev_orders,
            menu_item__category=category
        )
        prev_category_revenue = prev_items.aggregate(total=Sum('total_price'))['total'] or Decimal('0')
        
        category_change = calculate_percentage_change(category_revenue, prev_category_revenue)
        percentage_of_total = (float(category_revenue) / float(total_revenue) * 100) if total_revenue > 0 else 0
        
        if items_sold > 0:  # Only include categories with sales
            category_sales.append({
                'name': category.name,
                'items_sold': items_sold,
                'revenue': category_revenue,
                'percentage': round(percentage_of_total, 1),
                'change': category_change
            })
    
    category_sales.sort(key=lambda x: x['revenue'], reverse=True)
    
    # Top selling items
    top_items = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'menu_item__name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_qty')[:10]
    
    # Peak hours analysis
    peak_hours = []
    time_slots = [
        ('09:00', '11:00', 'Breakfast'),
        ('12:00', '14:00', 'Lunch'),
        ('15:00', '17:00', 'Evening'),
        ('19:00', '21:00', 'Dinner'),
    ]
    
    max_orders = 0
    for start_time, end_time, label in time_slots:
        start_hour = int(start_time.split(':')[0])
        end_hour = int(end_time.split(':')[0])
        
        slot_orders = orders.filter(
            created_at__hour__gte=start_hour,
            created_at__hour__lt=end_hour
        ).count()
        
        if slot_orders > max_orders:
            max_orders = slot_orders
        
        peak_hours.append({
            'label': f'{start_time} - {end_time} ({label})',
            'orders': slot_orders
        })
    
    # Calculate percentages for peak hours
    for slot in peak_hours:
        slot['percentage'] = round((slot['orders'] / max_orders * 100) if max_orders > 0 else 0, 0)
    
    context = {
        'date_range': date_range,
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'revenue_change': revenue_change,
        'total_orders': total_orders,
        'orders_change': orders_change,
        'avg_order_value': avg_order_value,
        'avg_change': avg_change,
        'total_customers': total_customers,
        'customers_change': customers_change,
        'daily_sales': daily_sales,
        'payment_data': payment_data,
        'category_sales': category_sales,
        'top_items': top_items,
        'peak_hours': peak_hours,
    }
    
    return render(request, 'reports/sales_report.html', context)


def calculate_percentage_change(current, previous):
    """Calculate percentage change between two values"""
    try:
        current = float(current) if current else 0
        previous = float(previous) if previous else 0
        
        if previous == 0:
            return 100 if current > 0 else 0
        
        change = ((current - previous) / previous) * 100
        return round(change, 1)
    except:
        return 0


@login_required
@login_required
def inventory_report(request):
    """Comprehensive inventory report with real data"""
    from inventory.models import StockItem, PurchaseOrder, StockMovement
    from django.db.models import Sum
    
    # Get all stock items
    items = StockItem.objects.all().select_related('vendor', 'location')
    
    # Calculate statistics
    total_items = items.count()
    low_stock_items = [item for item in items if item.is_low_stock]
    out_of_stock_items = [item for item in items if item.current_quantity == 0]
    
    # Calculate total stock value
    total_value = sum(item.stock_value for item in items)
    
    # Get items by category
    categories = {}
    for item in items:
        cat = item.category or 'Uncategorized'
        if cat not in categories:
            categories[cat] = {'count': 0, 'value': Decimal('0')}
        categories[cat]['count'] += 1
        categories[cat]['value'] += item.stock_value
    
    # Get recent stock movements
    recent_movements = StockMovement.objects.select_related('stock_item', 'created_by').order_by('-created_at')[:10]
    
    # Get recent purchase orders
    recent_pos = PurchaseOrder.objects.select_related('vendor').order_by('-order_date')[:5]
    
    context = {
        'total_items': total_items,
        'low_stock_count': len(low_stock_items),
        'out_of_stock_count': len(out_of_stock_items),
        'total_value': total_value,
        'items': items[:50],  # Show first 50 items
        'low_stock_items': low_stock_items[:10],  # Top 10 low stock
        'categories': categories,
        'recent_movements': recent_movements,
        'recent_pos': recent_pos,
    }
    
    return render(request, 'reports/inventory_report.html', context)


@login_required
def financial_report(request):
    return render(request, 'reports/financial_report.html')


@login_required
def orders_export_page(request):
    """Page to select export options for orders"""
    return render(request, 'reports/orders_export.html')


@login_required
def export_orders_pdf(request):
    """Export orders to PDF by day, week, or month"""
    from orders.models import Order, OrderItem
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from io import BytesIO
    
    # Get date range from request
    date_range = request.GET.get('range', 'this_week')
    today = timezone.now().date()
    
    if date_range == 'today':
        start_date = today
        end_date = today
        period_name = f"Daily Report - {today.strftime('%B %d, %Y')}"
    elif date_range == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
        period_name = f"Daily Report - {start_date.strftime('%B %d, %Y')}"
    elif date_range == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
        period_name = f"Weekly Report - Week of {start_date.strftime('%B %d, %Y')}"
    elif date_range == 'last_week':
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = today - timedelta(days=today.weekday() + 1)
        period_name = f"Weekly Report - Week of {start_date.strftime('%B %d, %Y')}"
    elif date_range == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
        period_name = f"Monthly Report - {today.strftime('%B %Y')}"
    elif date_range == 'last_month':
        last_month = today.replace(day=1) - timedelta(days=1)
        start_date = last_month.replace(day=1)
        end_date = last_month
        period_name = f"Monthly Report - {last_month.strftime('%B %Y')}"
    else:  # custom
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            period_name = f"Custom Report - {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}"
        else:
            start_date = today.replace(day=1)
            end_date = today
            period_name = f"Monthly Report - {today.strftime('%B %Y')}"
    
    # Get orders for the period
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).select_related('table', 'customer', 'created_by', 'assigned_to').order_by('created_at')
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                          rightMargin=30, leftMargin=30,
                          topMargin=30, bottomMargin=30)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#374151')
    )
    
    # Add title
    elements.append(Paragraph("Mai Kai Restaurant", title_style))
    elements.append(Paragraph("Orders Report", heading_style))
    elements.append(Paragraph(period_name, normal_style))
    elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Add summary statistics
    total_orders = orders.count()
    total_revenue = sum(order.total for order in orders)
    completed_orders = orders.filter(status='completed').count()
    pending_orders = orders.exclude(status='completed').count()
    
    summary_data = [
        ['Summary Statistics', ''],
        ['Total Orders:', str(total_orders)],
        ['Completed Orders:', str(completed_orders)],
        ['Pending Orders:', str(pending_orders)],
        ['Total Revenue:', f'Rs. {total_revenue:,.2f}'],
        ['Average Order Value:', f'Rs. {(total_revenue / total_orders if total_orders > 0 else 0):,.2f}'],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3f4f6')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Add orders details
    elements.append(Paragraph("Order Details", heading_style))
    elements.append(Spacer(1, 12))
    
    if orders.exists():
        # Create orders table header
        orders_data = [['Order #', 'Date & Time', 'Table', 'Server', 'Items', 'Total', 'Status']]
        
        for order in orders:
            # Get order items count
            items_count = order.items.count()
            
            # Format date and time
            order_datetime = timezone.localtime(order.created_at)
            date_str = order_datetime.strftime('%m/%d/%Y')
            time_str = order_datetime.strftime('%I:%M %p')
            
            # Get server name (assigned_to or created_by)
            server_name = 'N/A'
            if order.assigned_to:
                server_name = order.assigned_to.get_full_name() if hasattr(order.assigned_to, 'get_full_name') else order.assigned_to.username
            elif order.created_by:
                server_name = order.created_by.get_full_name() if hasattr(order.created_by, 'get_full_name') else order.created_by.username
            
            orders_data.append([
                f'#{order.id}',
                f'{date_str}\n{time_str}',
                order.table.table_number if order.table else 'N/A',
                server_name,
                str(items_count),
                f'Rs. {order.total:,.2f}',
                order.status.title()
            ])
        
        orders_table = Table(orders_data, colWidths=[0.7*inch, 1.3*inch, 0.7*inch, 1.2*inch, 0.6*inch, 1*inch, 1*inch])
        orders_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(orders_table)
        
        # Add detailed order items breakdown
        elements.append(PageBreak())
        elements.append(Paragraph("Detailed Order Items", heading_style))
        elements.append(Spacer(1, 12))
        
        for order in orders:
            # Order header
            order_datetime = timezone.localtime(order.created_at)
            
            # Get server name
            server_name = 'N/A'
            if order.assigned_to:
                server_name = order.assigned_to.get_full_name() if hasattr(order.assigned_to, 'get_full_name') else order.assigned_to.username
            elif order.created_by:
                server_name = order.created_by.get_full_name() if hasattr(order.created_by, 'get_full_name') else order.created_by.username
            
            # Create order header with bold text using Paragraph
            order_header_text = f"<b>Order #{order.id}</b> | {order_datetime.strftime('%m/%d/%Y %I:%M %p')} | Table: {order.table.table_number if order.table else 'N/A'} | Server: {server_name} | Status: {order.status.title()}"
            elements.append(Paragraph(order_header_text, normal_style))
            elements.append(Spacer(1, 8))
            
            # Order items table
            items_data = [['Item', 'Qty', 'Price', 'Total']]
            
            for item in order.items.all():
                items_data.append([
                    item.menu_item.name if item.menu_item else (item.combo.name if item.combo else 'N/A'),
                    str(item.quantity),
                    f'Rs. {item.unit_price:,.2f}',
                    f'Rs. {item.total_price:,.2f}'
                ])
            
            # Add subtotal, discount, tax, etc.
            items_data.append(['', '', 'Subtotal:', f'Rs. {order.subtotal:,.2f}'])
            if order.discount_amount > 0:
                items_data.append(['', '', 'Discount:', f'-Rs. {order.discount_amount:,.2f}'])
            if order.tax_amount > 0:
                items_data.append(['', '', 'Tax:', f'Rs. {order.tax_amount:,.2f}'])
            if order.service_charge > 0:
                items_data.append(['', '', 'Service Charge:', f'Rs. {order.service_charge:,.2f}'])
            items_data.append(['', '', 'Total:', f'Rs. {order.total:,.2f}'])
            
            items_table = Table(items_data, colWidths=[3.5*inch, 0.7*inch, 1.3*inch, 1.3*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#d1d5db')),
                ('LINEABOVE', (2, -5), (3, -5), 0.5, colors.HexColor('#9ca3af')),
                ('LINEABOVE', (2, -1), (3, -1), 1, colors.HexColor('#1f2937')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -6), [colors.white, colors.HexColor('#f9fafb')]),
            ]))
            
            elements.append(items_table)
            elements.append(Spacer(1, 15))
        
        # Add detailed breakdown by day if date range is more than 1 day
        if (end_date - start_date).days > 0:
            elements.append(PageBreak())
            elements.append(Paragraph("Daily Breakdown", heading_style))
            elements.append(Spacer(1, 12))
            
            # Group orders by day
            from collections import defaultdict
            daily_orders = defaultdict(list)
            
            for order in orders:
                day = order.created_at.date()
                daily_orders[day].append(order)
            
            # Create daily summary
            daily_data = [['Date', 'Orders', 'Revenue', 'Avg Order']]
            
            for day in sorted(daily_orders.keys()):
                day_orders = daily_orders[day]
                day_total = sum(o.total for o in day_orders)
                day_count = len(day_orders)
                day_avg = day_total / day_count if day_count > 0 else 0
                
                daily_data.append([
                    day.strftime('%B %d, %Y (%A)'),
                    str(day_count),
                    f'Rs. {day_total:,.2f}',
                    f'Rs. {day_avg:,.2f}'
                ])
            
            daily_table = Table(daily_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
            daily_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ]))
            
            elements.append(daily_table)
    else:
        elements.append(Paragraph("No orders found for this period.", normal_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and return it
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    filename = f'orders_report_{start_date.strftime("%Y%m%d")}_to_{end_date.strftime("%Y%m%d")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf)
    
    return response
