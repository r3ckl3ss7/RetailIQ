import asyncio
import random
import sys
from decimal import Decimal
from typing import Iterable

from sqlalchemy import delete

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


USER_COUNT_MIN = 3
USER_COUNT_MAX = 4
BUSINESS_COUNT_MIN = 2
BUSINESS_COUNT_MAX = 5
ROWS_PER_TABLE = 100
RANDOM_SEED = 42


def _rand_email(prefix: str, idx: int) -> str:
    return f"{prefix}{idx}@example.com"


def _rand_phone(idx: int) -> str:
    return f"9{idx:09d}"[-10:]


def _rand_decimal(min_value: float, max_value: float) -> Decimal:
    value = random.uniform(min_value, max_value)
    return Decimal(str(round(value, 2)))


def _pick_random(items: Iterable):
    return random.choice(list(items))


async def _reset_tables():
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


async def seed(reset: bool = False):
    random.seed(RANDOM_SEED)

    if reset:
        await _reset_tables()

    async with AsyncSessionLocal() as session:
        # Users and businesses
        user_count = random.randint(USER_COUNT_MIN, USER_COUNT_MAX)
        users: list[User] = []
        businesses: list[Business] = []

        for idx in range(1, user_count + 1):
            user = User(
                name=f"User {idx}",
                email=_rand_email("user", idx),
                password=hash_password("Password@123"),
            )
            session.add(user)
            await session.flush()
            users.append(user)

            business_count = random.randint(BUSINESS_COUNT_MIN, BUSINESS_COUNT_MAX)
            for b_idx in range(1, business_count + 1):
                business = Business(
                    user_id=user.id,
                    name=f"Business {idx}-{b_idx}",
                    phone=_rand_phone(idx * 100 + b_idx),
                    email=_rand_email("biz", idx * 10 + b_idx),
                    address=f"{b_idx} Market Street",
                    city="Bengaluru",
                    state="Karnataka",
                    country="India",
                    postal_code=f"5600{idx:02d}",
                    invoice_prefix=f"B{idx}{b_idx}",
                )
                session.add(business)
                await session.flush()
                businesses.append(business)

        # Products
        products: list[Product] = []
        for idx in range(1, ROWS_PER_TABLE + 1):
            business = _pick_random(businesses)
            original_price = _rand_decimal(20, 200)
            selling_price = original_price - _rand_decimal(0, 10)
            product = Product(
                name=f"Product {idx}",
                business_id=business.id,
                original_price=original_price,
                selling_price=max(selling_price, Decimal("1.00")),
                stock=random.randint(0, 200),
                sku=f"SKU{idx:05d}",
                barcode=f"BC{idx:08d}",
                category=random.choice(["Grocery", "Beverage", "Personal", "Other"]),
                description="Seeded product",
            )
            session.add(product)
            products.append(product)

        await session.flush()

        # Customers and addresses
        customers: list[Customer] = []
        for idx in range(1, ROWS_PER_TABLE + 1):
            business = _pick_random(businesses)
            customer = Customer(
                business_id=business.id,
                name=f"Customer {idx}",
                phone_number=_rand_phone(1000 + idx),
                email=_rand_email("customer", idx),
            )
            session.add(customer)
            await session.flush()
            customers.append(customer)

            address = CustomerAddress(
                customer_id=customer.id,
                line1=f"{idx} Main Road",
                city="Bengaluru",
                state="Karnataka",
                country="India",
                postal_code=f"5601{idx % 100:02d}",
            )
            session.add(address)

        # Invoices, payments, and items
        products_by_business: dict[int, list[Product]] = {}
        for product in products:
            products_by_business.setdefault(product.business_id, []).append(product)

        for idx in range(1, ROWS_PER_TABLE + 1):
            business = _pick_random(businesses)
            business_products = products_by_business.get(business.id) or products
            product = _pick_random(business_products)
            quantity = random.randint(1, 5)

            subtotal = product.selling_price * quantity
            tax = _rand_decimal(0, 10)
            discount = _rand_decimal(0, 5)
            total = subtotal + tax - discount

            status = _pick_random(list(InvoiceStatus))
            source = _pick_random(list(InvoiceSource))

            payment = Payment(
                method=_pick_random(list(PaymentMethod)),
                status="PAID" if status == InvoiceStatus.PAID else "PENDING",
                amount=total,
            )
            session.add(payment)
            await session.flush()

            invoice = Invoice(
                business_id=business.id,
                customer_id=_pick_random(customers).id,
                payment_id=payment.id if status == InvoiceStatus.PAID else None,
                status=status,
                source=source,
                subtotal=subtotal,
                tax=tax,
                discount=discount,
                total=total,
                notes="Seeded invoice",
            )
            session.add(invoice)
            await session.flush()

            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=product.id,
                quantity=quantity,
            )
            session.add(invoice_item)

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed(reset="--reset" in sys.argv))
