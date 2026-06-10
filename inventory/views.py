import json
from django.shortcuts import render, redirect, get_object_or_anchor, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.urls import reverse

from .models import Category, Asset, Booking, AssetHealth, AuditLog
from .forms import UserRegistrationForm, AssetForm, BookingRequestForm, AssetHealthForm

import qrcode
import io
import base64

User = get_user_model()

# Custom Decorator for Admin access
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_admin():
            messages.error(request, "Access denied. Administrator privileges required.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

# Helper to log actions
def log_action(user, action, details):
    AuditLog.objects.create(
        user=user if user.is_authenticated else None,
        action=action,
        details=json.dumps(details, default=str)
    )

# --- Authentication Views ---

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.is_ajax or request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(user, "USER_REGISTER", {"username": user.username, "role": user.role})
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'inventory/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            log_action(user, "USER_LOGIN", {"username": user.username})
            messages.success(request, f"Logged in successfully. Welcome back, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'inventory/login.html')

def logout_view(request):
    if request.user.is_authenticated:
        log_action(request.user, "USER_LOGOUT", {"username": request.user.username})
        logout(request)
        messages.success(request, "You have been logged out.")
    return redirect('login')


# --- Dashboard View ---

@login_required
def dashboard_view(request):
    if request.user.is_admin():
        # Admin Dashboard data
        total_assets = Asset.objects.count()
        pending_requests = Booking.objects.filter(status=Booking.Status.PENDING).count()
        active_loans = Booking.objects.filter(status=Booking.Status.ISSUED).count()
        overdue_loans = Booking.objects.filter(
            status=Booking.Status.ISSUED,
            end_date__lt=timezone.now()
        ).count()

        # Recent activities
        recent_bookings = Booking.objects.select_related('user', 'asset').order_by('-created_at')[:5]
        recent_logs = AuditLog.objects.select_related('user').order_by('-created_at')[:5]

        context = {
            'total_assets': total_assets,
            'pending_requests': pending_requests,
            'active_loans': active_loans,
            'overdue_loans': overdue_loans,
            'recent_bookings': recent_bookings,
            'recent_logs': recent_logs,
            'is_admin': True,
        }
        return render(request, 'inventory/dashboard.html', context)
    else:
        # User Dashboard data
        user_bookings = Booking.objects.filter(user=request.user).select_related('asset').order_by('-created_at')
        active_loans = user_bookings.filter(status=Booking.Status.ISSUED)
        pending_requests = user_bookings.filter(status=Booking.Status.PENDING)
        overdue_loans = active_loans.filter(end_date__lt=timezone.now())

        context = {
            'active_loans': active_loans,
            'pending_requests': pending_requests,
            'overdue_loans': overdue_loans,
            'bookings_count': user_bookings.count(),
            'recent_bookings': user_bookings[:5],
            'is_admin': False,
        }
        return render(request, 'inventory/dashboard.html', context)


# --- Asset Views ---

@login_required
def asset_list_view(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    
    categories = Category.objects.annotate(asset_count=Count('assets'))
    assets = Asset.objects.select_related('category').all()

    if query:
        assets = assets.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id:
        assets = assets.filter(category_id=category_id)

    # Calculate real-time available quantities
    # available_qty = total_qty - sum(issued quantities for active bookings right now)
    now = timezone.now()
    active_issuances = Booking.objects.filter(
        status=Booking.Status.ISSUED
    ).values('asset_id').annotate(allocated=Sum('quantity'))

    allocation_map = {item['asset_id']: item['allocated'] for item in active_issuances}

    asset_data = []
    for asset in assets:
        allocated = allocation_map.get(asset.id, 0)
        available = max(0, asset.total_qty - allocated)
        
        # QR Code lazily generated if empty
        if not asset.qr_code_url:
            qr_data = request.build_absolute_uri(reverse('qr_scan_action', args=[asset.id]))
            asset.qr_code_url = generate_qr_base64_data(qr_data)
            asset.save(update_fields=['qr_code_url'])

        asset_data.append({
            'asset': asset,
            'available': available,
        })

    context = {
        'assets': asset_data,
        'categories': categories,
        'selected_category': category_id,
        'query': query,
    }
    return render(request, 'inventory/asset_list.html', context)


@admin_required
def asset_add_view(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.save()
            
            # Generate QR Code URL mapping
            qr_data = request.build_absolute_uri(reverse('qr_scan_action', args=[asset.id]))
            asset.qr_code_url = generate_qr_base64_data(qr_data)
            asset.save(update_fields=['qr_code_url'])

            log_action(request.user, "ASSET_CREATE", {"asset_id": asset.id, "name": asset.name, "qty": asset.total_qty})
            messages.success(request, f"Asset '{asset.name}' has been added successfully.")
            return redirect('asset_list')
    else:
        form = AssetForm()
    return render(request, 'inventory/asset_form.html', {'form': form, 'title': 'Add New Asset'})


@admin_required
def asset_edit_view(request):
    # Wait, in Django we need asset pk. Let's get pk from view arguments. Let's define the view signature.
    # Actually, we can get it via argument pk. Let's redefine signature as:
    # def asset_edit_view(request, pk):
    pass

# Let's write the complete asset edit view below instead.
