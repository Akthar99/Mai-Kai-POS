from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, MenuItem, Modifier


@login_required
def menu_list(request):
    """Display full menu"""
    categories = Category.objects.filter(is_active=True)
    menu_items = MenuItem.objects.all().select_related('category')
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id and category_id != 'all':
        menu_items = menu_items.filter(category_id=category_id)
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'available':
        menu_items = menu_items.filter(is_available=True)
    elif status == 'unavailable':
        menu_items = menu_items.filter(is_available=False)
    
    # Search
    search = request.GET.get('search')
    if search:
        menu_items = menu_items.filter(name__icontains=search)
    
    # Sorting
    sort = request.GET.get('sort', 'name')
    if sort == 'price':
        menu_items = menu_items.order_by('price')
    elif sort == 'category':
        menu_items = menu_items.order_by('category__name', 'name')
    else:
        menu_items = menu_items.order_by('name')
    
    # Check if HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'menu/menu_items_partial.html', {
            'menu_items': menu_items
        })
    
    return render(request, 'menu/menu_list.html', {
        'categories': categories,
        'menu_items': menu_items
    })


@login_required
def category_list(request):
    """List all categories"""
    categories = Category.objects.all()
    return render(request, 'menu/category_list.html', {'categories': categories})


@login_required
def item_detail(request, item_id):
    """Item details"""
    item = get_object_or_404(MenuItem, id=item_id)
    return render(request, 'menu/item_detail.html', {'item': item})


@login_required
def menu_item_create(request):
    """Create new menu item"""
    if request.method == 'POST':
        # Handle form submission
        reference_number = request.POST.get('reference_number')
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        description = request.POST.get('description')
        is_vegetarian = request.POST.get('is_vegetarian') == 'on'
        is_available = request.POST.get('is_available') == 'on'
        
        category = get_object_or_404(Category, id=category_id)
        
        # Check if reference number already exists
        if MenuItem.objects.filter(reference_number=reference_number).exists():
            messages.error(request, f'Reference number "{reference_number}" already exists. Please use a unique number.')
            categories = Category.objects.filter(is_active=True)
            return render(request, 'menu/menu_item_form.html', {
                'categories': categories,
                'form_data': request.POST
            })
        
        menu_item = MenuItem.objects.create(
            reference_number=reference_number,
            name=name,
            category=category,
            description=description,
            price=price,
            is_vegetarian=is_vegetarian,
            is_available=is_available
        )
        
        if 'image' in request.FILES:
            menu_item.image = request.FILES['image']
            menu_item.save()
        
        messages.success(request, f'Menu item "#{reference_number} - {name}" created successfully!')
        return redirect('menu:menu_list')
    
    categories = Category.objects.filter(is_active=True)
    return render(request, 'menu/menu_item_form.html', {'categories': categories})


@login_required
def menu_item_update(request, item_id):
    """Update menu item"""
    item = get_object_or_404(MenuItem, id=item_id)
    
    if request.method == 'POST':
        reference_number = request.POST.get('reference_number')
        
        # Check if reference number already exists (excluding current item)
        if MenuItem.objects.filter(reference_number=reference_number).exclude(id=item_id).exists():
            messages.error(request, f'Reference number "{reference_number}" already exists. Please use a unique number.')
            categories = Category.objects.filter(is_active=True)
            return render(request, 'menu/menu_item_form.html', {
                'categories': categories,
                'item': item,
                'form_data': request.POST
            })
        
        item.reference_number = reference_number
        item.name = request.POST.get('name')
        item.category_id = request.POST.get('category')
        item.price = request.POST.get('price')
        item.description = request.POST.get('description')
        item.is_vegetarian = request.POST.get('is_vegetarian') == 'on'
        item.is_available = request.POST.get('is_available') == 'on'
        
        if 'image' in request.FILES:
            item.image = request.FILES['image']
        
        item.save()
        messages.success(request, f'Menu item "#{reference_number} - {item.name}" updated successfully!')
        return redirect('menu:menu_list')
    
    categories = Category.objects.filter(is_active=True)
    return render(request, 'menu/menu_item_form.html', {
        'item': item,
        'categories': categories
    })


@login_required
def menu_item_delete(request, item_id):
    """Delete menu item"""
    item = get_object_or_404(MenuItem, id=item_id)
    
    if request.method == 'POST':
        name = item.name
        item.delete()
        messages.success(request, f'Menu item "{name}" deleted successfully!')
        return redirect('menu:menu_list')
    
    return render(request, 'menu/menu_item_confirm_delete.html', {'item': item})


@login_required
def category_create(request):
    """Create new category"""
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to create categories.')
        return redirect('menu:category_list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        display_order = request.POST.get('display_order', 0)
        is_active = request.POST.get('is_active') == 'on'
        
        category = Category.objects.create(
            name=name,
            description=description,
            display_order=display_order,
            is_active=is_active
        )
        
        messages.success(request, f'Category "{name}" created successfully!')
        return redirect('menu:category_list')
    
    return render(request, 'menu/category_form.html', {'action': 'Create'})


@login_required
def category_update(request, category_id):
    """Update category"""
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to edit categories.')
        return redirect('menu:category_list')
    
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description', '')
        category.display_order = request.POST.get('display_order', 0)
        category.is_active = request.POST.get('is_active') == 'on'
        category.save()
        
        messages.success(request, f'Category "{category.name}" updated successfully!')
        return redirect('menu:category_list')
    
    return render(request, 'menu/category_form.html', {
        'category': category,
        'action': 'Edit'
    })


@login_required
def category_delete(request, category_id):
    """Delete category"""
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to delete categories.')
        return redirect('menu:category_list')
    
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        name = category.name
        # Check if category has items
        item_count = category.items.count()
        
        if item_count > 0:
            messages.error(request, f'Cannot delete "{name}". It has {item_count} menu items. Please move or delete those items first.')
            return redirect('menu:category_list')
        
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully!')
        return redirect('menu:category_list')
    
    return render(request, 'menu/category_confirm_delete.html', {'category': category})
