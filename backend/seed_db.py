"""
Seed script for RetailIQ.

Run:  python seed_db.py
Always clears the database and re-seeds from scratch.

Creates:
  - 1 user  (lunarberserk066 / lunarberserk066@example.com / 12345678)
  - 2 businesses for that user
  - 30 products  (15 per business)
  - 25 customers (split across businesses)
  - 40 invoices with 1-4 line-items each
  - Matching payments for PAID invoices
  - Dates spread over the last ~90 days for useful analytics
"""

import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, text

from db.database import AsyncSessionLocal
from models.invoice import (
    Customer,
    CustomerAddress,
    Invoice,
    InvoiceItem,
    InvoiceSource,
    InvoiceStatus,
    Payment,
    PaymentMethod,
)
from models.products import Product
from models.user import Business, User
from services.auth import hash_password

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
RANDOM_SEED = 42

PRODUCT_COUNT = 30          # 15 per business
CUSTOMER_COUNT = 25
INVOICE_COUNT = 40          # each gets 1-4 items
DATE_SPREAD_DAYS = 90       # invoices span this many days back from now

# ---------------------------------------------------------------------------
# Realistic data pools
# ---------------------------------------------------------------------------
PRODUCT_CATALOG = [
    # (name, category, price_range_low, price_range_high)
    ("Tata Salt 1kg", "Grocery", 22, 28),
    ("Aashirvaad Atta 5kg", "Grocery", 260, 310),
    ("Fortune Sunflower Oil 1L", "Grocery", 140, 175),
    ("Maggi 2-Minute Noodles Pack", "Grocery", 12, 15),
    ("Parle-G Gold Biscuit 1kg", "Grocery", 85, 100),
    ("Amul Butter 500g", "Grocery", 260, 290),
    ("India Gate Basmati Rice 5kg", "Grocery", 420, 520),
    ("MTR Sambar Powder 200g", "Grocery", 70, 95),
    ("Tata Tea Premium 500g", "Grocery", 210, 260),
    ("Nescafe Classic 200g", "Beverage", 380, 450),
    ("Coca-Cola 2L", "Beverage", 85, 95),
    ("Tropicana Orange Juice 1L", "Beverage", 90, 120),
    ("Bisleri Water 5L", "Beverage", 45, 55),
    ("Red Bull 250ml", "Beverage", 115, 130),
    ("Paper Boat Aam Panna 200ml", "Beverage", 25, 35),
    ("Dove Soap 100g", "Personal Care", 48, 62),
    ("Head & Shoulders Shampoo 340ml", "Personal Care", 310, 380),
    ("Colgate MaxFresh 150g", "Personal Care", 90, 115),
    ("Dettol Handwash 200ml", "Personal Care", 65, 82),
    ("Nivea Body Lotion 400ml", "Personal Care", 290, 360),
    ("Surf Excel Matic 2kg", "Household", 380, 450),
    ("Harpic Toilet Cleaner 500ml", "Household", 85, 110),
    ("Vim Dishwash Bar 500g", "Household", 35, 48),
    ("Godrej Air Freshener 240ml", "Household", 130, 165),
    ("Scotch-Brite Scrub Pad 3-Pack", "Household", 55, 72),
    ("Cadbury Dairy Milk Silk 150g", "Snacks", 155, 180),
    ("Lays Classic Salted 52g", "Snacks", 18, 22),
    ("Haldiram Aloo Bhujia 400g", "Snacks", 110, 140),
    ("KitKat 4-Finger Bar", "Snacks", 38, 45),
    ("Too Yumm Multigrain Chips 60g", "Snacks", 25, 32),
]

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun",
    "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Ananya", "Diya", "Meera", "Priya", "Kavya",
    "Riya", "Shruti", "Nisha", "Pooja", "Sneha",
    "Rahul", "Vikram", "Suresh", "Mohan", "Deepak",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Reddy", "Nair",
    "Iyer", "Kumar", "Singh", "Gupta", "Rao",
    "Joshi", "Menon", "Das", "Pillai", "Bhat",
]

CITIES = [
    ("Bengaluru", "Karnataka", "560"),
    ("Mumbai", "Maharashtra", "400"),
    ("Hyderabad", "Telangana", "500"),
    ("Chennai", "Tamil Nadu", "600"),
    ("Pune", "Maharashtra", "411"),
]

STREET_NAMES = [
    "MG Road", "Brigade Road", "Church Street", "Residency Road",
    "Indiranagar 1st Main", "Koramangala 5th Block", "Jayanagar 4th T Block",
    "Whitefield Main Road", "HSR Layout Sector 2", "Bannerghatta Road",
    "Rajaji Nagar 3rd Block", "Malleswaram 8th Cross", "JP Nagar 6th Phase",
    "BTM Layout 2nd Stage", "Electronic City Phase 1",
]

