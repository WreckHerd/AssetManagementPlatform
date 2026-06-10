import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
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

# Helper to generate QR code as Base64 data URL
def generate_qr_base64_data(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#060913", back_color="#ffffff")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# --- Authentication Views ---

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(user, "USER_REGISTER", {"username": user.username, "role": user.role})
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('dashboard')
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
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

    # Include booking form for modal
    booking_form = BookingRequestForm()

    context = {
        'assets': asset_data,
        'categories': categories,
        'selected_category': category_id,
        'query': query,
        'booking_form': booking_form,
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

            # Log audit
            log_action(request.user, "ASSET_CREATE", {"asset_id": asset.id, "name": asset.name, "qty": asset.total_qty})
            # Add initial health record
            AssetHealth.objects.create(asset=asset, condition="Good", notes="Initial setup registration")

            messages.success(request, f"Asset '{asset.name}' has been added successfully.")
            return redirect('asset_list')
    else:
        form = AssetForm()
    return render(request, 'inventory/asset_form.html', {'form': form, 'title': 'Add New Asset'})


@admin_required
def asset_edit_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            asset = form.save()
            log_action(request.user, "ASSET_EDIT", {"asset_id": asset.id, "name": asset.name, "qty": asset.total_qty})
            messages.success(request, f"Asset '{asset.name}' has been updated successfully.")
            return redirect('asset_list')
    else:
        form = AssetForm(instance=asset)
    return render(request, 'inventory/asset_form.html', {'form': form, 'title': f'Edit Asset: {asset.name}', 'asset': asset})


@admin_required
def asset_delete_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    asset_name = asset.name
    log_action(request.user, "ASSET_DELETE", {"asset_id": asset.id, "name": asset_name})
    asset.delete()
    messages.success(request, f"Asset '{asset_name}' has been deleted successfully.")
    return redirect('asset_list')


# --- Booking Engine Views ---

# Helper to check overlap limits
def check_booking_overlap(asset, quantity, start_date, end_date):
    # Query active bookings that overlap with requested range
    # Active means APPROVED or ISSUED. (PENDING bookings don't block inventory, only confirmed reservations do)
    overlapping_bookings = Booking.objects.filter(
        asset=asset,
        status__in=[Booking.Status.APPROVED, Booking.Status.ISSUED],
        start_date__lt=end_date,
        end_date__gt=start_date
    )

    # Walk events timeline to find maximum allocation at any one point in the requested window
    events = []
    for b in overlapping_bookings:
        events.append((b.start_date, b.quantity))
        events.append((b.end_date, -b.quantity))

    # Sort events by time. If times match, return (-qty) before borrow (+qty)
    events.sort(key=lambda x: (x[0], x[1]))

    current_allocated = 0
    max_allocated = 0

    # Evaluate allocated levels at all event points
    for t, qty_change in events:
        current_allocated += qty_change
        if start_date <= t < end_date:
            if current_allocated > max_allocated:
                max_allocated = current_allocated

    # Also evaluate the exact start date in case no events occur within the range
    allocated_at_start = sum(b.quantity for b in overlapping_bookings if b.start_date <= start_date < b.end_date)
    max_allocated = max(max_allocated, allocated_at_start)

    return max_allocated


@login_required
def booking_request_view(request, asset_id):
    asset = get_object_or_404(Asset, pk=asset_id)
    if request.method == 'POST':
        form = BookingRequestForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.asset = asset
            booking.user = request.user
            
            # Prevent requests exceeding total asset stock
            if booking.quantity > asset.total_qty:
                messages.error(request, f"Requested quantity ({booking.quantity}) exceeds total physical inventory ({asset.total_qty}).")
                return redirect('asset_list')

            # Start Transaction Block to lock row and compute overlaps safely
            try:
                with transaction.atomic():
                    # Lock row
                    locked_asset = Asset.objects.select_for_update().get(pk=asset.id)
                    
                    # Run timeline sweep overlap calculation
                    max_allocated = check_booking_overlap(
                        locked_asset, 
                        booking.quantity, 
                        booking.start_date, 
                        booking.end_date
                    )
                    
                    if max_allocated + booking.quantity > locked_asset.total_qty:
                        available_now = locked_asset.total_qty - max_allocated
                        messages.error(request, f"Overlapping booking conflict: only {available_now} units are available for this duration.")
                        return redirect('asset_list')
                        
                    booking.save()
                    log_action(request.user, "BOOKING_REQUEST", {
                        "booking_id": booking.id, 
                        "asset_name": asset.name, 
                        "qty": booking.quantity,
                        "start": booking.start_date,
                        "end": booking.end_date
                    })
                    messages.success(request, f"Booking request for {booking.quantity}x '{asset.name}' submitted successfully.")
            except Exception as e:
                messages.error(request, f"An error occurred while placing booking: {str(e)}")
            
            return redirect('booking_list')
    return redirect('asset_list')


@login_required
def booking_list_view(request):
    bookings = Booking.objects.filter(user=request.user).select_related('asset').order_by('-created_at')
    return render(request, 'inventory/booking_list.html', {'bookings': bookings})


# --- Admin Approvals & Issuance View ---

@admin_required
def admin_requests_view(request):
    pending = Booking.objects.filter(status=Booking.Status.PENDING).select_related('user', 'asset').order_by('-created_at')
    active_loans = Booking.objects.filter(status=Booking.Status.ISSUED).select_related('user', 'asset').order_by('end_date')
    history = Booking.objects.filter(
        status__in=[Booking.Status.APPROVED, Booking.Status.REJECTED, Booking.Status.CANCELLED, Booking.Status.RETURNED]
    ).select_related('user', 'asset').order_by('-updated_at')[:20]

    health_form = AssetHealthForm()

    context = {
        'pending': pending,
        'active_loans': active_loans,
        'history': history,
        'health_form': health_form,
    }
    return render(request, 'inventory/admin_requests.html', context)


@login_required
def booking_action_view(request, pk, action):
    booking = get_object_or_404(Booking, pk=pk)
    
    # Check permissions
    if action == 'cancel':
        if booking.user != request.user and not request.user.is_admin():
            return HttpResponseForbidden("Unauthorized to cancel this request.")
        if booking.status != Booking.Status.PENDING:
            messages.error(request, "Only pending booking requests can be cancelled.")
            return redirect('booking_list')
            
        booking.status = Booking.Status.CANCELLED
        booking.save()
        log_action(request.user, "BOOKING_CANCEL", {"booking_id": booking.id})
        messages.success(request, "Booking request has been cancelled.")
        return redirect('booking_list')
        
    # Actions below require Admin status
    if not request.user.is_admin():
        return HttpResponseForbidden("Admin authorization required.")

    if action == 'approve':
        comment = request.POST.get('admin_comment', '')
        booking.status = Booking.Status.APPROVED
        booking.admin_comment = comment
        booking.save()
        log_action(request.user, "BOOKING_APPROVE", {"booking_id": booking.id, "comment": comment})
        messages.success(request, f"Booking for {booking.user.username} approved.")
        
    elif action == 'reject':
        comment = request.POST.get('admin_comment', '')
        booking.status = Booking.Status.REJECTED
        booking.admin_comment = comment
        booking.save()
        log_action(request.user, "BOOKING_REJECT", {"booking_id": booking.id, "comment": comment})
        messages.success(request, f"Booking for {booking.user.username} rejected.")
        
    elif action == 'issue':
        # Check checkout overlap again to prevent double allocation if status changed
        with transaction.atomic():
            locked_asset = Asset.objects.select_for_update().get(pk=booking.asset.id)
            # Find current active checked out quantity
            now = timezone.now()
            currently_issued = Booking.objects.filter(
                asset=locked_asset,
                status=Booking.Status.ISSUED
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            if currently_issued + booking.quantity > locked_asset.total_qty:
                messages.error(request, f"Cannot check-out: Asset currently out of stock. Active checkouts: {currently_issued}/{locked_asset.total_qty}")
                return redirect('admin_requests')
                
            booking.status = Booking.Status.ISSUED
            booking.issued_at = timezone.now()
            booking.save()
            
        log_action(request.user, "ASSET_ISSUE", {"booking_id": booking.id, "asset": booking.asset.name})
        messages.success(request, f"Asset checked out to {booking.user.username}.")
        
    elif action == 'return':
        # Log returning condition
        condition = request.POST.get('condition', 'Good')
        notes = request.POST.get('notes', 'Normal return check-in')
        
        booking.status = Booking.Status.RETURNED
        booking.returned_at = timezone.now()
        booking.save()
        
        # Log asset condition history
        AssetHealth.objects.create(
            asset=booking.asset,
            condition=condition,
            notes=f"Returned by {booking.user.username}. notes: {notes}"
        )
        
        # Log audit
        log_action(request.user, "ASSET_RETURN", {"booking_id": booking.id, "condition": condition})
        messages.success(request, f"Asset returned successfully. Condition recorded: {condition}.")
        
    return redirect('admin_requests')


# --- Analytics & Visualizations ---

@admin_required
def analytics_view(request):
    # Calculations for stats cards
    total_bookings = Booking.objects.count()
    completed_returns = Booking.objects.filter(status=Booking.Status.RETURNED).count()
    active_issuances = Booking.objects.filter(status=Booking.Status.ISSUED).count()
    overdue_returns = Booking.objects.filter(status=Booking.Status.ISSUED, end_date__lt=timezone.now()).count()

    # Asset utilization rankings: most frequently booked
    utilization_ranks = Booking.objects.values('asset__name').annotate(
        booking_count=Count('id')
    ).order_by('-booking_count')[:10]

    # Category distribution
    category_distribution = Asset.objects.values('category__name').annotate(
        total_quantity=Sum('total_qty')
    ).order_by('-total_quantity')

    # Weekly bookings trend
    weekly_bookings = []
    today = timezone.now().date()
    for i in range(6, -1, -1):
        day = today - timezone.timedelta(days=i)
        count = Booking.objects.filter(created_at__date=day).count()
        weekly_bookings.append({
            'date': day.strftime('%b %d'),
            'count': count
        })

    context = {
        'total_bookings': total_bookings,
        'completed_returns': completed_returns,
        'active_issuances': active_issuances,
        'overdue_returns': overdue_returns,
        'ranks_json': json.dumps(list(utilization_ranks)),
        'category_json': json.dumps(list(category_distribution)),
        'weekly_json': json.dumps(weekly_bookings),
    }
    return render(request, 'inventory/analytics.html', context)


# --- Audit Logs View ---

@admin_required
def audit_logs_view(request):
    logs = AuditLog.objects.select_related('user').order_by('-created_at')[:100]
    return render(request, 'inventory/audit_logs.html', {'logs': logs})


# --- QR scan action & Simulation ---

@login_required
def qr_scan_action(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    
    # Calculate real-time available quantities
    active_issuances = Booking.objects.filter(
        asset=asset,
        status=Booking.Status.ISSUED
    ).aggregate(allocated=Sum('quantity'))['allocated'] or 0
    available = max(0, asset.total_qty - active_issuances)

    recent_health = asset.health_history.order_by('-created_at')[:5]

    # If post action is triggered (e.g. quick checkout/return simulation by admin)
    if request.user.is_admin():
        admin_action = request.POST.get('action')
        if admin_action == 'quick_issue':
            # Create a booking on-the-spot and issue it immediately
            username = request.POST.get('username')
            qty = int(request.POST.get('qty', 1))
            try:
                borrower = User.objects.get(username=username)
                if qty > available:
                    messages.error(request, f"Insufficient stock. Available: {available}")
                else:
                    with transaction.atomic():
                        booking = Booking.objects.create(
                            user=borrower,
                            asset=asset,
                            quantity=qty,
                            start_date=timezone.now(),
                            end_date=timezone.now() + timezone.timedelta(days=7),
                            status=Booking.Status.ISSUED,
                            issued_at=timezone.now()
                        )
                    log_action(request.user, "ASSET_QUICK_ISSUE", {"booking_id": booking.id})
                    messages.success(request, f"Quick issue successful: {qty}x '{asset.name}' checked out to {username}.")
                    return redirect('admin_requests')
            except User.DoesNotExist:
                messages.error(request, f"User '{username}' does not exist.")
                
        elif admin_action == 'quick_return':
            booking_id = request.POST.get('booking_id')
            booking = get_object_or_404(Booking, pk=booking_id)
            booking.status = Booking.Status.RETURNED
            booking.returned_at = timezone.now()
            booking.save()
            
            condition = request.POST.get('condition', 'Good')
            AssetHealth.objects.create(asset=asset, condition=condition, notes="Quick scanner check-in")
            log_action(request.user, "ASSET_QUICK_RETURN", {"booking_id": booking.id})
            messages.success(request, f"Quick return recorded successfully.")
            return redirect('admin_requests')

    # Get active bookings of this asset to display check-in options for admin
    active_bookings = Booking.objects.filter(
        asset=asset,
        status=Booking.Status.ISSUED
    ).select_related('user')

    context = {
        'asset': asset,
        'available': available,
        'recent_health': recent_health,
        'active_bookings': active_bookings,
    }
    return render(request, 'inventory/qr_scan_action.html', context)


@admin_required
def qr_scanner_view(request):
    # Render simulated camera/code reader UI
    if request.method == 'POST':
        asset_id = request.POST.get('asset_id', '').strip()
        if asset_id:
            try:
                asset = Asset.objects.get(id=asset_id)
                return redirect('qr_scan_action', pk=asset.id)
            except (Asset.DoesNotExist, ValueError):
                messages.error(request, f"Invalid asset key or asset not found: '{asset_id}'")
    
    # Send all assets for a dropdown mock select
    assets = Asset.objects.all()
    return render(request, 'inventory/qr_scanner.html', {'assets': assets})
