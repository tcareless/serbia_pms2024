# passwords/views.py
from django.db.models import Q
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Password, DeletedPassword
from .forms import PasswordForm

def password_list(request):
    query = request.GET.get('q')
    sort = request.GET.get('sort', '-id')  # Default sort by ID descending
    sort = sort if sort else '-id'  # Default to '-id' if sort is None or empty
    
    if query:
        passwords = Password.objects.filter(
            Q(machine__icontains=query) |
            Q(label__icontains=query) |
            Q(username__icontains=query) |
            Q(password__icontains=query)
        ).order_by(sort)
    else:
        passwords = Password.objects.all().order_by(sort)
    
    return render(request, 'passwords/password_list.html', {'passwords': passwords, 'query': query, 'sort': sort})


def password_create(request):
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('password_list')
    else:
        form = PasswordForm()
    return render(request, 'passwords/password_form.html', {'form': form})

def password_edit(request, pk):
    password = get_object_or_404(Password, pk=pk)
    if request.method == 'POST':
        form = PasswordForm(request.POST, instance=password)
        if form.is_valid():
            form.save()
            return redirect('password_list')
    else:
        form = PasswordForm(instance=password)
    return render(request, 'passwords/password_form.html', {'form': form})

def password_delete(request, pk):
    password = get_object_or_404(Password, pk=pk)
    DeletedPassword.objects.create(
        machine=password.machine,
        label=password.label,
        username=password.username,
        password=password.password,
        deleted_at=timezone.now()
    )
    password.delete()
    return redirect('password_list')

def deleted_passwords(request):
    deleted_passwords = DeletedPassword.objects.all().order_by('-id')  # Order by ID descending
    return render(request, 'passwords/deleted_passwords.html', {'deleted_passwords': deleted_passwords})


def password_recover(request, pk):
    deleted_password = get_object_or_404(DeletedPassword, pk=pk)
    
    with transaction.atomic():
        Password.objects.create(
            machine=deleted_password.machine,
            label=deleted_password.label,
            username=deleted_password.username,
            password=deleted_password.password,
        )
        deleted_password.delete()
    
    return redirect('password_list')