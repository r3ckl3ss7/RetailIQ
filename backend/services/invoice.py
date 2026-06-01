from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.invoice import Customer, Invoice, InvoiceItem, InvoiceSource, InvoiceStatus
from models.products import Product
from models.user import Business
from schemas.invoice import InvoiceCreatePayload, InvoiceMetadata, InvoiceUpdate


MONEY_QUANT = Decimal("0.01")


def _to_decimal(value: Decimal | int | float | str | None) -> Decimal | None:
	if value is None:
		return None
	if isinstance(value, Decimal):
		return value
	return Decimal(str(value))


def _quantize_money(value: Decimal) -> Decimal:
	return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


async def _resolve_customer(
	db: AsyncSession,
	business_id: int,
	payload: InvoiceCreatePayload,
) -> int | None:
	if payload.customer_id:
		return payload.customer_id

	if not payload.customer:
		return None

	if not payload.customer.phone_number:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Customer phone number is required to create a new customer",
		)

	filters = []
	if payload.customer.phone_number:
		filters.append(Customer.phone_number == payload.customer.phone_number)
	if payload.customer.email:
		filters.append(Customer.email == payload.customer.email)

	result = await db.execute(
		select(Customer)
		.where(Customer.business_id == business_id)
		.where(or_(*filters))
	)
	existing = result.scalar_one_or_none()
	if existing:
		return existing.id

	customer = Customer(
		business_id=business_id,
		name=payload.customer.name,
		phone_number=payload.customer.phone_number,
		email=payload.customer.email,
	)
	db.add(customer)
	await db.flush()
	return customer.id


async def _resolve_product(
	db: AsyncSession,
	business_id: int,
	product_id: int | None,
	sku: str | None,
	barcode: str | None,
) -> Product:
	if product_id is not None:
		result = await db.execute(
			select(Product).where(
				Product.id == product_id,
				Product.business_id == business_id,
			)
		)
		product = result.scalar_one_or_none()
		if not product:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"Invalid product_id {product_id}",
			)
		return product

	if not sku and not barcode:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Each item must include product_id, sku, or barcode",
		)

	query = select(Product).where(Product.business_id == business_id)
	filters = []
	if sku:
		filters.append(Product.sku == sku)
	if barcode:
		filters.append(Product.barcode == barcode)
	result = await db.execute(query.where(or_(*filters)))
	product = result.scalar_one_or_none()
	if not product:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="No matching product found for sku/barcode",
		)
	return product


def _calculate_totals(
	payload: InvoiceCreatePayload,
	items: list[tuple[Product, int]],
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
	subtotal = Decimal("0")
	for product, quantity in items:
		subtotal += _to_decimal(product.selling_price) * Decimal(quantity)
	subtotal = _quantize_money(subtotal)

	tax = _quantize_money(_to_decimal(payload.tax or 0) or Decimal("0"))
	discount = _quantize_money(_to_decimal(payload.discount or 0) or Decimal("0"))
	total = _quantize_money(subtotal + tax - discount)

	if payload.subtotal is not None and _quantize_money(_to_decimal(payload.subtotal)) != subtotal:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Subtotal mismatch",
		)
	if payload.total is not None and _quantize_money(_to_decimal(payload.total)) != total:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Total mismatch",
		)

	return subtotal, tax, discount, total


