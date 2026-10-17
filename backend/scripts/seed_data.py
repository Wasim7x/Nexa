import asyncio
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

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
    NotificationJob,
    NotificationEvent,
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
    """Idempotently seed demo and operational data for all 4 Nexa merchants."""
    await init_db()

    async with AsyncSessionLocal() as session:
        print("Starting idempotent seed for Nexa Multi-Merchant AI Assistant...")
        pwd_hash = get_password_hash("Password123!")

        # ----------------------------------------------------
        # 1. MERCHANTS & SETTINGS
        # ----------------------------------------------------
        merchants_config = [
            {
                "id": "grocery-store",
                "name": "FreshMart Grocery",
                "slug": "grocery",
                "business_type": "grocery",
                "phone_number": "+917319770043",
                "description": "Premium neighborhood grocery store with organic produce, dairy, bakery, and daily staples.",
                "hours": "Mon-Sat: 8:00 AM - 10:00 PM, Sun: 9:00 AM - 8:00 PM",
                "welcome": "Welcome to FreshMart Grocery on Nexa! Check prices, find organic staples, and order grocery deliveries effortlessly.",
                "escalation": "Connecting you with FreshMart store support. Our team will assist you with your grocery order shortly."
            },
            {
                "id": "sweets-shop",
                "name": "Royal Sweets & Delights",
                "slug": "sweets",
                "business_type": "sweets",
                "phone_number": "+917319770044",
                "description": "Authentic artisan Indian confectioner specializing in pure desi ghee sweets, dry fruit delicacies, and gift boxes.",
                "hours": "Mon-Sun: 9:00 AM - 10:00 PM",
                "welcome": "Welcome to Royal Sweets & Delights on Nexa! I can assist you with festive sweet boxes, prices, and quick orders.",
                "escalation": "Forwarding your request to our Royal Sweets specialist team. We will be right with you."
            },
            {
                "id": "glow-salon",
                "name": "Glow Salon",
                "slug": "salon",
                "business_type": "salon",
                "phone_number": "+917319770045",
                "description": "Boutique unisex luxury salon and day spa offering precision hair styling, skin therapies, and bridal packages.",
                "hours": "Mon-Sat: 10:00 AM - 8:00 PM, Sun: 11:00 AM - 6:00 PM",
                "welcome": "Welcome to Glow Salon on Nexa! I can help you explore hair & skin treatments and schedule your appointments.",
                "escalation": "Connecting you with the Glow Salon front desk team for your appointment consultation."
            },
            {
                "id": "dental-clinic",
                "name": "SmileCare Dental Clinic",
                "slug": "dental",
                "business_type": "dental",
                "phone_number": "+917319770046",
                "description": "Advanced family dentistry providing comprehensive dental checkups, cleaning, cosmetic veneers, and restorative care.",
                "hours": "Mon-Sat: 9:00 AM - 6:00 PM, Sun: Closed",
                "welcome": "Welcome to SmileCare Dental Clinic on Nexa. I can assist you with service info, clinic hours, and consultation appointments.",
                "escalation": "Connecting you with SmileCare clinical staff for immediate dental attention."
            }
        ]

        for m_cfg in merchants_config:
            m = await session.get(Merchant, m_cfg["id"])
            if not m:
                m = Merchant(
                    id=m_cfg["id"],
                    name=m_cfg["name"],
                    slug=m_cfg["slug"],
                    business_type=m_cfg["business_type"],
                    phone_number=m_cfg["phone_number"],
                    description=m_cfg["description"],
                    is_active=True
                )
                session.add(m)
            else:
                m.name = m_cfg["name"]
                m.slug = m_cfg["slug"]
                m.business_type = m_cfg["business_type"]
                m.description = m_cfg["description"]
                m.is_active = True

            # Admin User
            user_id = f"user-{m_cfg['slug']}-admin"
            u = await session.get(MerchantUser, user_id)
            if not u:
                u = MerchantUser(
                    id=user_id,
                    merchant_id=m_cfg["id"],
                    email=f"admin@{m_cfg['slug']}.com",
                    hashed_password=pwd_hash,
                    full_name=f"{m_cfg['name']} Manager",
                    role="admin",
                    is_active=True
                )
                session.add(u)

            # Settings
            stmt = select(MerchantSettings).where(MerchantSettings.merchant_id == m_cfg["id"])
            res = await session.execute(stmt)
            settings = res.scalars().first()
            if not settings:
                settings = MerchantSettings(
                    merchant_id=m_cfg["id"],
                    business_hours=m_cfg["hours"],
                    timezone="Asia/Kolkata",
                    notification_phone="9351489260",
                    notification_channel="whatsapp",
                    escalation_message=m_cfg["escalation"],
                    welcome_message=m_cfg["welcome"],
                    ai_provider="ollama",
                    ai_model="qwen3:1.7b"
                )
                session.add(settings)
            else:
                settings.business_hours = m_cfg["hours"]
                settings.notification_phone = "9351489260"
                settings.notification_channel = "whatsapp"
                settings.ai_provider = "ollama"
                settings.ai_model = "qwen3:1.7b"
                settings.welcome_message = m_cfg["welcome"]
                settings.escalation_message = m_cfg["escalation"]

        await session.flush()

        # ----------------------------------------------------
        # 2. KNOWLEDGE BASE & OFFERS
        # ----------------------------------------------------
        kb_data = [
            # Grocery
            ("kb-gro-1", "grocery-store", "FreshMart Store Policies & Hours", "policy",
             "FreshMart Grocery Operating Schedule: Monday to Saturday from 8:00 AM to 10:00 PM, Sunday from 9:00 AM to 8:00 PM. Same-day delivery is available for orders placed before 7:00 PM within a 5 km radius. Free delivery on orders above ₹500. Returns on unopened non-perishable goods are accepted within 7 days with receipt. Perishable items (dairy, fresh produce) can be replaced or refunded within 24 hours.", True),
            ("kb-gro-2", "grocery-store", "Grocery Super Saver 10% Off", "offer",
             "Grocery Super Saver: 10% off eligible grocery orders above ₹500! Valid on all fresh dairy, bakery, produce, and pantry staples. Maximum discount ₹100. Valid through December 31, 2026.", True),
            ("kb-gro-3", "grocery-store", "Expired Monsoon Cooking Oil Sale", "offer",
             "15% off refined cooking oil and ghee during the monsoon festival. Expired August 31, 2026.", False),

            # Sweets
            ("kb-swt-1", "sweets-shop", "Royal Sweets & Delights Information & Hours", "policy",
             "Royal Sweets & Delights Store Information: Open Monday to Sunday from 9:00 AM to 10:00 PM without weekly off. All sweets are handcrafted fresh daily using 100% pure desi ghee. Ingredients: Kaju Katli is made with premium Goan cashews and sugar; Gulab Jamun contains fresh khoya, saffron, and cardamom. No artificial food coloring or preservatives. Milk sweets shelf life is 3 days refrigerated; dry fruit sweets have 30 days room temperature shelf life.", True),
            ("kb-swt-2", "sweets-shop", "Festive Sweet Box Offer", "offer",
             "Festive Sweet Box Offer: 10% off selected sweet boxes! Special Diwali & Festive Gift Box featuring assorted Kaju Katli, Gulab Jamun, and Milk Cake available for ₹499. Valid through December 31, 2026.", True),
            ("kb-swt-3", "sweets-shop", "Expired Independence Day Special", "offer",
             "Tri-color burfi 20% discount offer. Expired August 16, 2026.", False),

            # Salon
            ("kb-sln-1", "glow-salon", "Glow Salon Operating Guidelines & Hours", "policy",
             "Glow Salon Operating Policies: Operating hours are Monday to Saturday from 10:00 AM to 8:00 PM, and Sunday from 11:00 AM to 6:00 PM. Please arrive 10 minutes prior to your scheduled slot. Rescheduling is permitted up to 2 hours in advance without penalty. Highest hygiene standards with sterilized instruments and single-use kits.", True),
            ("kb-sln-2", "glow-salon", "Hair Spa Introductory Offer", "offer",
             "Hair Spa Introductory Offer: Enjoy a 20% introductory discount on eligible Hair Spa appointments booked this month! Regular price ₹899, introductory offer ₹719. Valid through December 31, 2026.", True),

            # Dental
            ("kb-dnt-1", "dental-clinic", "SmileCare Dental Clinic Information & Guidelines", "policy",
             "SmileCare Dental Clinic Operating Guidelines: Operating hours are Monday to Saturday from 9:00 AM to 6:00 PM. The clinic is CLOSED on Sundays. Safety and clinical policy: The Nexa AI assistant handles administrative queries, price checks, and appointment scheduling only. It strictly does not provide medical or dental diagnoses, nor does it prescribe medication. For urgent symptoms such as severe facial swelling, acute trauma, or uncontrolled bleeding, please visit the emergency hospital immediately.", True),
            ("kb-dnt-2", "dental-clinic", "New Patient Consultation Special", "offer",
             "New Patient Special: ₹100 discount on your first comprehensive Dental Consultation! Regular consultation fee ₹500, now ₹400 for new patients. Valid through December 31, 2026.", True)
        ]

        for doc_id, m_id, title, d_type, content, is_pub in kb_data:
            doc = await session.get(KnowledgeDocument, doc_id)
            if not doc:
                doc = KnowledgeDocument(
                    id=doc_id,
                    merchant_id=m_id,
                    title=title,
                    doc_type=d_type,
                    content=content,
                    embedding_status="indexed",
                    is_published=is_pub
                )
                session.add(doc)
            else:
                doc.title = title
                doc.doc_type = d_type
                doc.content = content
                doc.is_published = is_pub

        await session.flush()

        # ----------------------------------------------------
        # 3. PRODUCTS & SERVICES
        # ----------------------------------------------------
        # A. Grocery Products (Section 4.A)
        grocery_catalog = [
            ("gprod-1", "Milk, 1 litre", "Dairy", "litre", Decimal("65.00"), 50, "Fresh pasteurized whole milk, 1 litre pouch."),
            ("gprod-2", "Bread, 400 g", "Bakery", "pack", Decimal("45.00"), 40, "Soft sliced sandwich bread, 400 g loaf."),
            ("gprod-3", "Eggs, 12 pack", "Dairy", "pack", Decimal("90.00"), 35, "Farm fresh white eggs, pack of 12."),
            ("gprod-4", "Basmati rice, 1 kg", "Pantry", "kg", Decimal("120.00"), 60, "Premium long-grain aged basmati rice, 1 kg pack."),
            ("gprod-5", "Apples, 1 kg", "Produce", "kg", Decimal("180.00"), 25, "Crisp sweet Royal Delicious apples, 1 kg."),
            ("gprod-6", "Cooking oil, 1 litre", "Pantry", "litre", Decimal("160.00"), 30, "Pure refined sunflower cooking oil, 1 litre bottle."),
            ("gprod-7", "Organic Almond Butter, 350 g", "Pantry", "jar", Decimal("450.00"), 0, "Stone-ground pure organic almond butter, currently out of stock.")
        ]

        for p_id, name, cat, unit, price, stock, desc in grocery_catalog:
            stmt = select(GroceryProduct).options(selectinload(GroceryProduct.inventory)).where(GroceryProduct.id == p_id)
            prod = (await session.execute(stmt)).scalars().first()
            if not prod:
                prod = GroceryProduct(
                    id=p_id,
                    merchant_id="grocery-store",
                    name=name,
                    category=cat,
                    unit=unit,
                    price=price,
                    description=desc,
                    is_active=True
                )
                session.add(prod)
                inv = GroceryInventory(
                    id=f"inv-{p_id}",
                    product=prod,
                    stock_quantity=stock,
                    low_stock_threshold=5
                )
                session.add(inv)
            else:
                prod.name = name
                prod.category = cat
                prod.unit = unit
                prod.price = price
                prod.description = desc
                prod.is_active = True
                if prod.inventory:
                    prod.inventory.stock_quantity = stock
                else:
                    inv = GroceryInventory(id=f"inv-{p_id}", product_id=prod.id, stock_quantity=stock)
                    session.add(inv)

        # B. Sweets Products (Section 4.B)
        sweets_catalog = [
            ("sprod-1", "Gulab Jamun, 500 g", "Milk Sweets", "500g", Decimal("220.00"), 30, False, "Soft melt-in-mouth khoya gulab jamuns steeped in fragrant saffron sugar syrup."),
            ("sprod-2", "Kaju Katli, 250 g", "Dry Fruit Sweets", "250g", Decimal("350.00"), 40, False, "Exquisite diamond-shaped cashew fudge crafted with Goan cashews."),
            ("sprod-3", "Motichoor Laddu, 500 g", "Traditional Sweets", "500g", Decimal("280.00"), 25, False, "Fine melt-in-mouth gram flour pearls enriched with pure desi ghee."),
            ("sprod-4", "Milk Cake, 500 g", "Milk Sweets", "500g", Decimal("300.00"), 20, False, "Traditional rich granular caramelized milk fudge with subtle cardamom."),
            ("sprod-5", "Assorted Sweet Box", "Gift Boxes", "box", Decimal("499.00"), 50, False, "Festive gift box containing Kaju Katli, Gulab Jamun, Milk Cake, and Laddus."),
            ("sprod-6", "Sugar-Free Anjeer Barfi, 250 g", "Dry Fruit Sweets", "250g", Decimal("420.00"), 0, True, "Naturally sweetened dry fig and nut barfi, currently out of stock.")
        ]

        for p_id, name, cat, unit, price, stock, is_sugar, desc in sweets_catalog:
            stmt = select(SweetsProduct).options(selectinload(SweetsProduct.inventory)).where(SweetsProduct.id == p_id)
            prod = (await session.execute(stmt)).scalars().first()
            if not prod:
                prod = SweetsProduct(
                    id=p_id,
                    merchant_id="sweets-shop",
                    name=name,
                    category=cat,
                    unit=unit,
                    price=price,
                    description=desc,
                    is_sugar_free=is_sugar,
                    is_active=True
                )
                session.add(prod)
                inv = SweetsInventory(
                    id=f"inv-{p_id}",
                    product=prod,
                    stock_quantity=stock
                )
                session.add(inv)
            else:
                prod.name = name
                prod.category = cat
                prod.unit = unit
                prod.price = price
                prod.description = desc
                prod.is_sugar_free = is_sugar
                prod.is_active = True
                if prod.inventory:
                    prod.inventory.stock_quantity = stock
                else:
                    inv = SweetsInventory(id=f"inv-{p_id}", product_id=prod.id, stock_quantity=stock)
                    session.add(inv)

        # C. Salon Services (Section 4.C)
        salon_catalog = [
            ("sln-srv-1", "Haircut & Styling", "Hair Care", 45, Decimal("399.00"), "Custom precision haircut, shampoo wash, and blow-dry styling."),
            ("sln-srv-2", "Hair Spa", "Hair Care", 60, Decimal("899.00"), "Deep nourishing scalp massage, hair mask, and aromatic steam treatment."),
            ("sln-srv-3", "Hydra Facial", "Skin & Facial", 60, Decimal("1499.00"), "Intense medical-grade hydrating facial with vortex pore extraction."),
            ("sln-srv-4", "Keratin Treatment", "Hair Care", 120, Decimal("2499.00"), "Smooth protein smoothing treatment eliminating frizz for up to 4 months."),
            ("sln-srv-5", "Balayage & Styling", "Hair Care", 180, Decimal("2999.00"), "Freehand dimensional hair painting followed by gloss toner and blowout."),
            ("sln-srv-6", "Bridal Makeup", "Bridal", 180, Decimal("4999.00"), "Complete high-definition bridal look with hairstyling, draping, and lashes.")
        ]

        for s_id, name, cat, dur, price, desc in salon_catalog:
            serv = await session.get(SalonService, s_id)
            if not serv:
                serv = SalonService(
                    id=s_id,
                    merchant_id="glow-salon",
                    name=name,
                    category=cat,
                    duration_minutes=dur,
                    price=price,
                    description=desc,
                    is_active=True
                )
                session.add(serv)
            else:
                serv.name = name
                serv.category = cat
                serv.duration_minutes = dur
                serv.price = price
                serv.description = desc
                serv.is_active = True

        # Salon Staff
        salon_staff_data = [
            ("staff-elena", "Elena Rostova", "Master Stylist", "Precision cuts, balayage, keratin smoothing, hair spa"),
            ("staff-priya", "Priya Sharma", "Senior Esthetician", "Hydra-facials, bridal makeup, skincare therapies")
        ]
        for st_id, name, role, spec in salon_staff_data:
            st = await session.get(SalonStaff, st_id)
            if not st:
                st = SalonStaff(
                    id=st_id,
                    merchant_id="glow-salon",
                    name=name,
                    role=role,
                    specialties=spec,
                    is_active=True
                )
                session.add(st)
            else:
                st.name = name
                st.role = role
                st.specialties = spec

        # D. Dental Clinic Services (Section 4.D)
        dental_catalog = [
            ("dnt-srv-1", "Dental Consultation", "Consultation", 30, Decimal("500.00"), "Comprehensive clinical exam, oral cancer screen, and treatment roadmap."),
            ("dnt-srv-2", "Teeth Cleaning", "Preventative", 45, Decimal("1200.00"), "Full-mouth ultrasonic scaling and enamel polishing to remove calculus."),
            ("dnt-srv-3", "Dental X-ray", "Diagnostic", 20, Decimal("800.00"), "High-resolution digital panoramic and periapical diagnostic radiography."),
            ("dnt-srv-4", "Tooth Filling", "Restorative", 45, Decimal("1500.00"), "Tooth-colored biocompatible composite resin restorative filling."),
            ("dnt-srv-5", "Follow-up Consultation", "Consultation", 20, Decimal("300.00"), "Post-operative clinical evaluation and bite adjustment check.")
        ]

        for s_id, name, cat, dur, fee, desc in dental_catalog:
            serv = await session.get(DentalService, s_id)
            if not serv:
                serv = DentalService(
                    id=s_id,
                    merchant_id="dental-clinic",
                    name=name,
                    category=cat,
                    duration_minutes=dur,
                    consultation_fee=fee,
                    description=desc,
                    is_active=True
                )
                session.add(serv)
            else:
                serv.name = name
                serv.category = cat
                serv.duration_minutes = dur
                serv.consultation_fee = fee
                serv.description = desc
                serv.is_active = True

        # Dental Staff
        dental_staff_data = [
            ("dentist-marcus", "Dr. Marcus Vance, DDS", "Senior Dental Surgeon", "DEN-98241", "Restorative crowns, fillings, oral exams"),
            ("dentist-sarah", "Dr. Sarah Lin, DMD", "Family & Pediatric Dentist", "DEN-87312", "Preventative hygiene, teeth cleaning, diagnostic X-rays")
        ]
        for st_id, name, title, lic, spec in dental_staff_data:
            st = await session.get(DentalStaff, st_id)
            if not st:
                st = DentalStaff(
                    id=st_id,
                    merchant_id="dental-clinic",
                    name=name,
                    title=title,
                    license_number=lic,
                    specialties=spec,
                    is_active=True
                )
                session.add(st)
            else:
                st.name = name
                st.title = title
                st.license_number = lic
                st.specialties = spec

        await session.flush()

        # ----------------------------------------------------
        # 4. DYNAMIC AVAILABILITY SLOTS (Next 30 Days)
        # ----------------------------------------------------
        # Clear existing unbooked slots so we avoid slot conflicts and always have live slots for today + 30 days
        await session.execute(delete(SalonAvailability).where(SalonAvailability.is_booked == False))
        await session.execute(delete(DentalAvailability).where(DentalAvailability.is_booked == False))

        today = date.today()
        # Salon: Mon-Sat 10am-8pm, Sun 11am-6pm
        salon_weekday_times = [(time(10, 0), time(11, 0)), (time(11, 30), time(12, 30)), (time(14, 0), time(15, 0)), (time(16, 0), time(17, 0)), (time(18, 0), time(19, 0))]
        salon_sunday_times = [(time(11, 0), time(12, 0)), (time(12, 30), time(13, 30)), (time(14, 0), time(15, 0)), (time(15, 30), time(16, 30)), (time(17, 0), time(18, 0))]

        # Dental: Mon-Sat 9am-6pm, Sun Closed
        dental_weekday_times = [(time(9, 0), time(10, 0)), (time(10, 30), time(11, 30)), (time(13, 0), time(14, 0)), (time(14, 30), time(15, 30)), (time(16, 0), time(17, 0))]

        for day_offset in range(30):
            slot_d = today + timedelta(days=day_offset)
            is_sunday = slot_d.weekday() == 6

            # Salon Slots (Open Every Day: Mon-Sat 10-8, Sun 11-6)
            s_times = salon_sunday_times if is_sunday else salon_weekday_times
            for st, et in s_times:
                for staff_id in ["staff-elena", "staff-priya"]:
                    session.add(SalonAvailability(
                        merchant_id="glow-salon",
                        staff_id=staff_id,
                        slot_date=slot_d,
                        start_time=st,
                        end_time=et,
                        is_booked=False
                    ))

            # Dental Slots (Closed on Sundays!)
            if not is_sunday:
                for st, et in dental_weekday_times:
                    for dentist_id in ["dentist-marcus", "dentist-sarah"]:
                        session.add(DentalAvailability(
                            merchant_id="dental-clinic",
                            dentist_id=dentist_id,
                            slot_date=slot_d,
                            start_time=st,
                            end_time=et,
                            is_booked=False
                        ))

        await session.flush()

        # ----------------------------------------------------
        # 5. TEST IDENTITIES & PROFILES (Section 3)
        # Customer: 7319770043, Human Assistant: 9351489260
        # ----------------------------------------------------
        test_customer_phones = ["+7319770043", "7319770043"]
        primary_cust_id = "cust-nexa-test"

        cust = await session.get(Customer, primary_cust_id)
        if not cust:
            cust = Customer(
                id=primary_cust_id,
                whatsapp_phone="+7319770043",
                name="Rajesh Kumar (Nexa Test)",
                email="test.customer@nexa-ai.local"
            )
            session.add(cust)
        else:
            cust.whatsapp_phone = "+7319770043"
            cust.name = "Rajesh Kumar (Nexa Test)"

        # Also support legacy test customer IDs so existing tests don't break
        legacy_cust1 = await session.get(Customer, "cust-alex")
        if not legacy_cust1:
            session.add(Customer(id="cust-alex", whatsapp_phone="+15551234567", name="Alex Morgan", email="alex@example.com"))
        legacy_cust2 = await session.get(Customer, "cust-priya")
        if not legacy_cust2:
            session.add(Customer(id="cust-priya", whatsapp_phone="+15559876543", name="Priya Sharma", email="priya@example.com"))

        await session.flush()

        # Establish customer profiles for primary test customer across all 4 merchants
        for m_id in ["grocery-store", "sweets-shop", "glow-salon", "dental-clinic"]:
            stmt = select(CustomerMerchantProfile).where(
                CustomerMerchantProfile.customer_id == primary_cust_id,
                CustomerMerchantProfile.merchant_id == m_id
            )
            prof = (await session.execute(stmt)).scalars().first()
            if not prof:
                session.add(CustomerMerchantProfile(
                    customer_id=primary_cust_id,
                    merchant_id=m_id,
                    preferred_name="Rajesh",
                    interaction_count=4,
                    opt_in_promotions=True,
                    notes=f"Test customer {test_customer_phones[0]} active in {m_id}"
                ))

        # Also ensure legacy profiles exist
        for cid, mid, name in [("cust-alex", "grocery-store", "Alex"), ("cust-alex", "glow-salon", "Alex"), ("cust-priya", "sweets-shop", "Priya"), ("cust-priya", "dental-clinic", "Priya")]:
            stmt = select(CustomerMerchantProfile).where(CustomerMerchantProfile.customer_id == cid, CustomerMerchantProfile.merchant_id == mid)
            if not (await session.execute(stmt)).scalars().first():
                session.add(CustomerMerchantProfile(customer_id=cid, merchant_id=mid, preferred_name=name, interaction_count=2, opt_in_promotions=True))

        await session.flush()

        # ----------------------------------------------------
        # 6. TRANSACTIONS, APPOINTMENTS & ESCALATIONS
        # ----------------------------------------------------
        # Sample Grocery Order
        gord = await session.get(GroceryOrder, "gord-nexa-1001")
        if not gord:
            gord = GroceryOrder(
                id="gord-nexa-1001",
                order_number="GRO-2026-1001",
                merchant_id="grocery-store",
                customer_id=primary_cust_id,
                status="confirmed",
                total_amount=Decimal("220.00"),
                delivery_address="Flat 402, Green Valley Apts, Test City",
                notes="Delivered to customer"
            )
            session.add(gord)
            session.add(GroceryOrderItem(order=gord, product_id="gprod-1", product_name="Milk, 1 litre", quantity=2, unit_price=Decimal("65.00"), total_price=Decimal("130.00")))
            session.add(GroceryOrderItem(order=gord, product_id="gprod-3", product_name="Eggs, 12 pack", quantity=1, unit_price=Decimal("90.00"), total_price=Decimal("90.00")))

        # Sample Sweets Order
        sord = await session.get(SweetsOrder, "sord-nexa-2001")
        if not sord:
            sord = SweetsOrder(
                id="sord-nexa-2001",
                order_number="SWT-2026-2001",
                merchant_id="sweets-shop",
                customer_id=primary_cust_id,
                status="confirmed",
                total_amount=Decimal("499.00"),
                order_type="pickup",
                gift_packaging=True,
                gift_message="Happy Celebrations from Nexa!"
            )
            session.add(sord)
            session.add(SweetsOrderItem(order=sord, product_id="sprod-5", product_name="Assorted Sweet Box", quantity=1, unit_price=Decimal("499.00"), total_price=Decimal("499.00")))

        # Sample Salon Appointment
        sappt = await session.get(SalonAppointment, "sappt-nexa-3001")
        tomorrow = today + timedelta(days=1)
        if not sappt:
            sappt = SalonAppointment(
                id="sappt-nexa-3001",
                booking_reference="SLN-2026-3001",
                merchant_id="glow-salon",
                customer_id=primary_cust_id,
                service_id="sln-srv-2",
                staff_id="staff-elena",
                appointment_date=tomorrow,
                start_time=time(11, 0),
                end_time=time(12, 0),
                status="confirmed",
                notes="Hair Spa introductory appointment"
            )
            session.add(sappt)

        # Sample Dental Appointment (ensure open day)
        dental_date = tomorrow if tomorrow.weekday() != 6 else tomorrow + timedelta(days=1)
        dappt = await session.get(DentalAppointment, "dappt-nexa-4001")
        if not dappt:
            dappt = DentalAppointment(
                id="dappt-nexa-4001",
                booking_reference="DNT-2026-4001",
                merchant_id="dental-clinic",
                customer_id=primary_cust_id,
                service_id="dnt-srv-1",
                dentist_id="dentist-marcus",
                appointment_date=dental_date,
                start_time=time(10, 30),
                end_time=time(11, 0),
                status="confirmed",
                chief_complaint="Routine initial dental checkup"
            )
            session.add(dappt)

        # Support Escalations (Section 10)
        esc1 = await session.get(SupportEscalation, "esc-nexa-dental-01")
        if not esc1:
            esc1 = SupportEscalation(
                id="esc-nexa-dental-01",
                merchant_id="dental-clinic",
                customer_id=primary_cust_id,
                reason="Customer requested consultation regarding acute dental discomfort. Safely triaged to human clinical assistant at 9351489260.",
                category="dental_clinical",
                status="pending",
                urgency="high",
                assigned_to="9351489260"
            )
            session.add(esc1)

        esc2 = await session.get(SupportEscalation, "esc-nexa-gro-02")
        if not esc2:
            esc2 = SupportEscalation(
                id="esc-nexa-gro-02",
                merchant_id="grocery-store",
                customer_id=primary_cust_id,
                reason="Customer inquired about delivery schedule change for order GRO-2026-1001.",
                category="general",
                status="resolved",
                urgency="medium",
                assigned_to="9351489260",
                resolution_notes="Delivery window confirmed with customer."
            )
            session.add(esc2)

        # Notification Jobs
        stmt = select(NotificationJob).where(NotificationJob.id == "notif-job-1001")
        if not (await session.execute(stmt)).scalars().first():
            job = NotificationJob(
                id="notif-job-1001",
                merchant_id="grocery-store",
                customer_id=primary_cust_id,
                event_type="order.created",
                status="sent",
                payload_json={"order_number": "GRO-2026-1001", "total_amount": 220.00, "customer_phone": "7319770043"}
            )
            session.add(job)
            session.add(NotificationEvent(
                id="notif-evt-1001",
                job_id="notif-job-1001",
                merchant_id="grocery-store",
                event_type="order.created",
                status="delivered",
                provider_response={"simulation": True, "recipient": "7319770043"}
            ))

        await session.commit()
        print("Idempotent seed completed successfully!")
        print("4 Merchants, Products (INR), Services (INR), Dynamic 30-Day Slots, Test Customer 7319770043 & Assistant 9351489260 ready.")

if __name__ == "__main__":
    asyncio.run(seed_data())
