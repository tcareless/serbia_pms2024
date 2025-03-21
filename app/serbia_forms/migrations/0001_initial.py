# Generated by Django 4.2.16 on 2025-03-21 14:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='serbia_Form',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='serbia_FormType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('template_name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='serbia_FormSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payload', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('form_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='serbia_forms.serbia_formtype')),
            ],
        ),
        migrations.CreateModel(
            name='serbia_FormQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='serbia_forms.serbia_form')),
            ],
        ),
        migrations.CreateModel(
            name='serbia_FormAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.JSONField()),
                ('operator_number', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField()),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='serbia_forms.serbia_formquestion')),
            ],
        ),
        migrations.AddField(
            model_name='serbia_form',
            name='form_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='serbia_forms.serbia_formtype'),
        ),
    ]
