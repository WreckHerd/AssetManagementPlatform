from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        USER = 'USER', 'User'
        
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER
    )

    def is_admin(self):
        return self.role == self.Role.ADMIN

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Asset(models.Model):
    class Status(models.TextChoices):
        READY = 'READY', 'Ready'
        MAINTENANCE = 'MAINTENANCE', 'In Maintenance'
        DAMAGED = 'DAMAGED', 'Damaged'
        RETIRED = 'RETIRED', 'Retired'

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='assets')
    total_qty = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.READY
    )
    qr_code_url = models.TextField(blank=True, null=True)  # Base64 string for SVG/PNG
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'
        ISSUED = 'ISSUED', 'Issued'
        RETURNED = 'RETURNED', 'Returned'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='bookings')
    quantity = models.PositiveIntegerField(default=1)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    admin_comment = models.TextField(blank=True, null=True)
    issued_at = models.DateTimeField(blank=True, null=True)
    returned_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.asset.name} ({self.quantity})"

class AssetHealth(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='health_history')
    condition = models.CharField(max_length=100)  # e.g., "Good", "Fair", "Damaged", "Unusable"
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.name} - {self.condition} ({self.created_at.date()})"

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100)  # e.g., "ASSET_CREATE", "BOOKING_APPROVE"
    details = models.TextField()  # JSON formatted string
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        actor = self.user.username if self.user else "System"
        return f"{actor} - {self.action} at {self.created_at}"
