from django.db import migrations, models
import quality.models

class Migration(migrations.Migration):

    dependencies = [
        ('quality', '0017_redrabbittype_part'),
    ]

    operations = [
        migrations.CreateModel(
            name='QualityTagDropdownOptions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.JSONField(blank=True, default=quality.models.default_dropdown_data)),
            ],
            options={
                'verbose_name': 'Quality Tag Dropdown Options',
                'verbose_name_plural': 'Quality Tag Dropdown Options',
            },
        ),
    ]
