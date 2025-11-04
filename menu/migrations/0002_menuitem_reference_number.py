# Generated migration for adding reference_number field to MenuItem

from django.db import migrations, models


def set_default_reference_numbers(apps, schema_editor):
    """Set temporary reference numbers for existing menu items"""
    MenuItem = apps.get_model('menu', 'MenuItem')
    items = MenuItem.objects.all().order_by('id')
    
    for index, item in enumerate(items, start=1):
        # Format as TEMP-XXX so admin knows to change them
        item.reference_number = f"TEMP{index:03d}"
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0001_initial'),
    ]

    operations = [
        # Step 1: Add field as nullable
        migrations.AddField(
            model_name='menuitem',
            name='reference_number',
            field=models.CharField(
                blank=True,
                null=True,
                help_text='Menu reference number (e.g., 001, 002)',
                max_length=10
            ),
        ),
        # Step 2: Populate with temporary values
        migrations.RunPython(set_default_reference_numbers, migrations.RunPython.noop),
        # Step 3: Make it non-nullable and unique
        migrations.AlterField(
            model_name='menuitem',
            name='reference_number',
            field=models.CharField(
                max_length=10,
                unique=True,
                help_text='Menu reference number (e.g., 001, 002)'
            ),
        ),
        # Step 4: Update ordering
        migrations.AlterModelOptions(
            name='menuitem',
            options={'ordering': ['reference_number']},
        ),
    ]
