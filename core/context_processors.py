from django.conf import settings


def business_info(request):
    """Add business information to template context"""
    return {
        'BUSINESS_NAME': settings.BUSINESS_NAME,
        'BUSINESS_ADDRESS': settings.BUSINESS_ADDRESS,
        'BUSINESS_PHONE': settings.BUSINESS_PHONE,
        'BUSINESS_EMAIL': settings.BUSINESS_EMAIL,
    }
