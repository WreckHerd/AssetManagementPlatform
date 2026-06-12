from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inventory.models import Category, Asset, AssetHealth

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds the database with default categories, items, and test users."

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")
        
        # 1. Clear existing database
        self.stdout.write("Clearing existing records...")
        AssetHealth.objects.all().delete()
        Asset.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()

        # 2. Create default users
        self.stdout.write("Creating default credentials...")
        admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass",
            name="System Admin",
            role=User.Role.ADMIN
        )
        self.stdout.write("Created Admin: username 'admin', password 'adminpass'")

        user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="userpass",
            name="General User",
            role=User.Role.USER
        )
        self.stdout.write("Created User: username 'user', password 'userpass'")

        # 3. Create default categories
        self.stdout.write("Creating categories...")
        categories_data = [
            ("Cameras", "DSLRs, mirrorless cameras, and lens assets"),
            ("Studio Lighting", "Strobes, continuous LED lights, and diffusers"),
            ("Audio Systems", "Speakers, amplifiers, and mixer consoles"),
            ("Costumes", "Traditional, theater, and theme clothing sets"),
            ("Stage Props", "Stage infrastructure, backgrounds, and weapons"),
            ("Recording Equipment", "Microphones, audio recorders, and tripods"),
        ]
        
        categories = {}
        for name, desc in categories_data:
            cat = Category.objects.create(name=name, description=desc)
            categories[name] = cat
            self.stdout.write(f"Category '{name}' created.")

        # 4. Create sample assets
        self.stdout.write("Creating assets...")
        assets_data = [
            # Cameras
            ("Sony Alpha 7 IV DSLR", "Full-frame mirrorless camera with 28-70mm lens kit", "Cameras", 4),
            ("Canon EOS R6 Mark II", "Full-frame mirrorless camera body for high-speed photography", "Cameras", 3),
            
            # Studio Lighting
            ("Godox SL60W Studio Light", "60W LED continuous light with Bowens mount reflector", "Studio Lighting", 8),
            ("Aputure Amaran 200d", "200W daylight point-source LED light", "Studio Lighting", 5),
            
            # Audio Systems
            ("JBL PartyBox 310", "Portable party speaker with built-in lights and bluetooth", "Audio Systems", 4),
            ("Rode Wireless GO II Mic", "Dual-channel wireless microphone system with transmitters", "Audio Systems", 10),
            
            # Costumes
            ("Classical Dance Costumes", "Traditional Indian classical dance dress sets (multiple sizes)", "Costumes", 15),
            ("Theater Stage Robes", "Velvet historical robes for theatrical drama enactments", "Costumes", 20),
            
            # Stage Props
            ("Wooden Theater Swords", "Handcrafted safety wooden swords for combat play", "Stage Props", 12),
            ("Decorative Handheld Fans", "Folding fans for traditional cultural dance props", "Stage Props", 25),
            
            # Recording Equipment
            ("Zoom H6 Handy Recorder", "6-track portable audio recorder with interchangeable mic capsules", "Recording Equipment", 6),
            ("Shure SM58 Vocal Mic", "Cardioid dynamic vocal microphone for live stage performances", "Recording Equipment", 12),
        ]

        for name, desc, cat_name, qty in assets_data:
            cat = categories[cat_name]
            asset = Asset.objects.create(
                name=name,
                description=desc,
                category=cat,
                total_qty=qty,
                status=Asset.Status.READY
            )
            # Add initial health record
            AssetHealth.objects.create(
                asset=asset,
                condition="Good",
                notes="Initial seeding check-in. Condition verified."
            )
            self.stdout.write(f"Asset '{name}' created with quantity {qty}.")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
