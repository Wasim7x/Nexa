import asyncio
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import engine, Base, AsyncSessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.shared import (
    Merchant,
    MerchantUser,
    Customer,
    CustomerMerchantProfile,
    MerchantSettings,
    KnowledgeDocument,
    Conversation,
    Message,
    SupportEscalation,
    AuditLog
)
from backend.app.models.grocery import GroceryProduct, GroceryInventory, GroceryOrder, GroceryOrderItem
from backend.app.models.sweets import SweetsProduct, SweetsInventory, SweetsOrder, SweetsOrderItem
from backend.app.models.salon import SalonService, SalonStaff, SalonAvailability, SalonAppointment
from backend.app.models.dental import DentalService, DentalStaff, DentalAvailability, DentalAppointment

async def init_db():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables initialized.")

async def seed_data():
    """Seed comprehensive demo data for all 4 merchants."""
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(Merchant))
        if result.scalars().first():
            print("Database already contains merchants. Skipping seed.")
            return

        print("Seeding database with multi-merchant records...")
        pwd_hash = get_password_hash("Password123!")

        # ----------------------------------------------------
        # 1. GROCERY STORE
        # ----------------------------------------------------
        grocery_merchant = Merchant(
            id="grocery-store",
            name="FreshMart Grocery",
            slug="grocery",
            business_type="grocery",
            phone_number="+15550100001",
            description="Your premium neighborhood grocery store with organic produce, dairy, bakery, and pantry staples."
        )
        session.add(grocery_merchant)

        grocery_user = MerchantUser(
            id="user-grocery-admin",
            merchant_id="grocery-store",
            email="admin@freshmart.com",
            hashed_password=pwd_hash,
            full_name="Sarah Jenkins",
            role="admin"
        )
        session.add(grocery_user)

        grocery_settings = MerchantSettings(
            merchant_id="grocery-store",
            business_hours="Mon-Sun: 7:00 AM - 10:00 PM",
            timezone="America/New_York",
            notification_phone="+15550109991",
            notification_channel="whatsapp",
            escalation_message="I'm connecting you with FreshMart customer support for your order inquiry.",
            welcome_message="Welcome to FreshMart Grocery! I can help you check prices, search organic produce, and track or place your delivery orders.",
            ai_provider="mock",
            ai_model="default"
        )
        session.add(grocery_settings)

        # Grocery Knowledge Docs
        session.add(KnowledgeDocument(
            merchant_id="grocery-store",
            title="FreshMart Store Policies & Delivery",
            doc_type="policy",
            content="FreshMart provides same-day delivery within a 5-mile radius on all orders placed before 6:00 PM. Minimum order for free delivery is $35. Returns on unopened non-perishable goods are accepted within 7 days with receipt. Perishable items (dairy, fresh produce) can be refunded if reported within 24 hours.",
            is_published=True
        ))
        session.add(KnowledgeDocument(
            merchant_id="grocery-store",
            title="FreshMart Weekly Specials",
            doc_type="offer",
            content="Special Offers this week: Buy 1 gallon of Organic Whole Milk get 1 free Organic Eggs dozen! 20% discount on California Avocados and Basmati Rice 5kg bags.",
            is_published=True
        ))

        # Grocery Products & Inventory
        grocery_items_data = [
            ("Organic Whole Milk 1 Gallon", "Dairy", "gallon", Decimal("4.99"), 45, "Fresh organic whole milk from local pasture-raised cows."),
            ("Farm Fresh Eggs (Dozen)", "Dairy", "carton", Decimal("3.49"), 80, "Grade A large brown eggs from free-range hens."),
            ("Artisan Sourdough Bread", "Bakery", "loaf", Decimal("5.25"), 25, "Slow-fermented artisan sourdough baked fresh daily."),
            ("Organic Hass Avocados (4-pack)", "Produce", "pack", Decimal("4.49"), 60, "Ripe and ready to eat California Hass avocados."),
            ("Royal Basmati Rice 5kg", "Pantry", "bag", Decimal("14.99"), 35, "Aromatic long-grain aged basmati rice."),
            ("Cold Pressed Extra Virgin Olive Oil 750ml", "Pantry", "bottle", Decimal("12.99"), 40, "Single-origin extra virgin cold-pressed olive oil."),
            ("Fresh Organic Bananas", "Produce", "bunch", Decimal("1.89"), 120, "Fair-trade certified ripe organic bananas."),
            ("Greek Yogurt Plain 32oz", "Dairy", "tub", Decimal("5.49"), 30, "Thick and creamy high-protein authentic Greek yogurt.")
        ]

        grocery_product_objs = []
        for name, cat, unit, price, stock, desc in grocery_items_data:
            prod = GroceryProduct(
                merchant_id="grocery-store",
                name=name,
                category=cat,
                unit=unit,
                price=price,
                description=desc
            )
            session.add(prod)
            inv = GroceryInventory(
                product=prod,
                stock_quantity=stock,
                low_stock_threshold=10
            )
            session.add(inv)
            grocery_product_objs.append(prod)

        # ----------------------------------------------------
        # 2. SWEETS SHOP
        # ----------------------------------------------------
        sweets_merchant = Merchant(
            id="sweets-shop",
            name="Royal Sweets & Delights",
            slug="sweets",
            business_type="sweets",
            phone_number="+15550100002",
            description="Traditional and contemporary artisanal confectionery, mithai, premium gift boxes, and festive savories."
        )
        session.add(sweets_merchant)

        sweets_user = MerchantUser(
            id="user-sweets-admin",
            merchant_id="sweets-shop",
            email="admin@royalsweets.com",
            hashed_password=pwd_hash,
            full_name="Rajesh Patel",
            role="admin"
        )
        session.add(sweets_user)

        sweets_settings = MerchantSettings(
            merchant_id="sweets-shop",
            business_hours="Mon-Sun: 9:00 AM - 10:00 PM",
            timezone="America/New_York",
            notification_phone="+15550109992",
            notification_channel="whatsapp",
            escalation_message="Connecting you with our master confectioner at Royal Sweets for custom orders and special requests.",
            welcome_message="Namaste and welcome to Royal Sweets & Delights! Looking for handcrafted Kaju Katli, Gulab Jamun, or luxury festive gift hampers?",
            ai_provider="mock",
            ai_model="default"
        )
        session.add(sweets_settings)

        # Sweets Knowledge Docs
        session.add(KnowledgeDocument(
            merchant_id="sweets-shop",
            title="Royal Sweets Gifting & Freshness Policy",
            doc_type="policy",
            content="All sweets are prepared fresh each morning with 100% pure desi ghee and premium nuts. Dry fruit sweets retain peak freshness for 15 days at room temperature. Milk sweets (Rasgulla, Cham Cham) must be refrigerated and enjoyed within 4 days. Custom gift packaging and message tags available on request.",
            is_published=True
        ))
        session.add(KnowledgeDocument(
            merchant_id="sweets-shop",
            title="Festive Discounts and Sugar-Free Range",
            doc_type="offer",
            content="Order 2kg or more of Royal Assorted Gift Hampers and receive a complimentary 250g box of Pistachio Barfi. We also feature Stevia-sweetened sugar-free Kaju Katli and Besan Ladoo.",
            is_published=True
        ))

        # Sweets Products & Inventory
        sweets_items_data = [
            ("Premium Kaju Katli", "Dry Fruit Sweets", "kg", Decimal("22.00"), 50, "Signature diamond-shaped cashew delicacy prepared with pure silver leaf.", False),
            ("Sugar-Free Kaju Katli", "Dry Fruit Sweets", "kg", Decimal("24.00"), 25, "Stevia-sweetened rich cashew squares for health-conscious sweet lovers.", True),
            ("Desi Ghee Gulab Jamun (12 pcs)", "Milk Sweets", "box", Decimal("14.50"), 40, "Melt-in-mouth soft dumplings soaked in fragrant cardamom saffron syrup.", False),
            ("Spongy Kolkata Rasgulla (10 pcs)", "Bengali Sweets", "box", Decimal("13.00"), 35, "Classic delicate cottage cheese balls poached in light sugar syrup.", False),
            ("Motichoor Ladoo Pure Ghee", "Traditional", "kg", Decimal("16.00"), 60, "Fine golden gram flour pearls infused with saffron and crushed cardamom.", False),
            ("Royal Royal Celebration Gift Hamper (1kg)", "Gift Boxes", "box", Decimal("32.00"), 30, "Luxurious assortment of Kaju Katli, Pista Roll, Almond Barfi, and Anjeer King.", False),
            ("Spicy Kaju Masala Savory", "Snacks", "500g", Decimal("15.00"), 45, "Roasted whole cashews tossed in savory chaat masala spices.", False)
        ]

        sweets_product_objs = []
        for name, cat, unit, price, stock, desc, is_sf in sweets_items_data:
            prod = SweetsProduct(
                merchant_id="sweets-shop",
                name=name,
                category=cat,
                unit=unit,
                price=price,
                description=desc,
                is_sugar_free=is_sf
            )
            session.add(prod)
            inv = SweetsInventory(
                product=prod,
                stock_quantity=stock,
                batch_freshness_date="Today"
            )
            session.add(inv)
            sweets_product_objs.append(prod)

        # ----------------------------------------------------
        # 3. GLOW SALON
        # ----------------------------------------------------
        salon_merchant = Merchant(
            id="glow-salon",
            name="Glow & Glamour Salon",
            slug="salon",
            business_type="salon",
            phone_number="+15550100003",
            description="Luxury hair, skincare, and bridal salon offering personalized beauty and spa experiences."
        )
        session.add(salon_merchant)

        salon_user = MerchantUser(
            id="user-salon-admin",
            merchant_id="glow-salon",
            email="admin@glowsalon.com",
            hashed_password=pwd_hash,
            full_name="Elena Rostova",
            role="admin"
        )
        session.add(salon_user)

        salon_settings = MerchantSettings(
            merchant_id="glow-salon",
            business_hours="Tue-Sun: 10:00 AM - 8:00 PM (Closed Mondays)",
            timezone="America/New_York",
            notification_phone="+15550109993",
            notification_channel="whatsapp",
            escalation_message="Transferring you to our salon receptionist for customized beauty packages and stylist scheduling.",
            welcome_message="Welcome to Glow & Glamour Salon! Ready to treat yourself? I can check stylist openings, explain services, and book your appointment.",
            ai_provider="mock",
            ai_model="default"
        )
        session.add(salon_settings)

        # Salon Knowledge Docs
        session.add(KnowledgeDocument(
            merchant_id="glow-salon",
            title="Salon Booking & Cancellation Guidelines",
            doc_type="policy",
            content="Appointments may be rescheduled or cancelled without fee up to 4 hours in advance. Please arrive 10 minutes prior to scheduled treatment. Complimentary beverages and consultation included with all hair and facial treatments.",
            is_published=True
        ))

        # Salon Services
        salon_services_data = [
            ("Signature Haircut & Blowout", "Hair Care", 60, Decimal("65.00"), "Includes customized hair consultation, soothing scalp massage, precision cut, and blowout."),
            ("Hydra-Glow Deep Cleansing Facial", "Skin & Facial", 75, Decimal("95.00"), "Deep pore extraction, ultrasonic exfoliation, and multi-peptide collagen infusion."),
            ("Keratin Smoothing Therapy", "Hair Care", 120, Decimal("180.00"), "Formaldehyde-free smoothing treatment providing 4 months of frizz-free shine."),
            ("Luxury Spa Gel Manicure & Pedicure", "Nails", 90, Decimal("75.00"), "Exfoliating sugar scrub, hot stone massage, cuticle care, and chip-free gel polish."),
            ("Full Body Aromatherapy Massage", "Spa & Massage", 60, Decimal("110.00"), "Swedish relaxation massage utilizing customized organic essential oil blends.")
        ]

        salon_service_objs = []
        for name, cat, dur, price, desc in salon_services_data:
            serv = SalonService(
                merchant_id="glow-salon",
                name=name,
                category=cat,
                duration_minutes=dur,
                price=price,
                description=desc
            )
            session.add(serv)
            salon_service_objs.append(serv)

        # Salon Staff
        staff_elena = SalonStaff(
            merchant_id="glow-salon",
            name="Elena Rostova",
            role="Master Stylist",
            specialties="Precision cuts, balayage, keratin smoothing"
        )
        staff_maya = SalonStaff(
            merchant_id="glow-salon",
            name="Maya Chen",
            role="Senior Esthetician",
            specialties="Hydra-facials, chemical peels, acne therapies"
        )
        session.add_all([staff_elena, staff_maya])
        await session.flush()

        # Salon Availability Slots (for tomorrow and day after)
        tomorrow = date.today() + timedelta(days=1)
        day_after = date.today() + timedelta(days=2)

        for d in [tomorrow, day_after]:
            for st, et in [(time(10, 0), time(11, 0)), (time(11, 30), time(12, 30)), (time(14, 0), time(15, 0)), (time(16, 0), time(17, 0))]:
                session.add(SalonAvailability(
                    merchant_id="glow-salon",
                    staff_id=staff_elena.id,
                    slot_date=d,
                    start_time=st,
                    end_time=et,
                    is_booked=False
                ))
            for st, et in [(time(10, 30), time(11, 45)), (time(13, 0), time(14, 15)), (time(15, 30), time(16, 45))]:
                session.add(SalonAvailability(
                    merchant_id="glow-salon",
                    staff_id=staff_maya.id,
                    slot_date=d,
                    start_time=st,
                    end_time=et,
                    is_booked=False
                ))

        # ----------------------------------------------------
        # 4. DENTAL CLINIC
        # ----------------------------------------------------
        dental_merchant = Merchant(
            id="dental-clinic",
            name="SmileCare Dental Clinic",
            slug="dental",
            business_type="dental",
            phone_number="+15550100004",
            description="Compassionate, state-of-the-art family and cosmetic dental care with gentle sedation options."
        )
        session.add(dental_merchant)

        dental_user = MerchantUser(
            id="user-dental-admin",
            merchant_id="dental-clinic",
            email="admin@smilecaredental.com",
            hashed_password=pwd_hash,
            full_name="Dr. Marcus Vance",
            role="admin"
        )
        session.add(dental_user)

        dental_settings = MerchantSettings(
            merchant_id="dental-clinic",
            business_hours="Mon-Fri: 8:00 AM - 5:00 PM (Emergency line on weekends)",
            timezone="America/New_York",
            notification_phone="+15550109994",
            notification_channel="whatsapp",
            escalation_message="I am connecting you with the SmileCare clinical front desk team for professional dental assistance.",
            welcome_message="Welcome to SmileCare Dental Clinic! I can help you review our dental services, schedule cleanings or consultations, and find appointment slots.",
            ai_provider="mock",
            ai_model="default"
        )
        session.add(dental_settings)

        # Dental Knowledge Docs
        session.add(KnowledgeDocument(
            merchant_id="dental-clinic",
            title="SmileCare Appointment & Clinical Disclaimer Policy",
            doc_type="policy",
            content="SmileCare provides preventative, cosmetic, and emergency dental appointments. Vera is an administrative assistant and cannot diagnose symptoms, prescribe medications, or provide medical treatment advice. If you are experiencing severe swelling, uncontrollable bleeding, or difficulty breathing, please seek emergency medical attention or contact our emergency desk immediately.",
            is_published=True
        ))
        session.add(KnowledgeDocument(
            merchant_id="dental-clinic",
            title="Dental Insurance and Payment Plans",
            doc_type="faq",
            content="We accept most PPO insurance plans including Delta Dental, MetLife, Cigna, and Guardian. Flexible 0% interest payment plans are available via CareCredit.",
            is_published=True
        ))

        # Dental Services
        dental_services_data = [
            ("Comprehensive Dental Exam & Cleaning", "Preventative", 60, Decimal("120.00"), "Full oral cancer screening, periodontal charting, digital bitewing x-rays, and ultrasonic cleaning."),
            ("Professional In-Office Teeth Whitening", "Cosmetic", 60, Decimal("299.00"), "Advanced LED-accelerated bleaching delivering up to 8 shades brighter in one hour."),
            ("Emergency Toothache Consultation", "Emergency", 30, Decimal("85.00"), "Targeted diagnostic x-ray, clinical examination of pain site, and urgent stabilization plan."),
            ("Invisalign & Orthodontic Evaluation", "Orthodontics", 45, Decimal("75.00"), "3D digital iTero scan and treatment simulation for clear aligners."),
            ("Pediatric Dental Checkup (Under 12)", "Pediatric", 45, Decimal("90.00"), "Gentle fluoride treatment, gentle cleaning, cavity prevention sealing, and habit coaching.")
        ]

        dental_service_objs = []
        for name, cat, dur, fee, desc in dental_services_data:
            serv = DentalService(
                merchant_id="dental-clinic",
                name=name,
                category=cat,
                duration_minutes=dur,
                consultation_fee=fee,
                description=desc
            )
            session.add(serv)
            dental_service_objs.append(serv)

        # Dental Staff
        dentist_marcus = DentalStaff(
            merchant_id="dental-clinic",
            name="Dr. Marcus Vance, DDS",
            title="Lead Cosmetic Dentist",
            license_number="DEN-98241",
            specialties="Cosmetic veneers, smile makeovers, restorative crown work"
        )
        dentist_sarah = DentalStaff(
            merchant_id="dental-clinic",
            name="Dr. Sarah Lin, DMD",
            title="Family & Pediatric Dentist",
            license_number="DEN-87312",
            specialties="Preventative hygiene, pediatric dentistry, gentle sedation"
        )
        session.add_all([dentist_marcus, dentist_sarah])
        await session.flush()

        # Dental Availability Slots
        for d in [tomorrow, day_after]:
            for st, et in [(time(9, 0), time(10, 0)), (time(10, 30), time(11, 30)), (time(13, 0), time(14, 0)), (time(14, 30), time(15, 30))]:
                session.add(DentalAvailability(
                    merchant_id="dental-clinic",
                    dentist_id=dentist_marcus.id,
                    slot_date=d,
                    start_time=st,
                    end_time=et,
                    is_booked=False
                ))
            for st, et in [(time(9, 30), time(10, 15)), (time(11, 0), time(11, 45)), (time(13, 30), time(14, 15)), (time(15, 0), time(15, 45))]:
                session.add(DentalAvailability(
                    merchant_id="dental-clinic",
                    dentist_id=dentist_sarah.id,
                    slot_date=d,
                    start_time=st,
                    end_time=et,
                    is_booked=False
                ))

        # ----------------------------------------------------
        # 5. SAMPLE CUSTOMERS & TRANSACTIONS
        # ----------------------------------------------------
        cust1 = Customer(
            id="cust-alex",
            whatsapp_phone="+15551234567",
            name="Alex Morgan",
            email="alex.morgan@example.com"
        )
        cust2 = Customer(
            id="cust-priya",
            whatsapp_phone="+15559876543",
            name="Priya Sharma",
            email="priya.sharma@example.com"
        )
        session.add_all([cust1, cust2])
        await session.flush()

        # Customer merchant profiles (Strict Tenant Isolation)
        session.add(CustomerMerchantProfile(
            customer_id=cust1.id,
            merchant_id="grocery-store",
            preferred_name="Alex",
            interaction_count=5,
            notes="Prefers organic dairy and morning deliveries."
        ))
        session.add(CustomerMerchantProfile(
            customer_id=cust1.id,
            merchant_id="glow-salon",
            preferred_name="Alex",
            interaction_count=2,
            notes="Prefers stylist Elena for haircuts."
        ))
        session.add(CustomerMerchantProfile(
            customer_id=cust2.id,
            merchant_id="sweets-shop",
            preferred_name="Priya",
            interaction_count=8,
            notes="Regular customer for Diwali festive gift boxes."
        ))
        session.add(CustomerMerchantProfile(
            customer_id=cust2.id,
            merchant_id="dental-clinic",
            preferred_name="Priya",
            interaction_count=1,
            notes="Interested in teeth whitening."
        ))

        # Sample Orders
        g_order = GroceryOrder(
            id="gord-1001",
            order_number="GRO-1001",
            merchant_id="grocery-store",
            customer_id=cust1.id,
            status="confirmed",
            total_amount=Decimal("13.47"),
            delivery_address="45 Elm St, Apt 3B, New York, NY",
            notes="Leave at door"
        )
        session.add(g_order)
        session.add(GroceryOrderItem(
            order=g_order,
            product_id=grocery_product_objs[0].id,
            product_name="Organic Whole Milk 1 Gallon",
            quantity=2,
            unit_price=Decimal("4.99"),
            total_price=Decimal("9.98")
        ))
        session.add(GroceryOrderItem(
            order=g_order,
            product_id=grocery_product_objs[1].id,
            product_name="Farm Fresh Eggs (Dozen)",
            quantity=1,
            unit_price=Decimal("3.49"),
            total_price=Decimal("3.49")
        ))

        s_order = SweetsOrder(
            id="sord-2001",
            order_number="SWT-2001",
            merchant_id="sweets-shop",
            customer_id=cust2.id,
            status="confirmed",
            total_amount=Decimal("44.00"),
            order_type="pickup",
            gift_packaging=True,
            gift_message="Happy Birthday Uncle!"
        )
        session.add(s_order)
        session.add(SweetsOrderItem(
            order=s_order,
            product_id=sweets_product_objs[0].id,
            product_name="Premium Kaju Katli",
            quantity=2,
            unit_price=Decimal("22.00"),
            total_price=Decimal("44.00")
        ))

        # Sample Appointments
        salon_appt = SalonAppointment(
            id="sappt-3001",
            booking_reference="SLN-3001",
            merchant_id="glow-salon",
            customer_id=cust1.id,
            service_id=salon_service_objs[0].id,
            staff_id=staff_elena.id,
            appointment_date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            status="confirmed",
            notes="Wants layered cut"
        )
        session.add(salon_appt)

        dental_appt = DentalAppointment(
            id="dappt-4001",
            booking_reference="DNT-4001",
            merchant_id="dental-clinic",
            customer_id=cust2.id,
            service_id=dental_service_objs[0].id,
            dentist_id=dentist_marcus.id,
            appointment_date=tomorrow,
            start_time=time(9, 0),
            end_time=time(10, 0),
            status="confirmed",
            chief_complaint="Routine checkup and plaque cleaning"
        )
        session.add(dental_appt)

        # Sample Escalation
        escalation = SupportEscalation(
            id="esc-001",
            merchant_id="dental-clinic",
            customer_id=cust1.id,
            reason="Customer inquired about intense throbbing pain following wisdom tooth extraction. Safely referred to emergency care and front desk notified.",
            category="dental_clinical",
            status="pending",
            urgency="high"
        )
        session.add(escalation)

        # Audit Log
        audit = AuditLog(
            merchant_id="dental-clinic",
            customer_phone="+15551234567",
            action="GUARDRAIL_DENTAL_SAFETY_TRIGGERED",
            resource_type="message",
            status="success",
            details_json={"note": "Redirected clinical diagnosis query to licensed dentist"}
        )
        session.add(audit)

        await session.commit()
        print("Database successfully seeded with 4 merchants, products, services, slots, and demo transactions!")

if __name__ == "__main__":
    asyncio.run(seed_data())