async def create_invoice(
	db: AsyncSession,
	payload: InvoiceCreatePayload,
	current_user_id: int,
) -> tuple[Invoice, int]:
	try:
		business_result = await db.execute(
			select(Business).where(Business.id == payload.business_id)
		)
		business = business_result.scalar_one_or_none()
		if not business:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Business does not exist",
			)
		if business.user_id != current_user_id:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="Access Forbidden | Business does not belong to logged in user!",
			)

		if not payload.items:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Invoice must include at least one item",
			)

		customer_id = await _resolve_customer(db, payload.business_id, payload)

		resolved_items: list[tuple[Product, int]] = []
		for item in payload.items:
			product = await _resolve_product(
				db,
				payload.business_id,
				item.product_id,
				item.sku,
				item.barcode,
			)
			resolved_items.append((product, item.quantity))

		subtotal, tax, discount, total = _calculate_totals(payload, resolved_items)
		model_status = InvoiceStatus[payload.status.value]
		model_source = InvoiceSource[payload.source.value]

		invoice = Invoice(
			business_id=payload.business_id,
			customer_id=customer_id,
			payment_id=payload.payment_id,
			status=model_status,
			source=model_source,
			subtotal=subtotal,
			tax=tax,
			discount=discount,
			total=total,
			notes=payload.notes,
		)
		db.add(invoice)
		await db.flush()

		for product, quantity in resolved_items:
			invoice_item = InvoiceItem(
				invoice_id=invoice.id,
				product_id=product.id,
				quantity=quantity,
			)
			db.add(invoice_item)

			if model_status == InvoiceStatus.PAID:
				if product.stock < quantity:
					raise HTTPException(
						status_code=status.HTTP_400_BAD_REQUEST,
						detail=f"Insufficient stock for product {product.id}",
					)
				product.stock -= quantity

		await db.commit()
		await db.refresh(invoice)

		status_code = (
			status.HTTP_202_ACCEPTED
			if model_status == InvoiceStatus.PENDING
			else status.HTTP_201_CREATED
		)
		return invoice, status_code
	except HTTPException:
		await db.rollback()
		raise
	except Exception as exc:
		await db.rollback()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		) from exc


async def get_invoice_by_id(
	db: AsyncSession,
	invoice_id: int,
) -> Invoice:
	try:
		result = await db.execute(
			select(Invoice)
			.options(selectinload(Invoice.items))
			.where(Invoice.id == invoice_id)
		)
		invoice = result.scalar_one_or_none()
		if not invoice:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Invalid invoice id",
			)
		return invoice
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		) from exc


async def get_invoice_metadata(
	db: AsyncSession,
	business_id: int,
	current_user_id: int,
) -> InvoiceMetadata:
	business_result = await db.execute(
		select(Business).where(Business.id == business_id)
	)
	business = business_result.scalar_one_or_none()
	if not business:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Business does not exist",
		)
	if current_user_id != business.user_id:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Access Forbidden | Business does not belong to logged in user!",
		)

	invoice_result = await db.execute(
		select(Invoice)
		.options(selectinload(Invoice.customer))
		.where(Invoice.business_id == business_id)
		.order_by(Invoice.created_at.desc())
	)
	invoice = invoice_result.scalar_one_or_none()
	if not invoice:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="No invoices found for this business",
		)

	customer_name = invoice.customer.name if invoice.customer else "Walk-in"
	return InvoiceMetadata(
		customer_name=customer_name,
		status=invoice.status,
		tax=invoice.tax or 0,
		discount=invoice.discount or 0,
		total=invoice.total or 0,
	)


async def update_invoice(
	db: AsyncSession,
	invoice_id: int,
	payload: InvoiceUpdate,
	current_user_id: int,
) -> Invoice:
	invoice_result = await db.execute(
		select(Invoice).where(Invoice.id == invoice_id)
	)
	invoice = invoice_result.scalar_one_or_none()
	if not invoice:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Invalid invoice id",
		)

	business_result = await db.execute(
		select(Business).where(Business.id == invoice.business_id)
	)
	business = business_result.scalar_one_or_none()
	if not business or business.user_id != current_user_id:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Access Forbidden | Business does not belong to logged in user!",
		)

	update_data = payload.model_dump(exclude_unset=True)
	allowed_fields = {"status", "payment_id", "notes"}
	invalid_fields = set(update_data.keys()) - allowed_fields
	if invalid_fields:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Only status, payment_id, and notes can be updated",
		)

	for key, value in update_data.items():
		setattr(invoice, key, value)

	await db.commit()
	await db.refresh(invoice)
	return invoice