INVOICE_NOTES = [
    "Regular purchase",
    "Bulk order — discount applied",
    "Monthly restocking",
    "Walk-in customer",
    "Phone order",
    "Festival season order",
    "Repeat customer — loyalty discount",
    None,
    None,
    None,
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _rand_decimal(low: float, high: float) -> Decimal:
    return Decimal(str(round(random.uniform(low, high), 2)))


def _rand_phone() -> str:
    """Generate a realistic 10-digit Indian mobile number."""
    prefix = random.choice(["98", "97", "96", "95", "94", "93", "91", "90",
                            "88", "87", "86", "85", "84", "83", "82", "81",
                            "70", "72", "73", "74", "75", "76", "77", "78", "79"])
    suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + suffix


def _rand_datetime_in_range(start: datetime, end: datetime) -> datetime:
    """Return a random datetime between start and end."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


# ---------------------------------------------------------------------------
# DB reset
# ---------------------------------------------------------------------------
async def _reset_tables():
    """Delete all rows in dependency order."""
    async with AsyncSessionLocal() as session:
        await session.execute(delete(InvoiceItem))
        await session.execute(delete(Invoice))
        await session.execute(delete(Payment))
        await session.execute(delete(CustomerAddress))
        await session.execute(delete(Customer))
        await session.execute(delete(Product))
        await session.execute(delete(Business))
        await session.execute(delete(User))
        await session.commit()
    print("✓ Database cleared")


# ---------------------------------------------------------------------------
# Main seeding logic
# ---------------------------------------------------------------------------
async def seed():
    random.seed(RANDOM_SEED)
    now = datetime.now(timezone.utc)
    date_start = now - timedelta(days=DATE_SPREAD_DAYS)

    # 1. Clear everything
    await _reset_tables()

    async with AsyncSessionLocal() as session:

        # ------------------------------------------------------------------
        # 2. Create one user
        # ------------------------------------------------------------------
        user = User(
            name="lunarberserk066",
            email="lunarberserk066@example.com",
            password=hash_password("12345678"),
        )
        session.add(user)
        await session.flush()
        print(f"✓ User created  →  {user.email} / 12345678")

        # ------------------------------------------------------------------
        # 3. Create two businesses for the user
        # ------------------------------------------------------------------
        biz_a = Business(
            user_id=user.id,
            name="Lunar Mart",
            gst_number="29AABCL1234F1Z5",
            phone="9876543210",
            email="lunarmart@example.com",
            address="42 MG Road, Indiranagar",
            city="Bengaluru",
            state="Karnataka",
            country="India",
            postal_code="560038",
            invoice_prefix="LM",
            currency="INR",
            timezone="Asia/Kolkata",
        )
        biz_b = Business(
            user_id=user.id,
            name="Berserk Bazaar",
            gst_number="29AABCB5678G2Z8",
            phone="9123456780",
            email="berserkbazaar@example.com",
            address="17 Brigade Road, Ashok Nagar",
            city="Bengaluru",
            state="Karnataka",
            country="India",
            postal_code="560025",
            invoice_prefix="BB",
            currency="INR",
            timezone="Asia/Kolkata",
        )
        session.add_all([biz_a, biz_b])
        await session.flush()
        businesses = [biz_a, biz_b]
        print(f"✓ Businesses created  →  '{biz_a.name}' (id={biz_a.id}), '{biz_b.name}' (id={biz_b.id})")

        # ------------------------------------------------------------------
        # 4. Create products — 15 per business
        # ------------------------------------------------------------------
        products: list[Product] = []
        products_by_biz: dict[int, list[Product]] = {b.id: [] for b in businesses}

        shuffled_catalog = list(PRODUCT_CATALOG)
        random.shuffle(shuffled_catalog)

        for idx, (p_name, p_cat, p_low, p_high) in enumerate(shuffled_catalog):
            biz = businesses[idx % 2]   # alternate between the two businesses
            original = _rand_decimal(p_low, p_high)
            margin = _rand_decimal(2, max(5, float(original) * 0.15))
            selling = original + margin

            # Stagger creation dates
            created = _rand_datetime_in_range(
                date_start,
                date_start + timedelta(days=15),   # products created early
            )

            product = Product(
                name=p_name,
                business_id=biz.id,
                original_price=original,
                selling_price=selling,
                stock=random.randint(5, 200),
                sku=f"SKU-{biz.invoice_prefix}-{idx + 1:03d}",
                barcode=f"890{random.randint(1000000000, 9999999999)}",
                category=p_cat,
                description=f"{p_cat} item — {p_name}",
                created_at=created,
                updated_at=created,
            )
            session.add(product)
            products.append(product)
            products_by_biz[biz.id].append(product)

        await session.flush()
        print(f"✓ Products created  →  {len(products)} items")

        # ------------------------------------------------------------------
        # 5. Create customers — split across both businesses
        # ------------------------------------------------------------------
        customers: list[Customer] = []
        customers_by_biz: dict[int, list[Customer]] = {b.id: [] for b in businesses}

        used_names: set[str] = set()
        for idx in range(CUSTOMER_COUNT):
            # Unique name
            while True:
                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                full_name = f"{fname} {lname}"
                if full_name not in used_names:
                    used_names.add(full_name)
                    break

            biz = businesses[idx % 2] if idx < 20 else random.choice(businesses)
            city_name, state_name, postal_prefix = random.choice(CITIES)

            created = _rand_datetime_in_range(
                date_start,
                date_start + timedelta(days=20),
            )

            customer = Customer(
                business_id=biz.id,
                name=full_name,
                phone_number=_rand_phone(),
                phone_number_country_code="+91",
                email=f"{fname.lower()}.{lname.lower()}{idx}@example.com",
                created_at=created,
            )
            session.add(customer)
            await session.flush()
            customers.append(customer)
            customers_by_biz[biz.id].append(customer)

            # Address
            address = CustomerAddress(
                customer_id=customer.id,
                line1=f"{random.randint(1, 500)}, {random.choice(STREET_NAMES)}",
                line2=f"Near {random.choice(['Metro Station', 'Bus Stop', 'Park', 'Temple', 'Market'])}",
                city=city_name,
                state=state_name,
                country="India",
                postal_code=f"{postal_prefix}{random.randint(1, 99):03d}",
                created_at=created,
            )
            session.add(address)

        await session.flush()
        print(f"✓ Customers created  →  {len(customers)} customers with addresses")

        # ------------------------------------------------------------------
        # 6. Create invoices, payments, and line-items
        # ------------------------------------------------------------------
        # Weight statuses so PAID dominates (makes analytics useful)
        status_weights = [
            (InvoiceStatus.PAID, 55),
            (InvoiceStatus.PENDING, 20),
            (InvoiceStatus.DRAFT, 10),
            (InvoiceStatus.CANCELLED, 10),
            (InvoiceStatus.REFUNDED, 5),
        ]
        status_pool = [s for s, w in status_weights for _ in range(w)]

        invoice_count = 0
        item_count = 0
        payment_count = 0

        for _ in range(INVOICE_COUNT):
            biz = random.choice(businesses)
            biz_products = products_by_biz[biz.id]
            biz_customers = customers_by_biz[biz.id]

            if not biz_products or not biz_customers:
                continue

            inv_status = random.choice(status_pool)
            inv_source = random.choice(list(InvoiceSource))
            inv_date = _rand_datetime_in_range(
                date_start + timedelta(days=20),  # after products & customers exist
                now,
            )

            # Pick 1-4 distinct products for line-items
            num_items = random.randint(1, min(4, len(biz_products)))
            chosen_products = random.sample(biz_products, num_items)

            subtotal = Decimal("0.00")
            pending_items = []

            for prod in chosen_products:
                qty = random.randint(1, 6)
                line_total = prod.selling_price * qty
                subtotal += line_total
                pending_items.append((prod, qty))

            tax = (subtotal * _rand_decimal(0, 18) / Decimal("100")).quantize(Decimal("0.01"))
            discount = (subtotal * _rand_decimal(0, 8) / Decimal("100")).quantize(Decimal("0.01"))
            total = subtotal + tax - discount
            if total < Decimal("0.01"):
                total = Decimal("0.01")

            # Payment — only for PAID invoices
            payment_id = None
            if inv_status == InvoiceStatus.PAID:
                paid_at = inv_date + timedelta(
                    minutes=random.randint(0, 60),
                )
                payment = Payment(
                    method=random.choice(list(PaymentMethod)),
                    status="PAID",
                    amount=total,
                    paid_at=paid_at,
                    created_at=inv_date,
                )
                session.add(payment)
                await session.flush()
                payment_id = payment.id
                payment_count += 1

            customer = random.choice(biz_customers)

            invoice = Invoice(
                business_id=biz.id,
                customer_id=customer.id,
                payment_id=payment_id,
                status=inv_status,
                source=inv_source,
                subtotal=subtotal,
                tax=tax,
                discount=discount,
                total=total,
                notes=random.choice(INVOICE_NOTES),
                created_at=inv_date,
                updated_at=inv_date,
            )
            session.add(invoice)
            await session.flush()
            invoice_count += 1

            for prod, qty in pending_items:
                inv_item = InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=prod.id,
                    quantity=qty,
                )
                session.add(inv_item)
                item_count += 1

        await session.flush()
        print(f"✓ Invoices created   →  {invoice_count} invoices, {item_count} line-items, {payment_count} payments")

        # ------------------------------------------------------------------
        # 7. Sync Postgres sequences to avoid PK conflicts on future inserts
        # ------------------------------------------------------------------
        for table in [
            "users",
            "businesses",
            "products",
            "customer",
            "customer_address",
            "payment",
            "invoice",
            "invoice_items",
        ]:
            try:
                await session.execute(
                    text(
                        f"SELECT setval('{table}_id_seq', "
                        f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
                    )
                )
            except Exception:
                pass

        await session.commit()
        print("\n✅ Seeding complete!")
        print(f"   Login: lunarberserk066@example.com / 12345678")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(seed())
