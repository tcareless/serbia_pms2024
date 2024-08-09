# passwords/views.py
from django.db.models import Q
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from ..models.password_models import Password, DeletedPassword
from ..forms.password_forms import PasswordForm
from django.http import HttpResponse
from django.core.paginator import Paginator


def auth_page(request):
    error_message = None
    if request.method == 'POST':
        input_value = request.POST.get('auth_input', '')
        if input_value == 'stackpole1':
            request.session['authenticated'] = True
            return redirect('password_list')
        else:
            error_message = "Incorrect password. Please try again."

    return render(request, 'passwords/auth.html', {'error_message': error_message})


def password_list(request):
    if not request.session.get('authenticated'):
        return redirect('auth_page')

    query = request.GET.get('q', '')  # Default to empty string if None
    sort = request.GET.get('sort', '-id')
    per_page = request.GET.get('per_page', 25)
    
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 25

    if query:
        passwords = Password.objects.filter(
            Q(machine__icontains=query) |
            Q(label__icontains=query) |
            Q(username__icontains=query) |
            Q(password__icontains=query)
        ).order_by(sort)
    else:
        passwords = Password.objects.all().order_by(sort)

    paginator = Paginator(passwords, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'passwords/password_list.html', {
        'page_obj': page_obj,
        'query': query,
        'sort': sort,
        'per_page': per_page,
    })


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
