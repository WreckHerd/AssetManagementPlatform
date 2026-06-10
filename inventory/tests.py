from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from inventory.models import Category, Asset, Booking, AssetHealth, AuditLog

User = get_user_model()

class SAMRAPTestCase(TestCase):
    def setUp(self):
        # Create categories
        self.category = Category.objects.create(name="Cameras", description="Lenses and bodies")
        
        # Create assets
        self.camera = Asset.objects.create(
            name="Sony A7R IV",
            description="61MP DSLR Camera",
            category=self.category,
            total_qty=2,
            status=Asset.Status.READY
        )
        
        # Create test users
        self.admin = User.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="password123",
            name="Admin Tester",
            role=User.Role.ADMIN
        )
        self.member1 = User.objects.create_user(
            username="member_test1",
            email="member1@test.com",
            password="password123",
            name="Member Tester 1",
            role=User.Role.USER
        )
        self.member2 = User.objects.create_user(
            username="member_test2",
            email="member2@test.com",
            password="password123",
            name="Member Tester 2",
            role=User.Role.USER
        )

        self.client = Client()

    def test_user_authentication_flows(self):
        # 1. Test Login with invalid credentials
        response = self.client.post(reverse('login'), {
            'username': 'member_test1',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200) # Renders login page with errors
        self.assertFalse('_auth_user_id' in self.client.session)

        # 2. Test Login with valid credentials
        response = self.client.post(reverse('login'), {
            'username': 'member_test1',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue('_auth_user_id' in self.client.session)

        # 3. Test Logout
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_role_based_access_controls(self):
        # Non-logged-in user should redirect to login
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

        # Regular user tries to access admin requests
        self.client.login(username='member_test1', password='password123')
        response = self.client.get(reverse('admin_requests'))
        self.assertRedirects(response, reverse('dashboard')) # Redirects to dashboard with error

        # Admin user accesses admin requests
        self.client.logout()
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('admin_requests'))
        self.assertEqual(response.status_code, 200)

    def test_booking_overlap_prevention_logic(self):
        # Log in member1
        self.client.login(username='member_test1', password='password123')
        
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(days=2)

        # Booking 1: Request 1 Sony Camera (Total stock is 2) - should succeed
        response = self.client.post(reverse('booking_request', args=[self.camera.id]), {
            'quantity': 1,
            'start_date': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_date': end_time.strftime('%Y-%m-%dT%H:%M')
        })
        self.assertRedirects(response, reverse('booking_list'))
        
        # Verify booking created with pending status
        booking1 = Booking.objects.get(user=self.member1, asset=self.camera)
        self.assertEqual(booking1.quantity, 1)
        self.assertEqual(booking1.status, Booking.Status.PENDING)

        # Admin approves booking 1 to occupy the inventory
        self.client.logout()
        self.client.login(username='admin_test', password='password123')
        response = self.client.post(reverse('booking_action', args=[booking1.id, 'approve']))
        self.assertRedirects(response, reverse('admin_requests'))
        booking1.refresh_from_db()
        self.assertEqual(booking1.status, Booking.Status.APPROVED)

        # Booking 2 (Member 2): Request 1 Sony Camera in the same period - should succeed (total is 2, 1 is free)
        self.client.logout()
        self.client.login(username='member_test2', password='password123')
        response = self.client.post(reverse('booking_request', args=[self.camera.id]), {
            'quantity': 1,
            'start_date': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_date': end_time.strftime('%Y-%m-%dT%H:%M')
        })
        booking2 = Booking.objects.get(user=self.member2, asset=self.camera)
        self.assertEqual(booking2.status, Booking.Status.PENDING)

        # Admin approves booking 2 - now all 2 stock units are reserved in that period
        self.client.logout()
        self.client.login(username='admin_test', password='password123')
        self.client.post(reverse('booking_action', args=[booking2.id, 'approve']))
        booking2.refresh_from_db()
        self.assertEqual(booking2.status, Booking.Status.APPROVED)

        # Booking 3 (Member 1): Request 1 Sony Camera in the same period - should fail (stock fully occupied)
        self.client.logout()
        self.client.login(username='member_test1', password='password123')
        
        # We try to book the 3rd camera in the same period
        response = self.client.post(reverse('booking_request', args=[self.camera.id]), {
            'quantity': 1,
            'start_date': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_date': end_time.strftime('%Y-%m-%dT%H:%M')
        })
        self.assertRedirects(response, reverse('asset_list')) # Redirects back with error
        # Verify no 3rd booking was saved (remains only 2 active bookings)
        self.assertEqual(Booking.objects.filter(asset=self.camera).count(), 2)

        # Booking 4 (Member 1): Request 1 Sony Camera in a non-overlapping future period - should succeed
        future_start = end_time + timedelta(days=1)
        future_end = future_start + timedelta(days=1)
        response = self.client.post(reverse('booking_request', args=[self.camera.id]), {
            'quantity': 1,
            'start_date': future_start.strftime('%Y-%m-%dT%H:%M'),
            'end_date': future_end.strftime('%Y-%m-%dT%H:%M')
        })
        self.assertRedirects(response, reverse('booking_list'))
        # Total bookings should now be 3 (2 approved overlapping, 1 pending non-overlapping)
        self.assertEqual(Booking.objects.filter(asset=self.camera).count(), 3)

    def test_issuance_and_return_workflows(self):
        # 1. Create a booking that is approved
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=4)
        booking = Booking.objects.create(
            user=self.member1,
            asset=self.camera,
            quantity=1,
            start_date=start,
            end_date=end,
            status=Booking.Status.APPROVED
        )

        # Log in as Admin to issue
        self.client.login(username='admin_test', password='password123')
        
        # 2. Check-out (Issue) asset
        response = self.client.get(reverse('booking_action', args=[booking.id, 'issue']))
        self.assertRedirects(response, reverse('admin_requests'))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.ISSUED)
        self.assertIsNotNone(booking.issued_at)

        # 3. Check-in (Return) asset and update condition
        response = self.client.post(reverse('booking_action', args=[booking.id, 'return']), {
            'condition': 'Fair',
            'notes': 'Slight scratches on lens'
        })
        self.assertRedirects(response, reverse('admin_requests'))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.RETURNED)
        self.assertIsNotNone(booking.returned_at)

        # Verify Asset Health History record was logged
        health_record = AssetHealth.objects.filter(asset=self.camera).latest('created_at')
        self.assertEqual(health_record.condition, 'Fair')
        self.assertIn('Slight scratches on lens', health_record.notes)
