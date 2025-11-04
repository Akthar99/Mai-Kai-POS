from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def customer_list(request):
    from .models import Customer
    customers = Customer.objects.all().order_by('-last_visit')
    
    # Calculate statistics
    loyalty_members_count = sum(1 for c in customers if c.loyalty_tier)
    vip_customers_count = sum(1 for c in customers if c.loyalty_tier == 'platinum')
    
    context = {
        'customers': customers,
        'loyalty_members_count': loyalty_members_count,
        'vip_customers_count': vip_customers_count,
    }
    
    return render(request, 'customers/customer_list.html', context)


@login_required
def customer_detail(request, customer_id):
    from .models import Customer
    from django.shortcuts import get_object_or_404
    customer = get_object_or_404(Customer, id=customer_id)
    return render(request, 'customers/customer_detail.html', {'customer': customer})


@login_required
def loyalty_program(request):
    return render(request, 'customers/loyalty_program.html')
