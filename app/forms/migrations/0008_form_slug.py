from django.db import migrations, models
from django.utils.text import slugify

from django.utils.text import slugify
from django.db import migrations

def populate_slugs(apps, schema_editor):
    Form = apps.get_model('forms', 'Form')
    existing_slugs = set()
    for form in Form.objects.all():
        base_slug = slugify(form.name or f"form-{form.id}")
        slug = base_slug
        counter = 1

        # Ensure the slug is unique by appending a counter if necessary
        while slug in existing_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1

        form.slug = slug
        form.save()
        existing_slugs.add(slug)

class Migration(migrations.Migration):
    dependencies = [
        ('forms', '0007_formanswer_operator_number'),  # Adjust based on your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='form',
            name='slug',
            field=models.SlugField(unique=True, blank=True, null=True),
        ),
        migrations.RunPython(populate_slugs),
        migrations.AlterField(
            model_name='form',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]





