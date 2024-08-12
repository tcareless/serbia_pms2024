#views/password_views.py
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from ..models.password_models import Password
from ..forms.password_forms import PasswordForm
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
            Q(password_asset__asset_number__icontains=query) |  # Updated to search by asset number
            Q(label__icontains=query) |
            Q(username__icontains=query) |
            Q(password__icontains=query),
            deleted=False  # Exclude deleted records
        ).order_by(sort)
    else:
        passwords = Password.objects.filter(deleted=False).order_by(sort)

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
    password.deleted = True
    password.deleted_at = timezone.now()
    password.save()
    return redirect('password_list')


def deleted_passwords(request):
    deleted_passwords = Password.objects.filter(deleted=True).order_by('-deleted_at')
    return render(request, 'passwords/deleted_passwords.html', {'deleted_passwords': deleted_passwords})


def password_recover(request, pk):
    password = get_object_or_404(Password, pk=pk)
    if password.deleted:
        password.deleted = False
        password.deleted_at = None
        password.save()
    return redirect('password_list')
