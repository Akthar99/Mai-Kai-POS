from django import forms
from .models import Table


class TableForm(forms.ModelForm):
    """Form for creating and editing tables"""
    
    class Meta:
        model = Table
        fields = ['table_number', 'capacity', 'location', 'status', 'assigned_server']
        widgets = {
            'table_number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'e.g., T1, VIP-1'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'min': '1',
                'max': '20'
            }),
            'location': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'e.g., Indoor, Outdoor, VIP Section'
            }),
            'status': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'assigned_server': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
        }
        labels = {
            'table_number': 'Table Number/Name',
            'capacity': 'Seating Capacity',
            'location': 'Location (Optional)',
            'status': 'Current Status',
            'assigned_server': 'Assigned Server (Optional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter assigned_server to only show staff members
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['assigned_server'].queryset = User.objects.filter(
            role__in=['waiter', 'manager']
        ).order_by('first_name', 'last_name')
        self.fields['assigned_server'].required = False
        self.fields['location'].required = False
