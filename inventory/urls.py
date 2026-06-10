from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # Assets CRUD
    path('assets/', views.asset_list_view, name='asset_list'),
    path('assets/add/', views.asset_add_view, name='asset_add'),
    path('assets/<int:pk>/edit/', views.asset_edit_view, name='asset_edit'),
    path('assets/<int:pk>/delete/', views.asset_delete_view, name='asset_delete'),

    # Bookings
    path('bookings/', views.booking_list_view, name='booking_list'),
    path('bookings/request/<int:asset_id>/', views.booking_request_view, name='booking_request'),

    # Admin actions & tracking
    path('approvals/', views.admin_requests_view, name='admin_requests'),
    path('bookings/<int:pk>/action/<str:action>/', views.booking_action_view, name='booking_action'),
    
    # Analytics & Audit Logs
    path('analytics/', views.analytics_view, name='analytics'),
    path('audit-logs/', views.audit_logs_view, name='audit_logs'),

    # QR Scan simulation
    path('qr/scan/<int:pk>/', views.qr_scan_action, name='qr_scan_action'),
    path('qr/scanner/', views.qr_scanner_view, name='qr_scanner'),
]
