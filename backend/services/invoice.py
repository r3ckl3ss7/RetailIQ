import json
import os
import re
from decimal import Decimal, ROUND_HALF_UP

import httpx

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.invoice import Customer, Invoice, InvoiceItem, InvoiceSource, InvoiceStatus
from models.products import Product
from models.user import Business
from schemas.invoice import (
	InvoiceCreatePayload,
	InvoiceMetadata,
	InvoiceOCRPayload,
	InvoiceUpdate,
)


MONEY_QUANT = Decimal("0.01")
OCR_INVOKE_URL = os.getenv("PADDLE_OCR_URL")
if OCR_INVOKE_URL:
	OCR_INVOKE_URL = OCR_INVOKE_URL.strip('"\'')
OCR_CONFIDENCE_THRESHOLD = 0.6


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
	existing = result.scalars().first()
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
	product = result.scalars().first()
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
		status_str = payload.status.value if hasattr(payload.status, "value") else payload.status
		source_str = payload.source.value if hasattr(payload.source, "value") else payload.source
		model_status = InvoiceStatus[status_str]
		model_source = InvoiceSource[source_str]

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
		result = await db.execute(
			select(Invoice)
			.options(
				selectinload(Invoice.items).selectinload(InvoiceItem.product),
				selectinload(Invoice.customer)
			)
			.where(Invoice.id == invoice.id)
		)
		invoice = result.scalar_one()

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
	current_user_id: int,
) -> Invoice:
	try:
		result = await db.execute(
			select(Invoice)
			.options(
				selectinload(Invoice.items).selectinload(InvoiceItem.product),
				selectinload(Invoice.customer)
			)
			.where(Invoice.id == invoice_id)
		)
		invoice = result.scalar_one_or_none()
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
	try:
		invoice_result = await db.execute(
			select(Invoice)
			.options(
				selectinload(Invoice.items).selectinload(InvoiceItem.product),
				selectinload(Invoice.customer)
			)
			.where(Invoice.id == invoice_id)
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

		old_status = invoice.status
		new_status = old_status
		if "status" in update_data and update_data["status"] is not None:
			status_val = update_data["status"].value if hasattr(update_data["status"], "value") else update_data["status"]
			new_status = InvoiceStatus[status_val]

		if old_status != new_status:
			stock_was_deducted_before = (old_status == InvoiceStatus.PAID) or (
				old_status == InvoiceStatus.PENDING and invoice.source == InvoiceSource.OCR
			)
			stock_should_be_deducted_now = (new_status == InvoiceStatus.PAID)

			if stock_should_be_deducted_now and not stock_was_deducted_before:
				for item in invoice.items:
					if item.product:
						if item.product.stock < item.quantity:
							raise HTTPException(
								status_code=status.HTTP_400_BAD_REQUEST,
								detail=f"Insufficient stock for product '{item.product.name}' (ID: {item.product.id})",
							)
						item.product.stock -= item.quantity
			elif not stock_should_be_deducted_now and stock_was_deducted_before:
				for item in invoice.items:
					if item.product:
						item.product.stock += item.quantity

		for key, value in update_data.items():
			if key == "status":
				value = new_status
			setattr(invoice, key, value)

		await db.commit()
		result = await db.execute(
			select(Invoice)
			.options(
				selectinload(Invoice.items).selectinload(InvoiceItem.product),
				selectinload(Invoice.customer)
			)
			.where(Invoice.id == invoice_id)
		)
		invoice = result.scalar_one()
		return invoice
	except HTTPException:
		await db.rollback()
		raise
	except Exception as exc:
		await db.rollback()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		) from exc


def _parse_money(value: str | None) -> Decimal | None:
	if not value:
		return None
	try:
		return Decimal(value.replace(",", ""))
	except Exception:
		return None


def _extract_ocr_lines(response_json: dict) -> list[tuple[str, float | None]]:
	data = response_json.get("data")
	if data is None:
		data = response_json.get("result") or response_json.get("results") or response_json.get("output")

	lines: list[tuple[str, float | None]] = []
	if isinstance(data, dict):
		if isinstance(data.get("data"), list):
			data = data.get("data")
		elif isinstance(data.get("text"), list):
			for text in data.get("text"):
				if isinstance(text, str) and text.strip():
					lines.append((text.strip(), None))
			return lines

	if isinstance(data, list):
		for entry in data:
			if isinstance(entry, dict):
				text_detections = entry.get("text_detections")
				if isinstance(text_detections, list):
					for detection in text_detections:
						if isinstance(detection, dict):
							text = detection.get("text")
							confidence = detection.get("confidence")
							if text and str(text).strip():
								lines.append((str(text).strip(), float(confidence) if confidence is not None else None))
					continue

				text = (
					entry.get("text")
					or entry.get("label")
					or entry.get("word")
					or entry.get("value")
				)
				confidence = entry.get("confidence") or entry.get("score") or entry.get("prob")
				if text and str(text).strip():
					lines.append((str(text).strip(), float(confidence) if confidence is not None else None))
			elif isinstance(entry, str) and entry.strip():
				lines.append((entry.strip(), None))

	if not lines and isinstance(response_json.get("text"), list):
		for text in response_json.get("text"):
			if isinstance(text, str) and text.strip():
				lines.append((text.strip(), None))

	return lines


def _extract_amount_from_line(line: str) -> Decimal | None:
	matches = re.findall(r"\d+(?:\.\d{1,2})?", line)
	if not matches:
		return None
	return _parse_money(matches[-1])


def _parse_ocr_items(lines: list[str]) -> list[dict]:
	items: list[dict] = []
	for line in lines:
		lowered = line.lower()
		if any(keyword in lowered for keyword in ["total", "subtotal", "sub total", "tax", "gst", "vat", "discount"]):
			continue

		numbers = re.findall(r"\d+(?:\.\d{1,2})?", line)
		if len(numbers) < 2:
			continue

		qty_value = int(float(numbers[0])) if float(numbers[0]) >= 1 else 1
		amount_value = _parse_money(numbers[-1])
		if not amount_value:
			continue

		name = re.sub(r"\d+(?:\.\d{1,2})?", " ", line)
		name = re.sub(r"\s+", " ", name.replace("x", " ")).strip(" -")
		items.append({
			"name": name or "Item",
			"quantity": qty_value,
			"amount": amount_value,
		})
	return items


async def _match_product_by_name(db: AsyncSession, business_id: int, name: str) -> Product | None:
	clean_name = name.strip()
	if len(clean_name) < 2:
		return None

	result = await db.execute(
		select(Product).where(
			Product.business_id == business_id,
			Product.name.ilike(f"%{clean_name}%"),
		)
	)
	return result.scalars().first()


async def create_invoice_ocr(
	payload: InvoiceOCRPayload,
	current_user_id: int,
	db: AsyncSession,
):
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

		api_key = os.getenv("PADDLE_OCR_KEY")
		if not api_key:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail="PADDLE_OCR_KEY is not configured",
			)

		if payload.image_base64 and len(payload.image_base64) >= 180_000:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Image too large for direct upload; use image_url",
			)

		image_url = payload.image_url
		if payload.image_base64:
			image_url = f"data:image/png;base64,{payload.image_base64}"

		headers = {
			"Authorization": f"Bearer {api_key}",
			"Accept": "application/json",
		}
		ocr_payload = {
			"input": [
				{
					"type": "image_url",
					"url": image_url,
				}
			]
		}

		async with httpx.AsyncClient() as client:
			response = await client.post(OCR_INVOKE_URL, headers=headers, json=ocr_payload, timeout=30)
		if not response.is_success:
			raise HTTPException(
				status_code=status.HTTP_502_BAD_GATEWAY,
				detail=f"OCR request failed: {response.status_code}",
			)

		ocr_json = response.json()
		ocr_lines = _extract_ocr_lines(ocr_json)
		if not ocr_lines:
			raise HTTPException(
				status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
				detail="OCR returned no text",
			)

		confidences = [conf for _, conf in ocr_lines if conf is not None]
		if confidences:
			avg_conf = sum(confidences) / len(confidences)
			threshold = payload.confidence_threshold or OCR_CONFIDENCE_THRESHOLD
			if avg_conf < threshold:
				raise HTTPException(
					status_code=status.HTTP_400_BAD_REQUEST,
					detail="OCR confidence below threshold",
				)
		else:
			avg_conf = None

		text_lines = [line for line, _ in ocr_lines]
		items = _parse_ocr_items(text_lines)

		tax = Decimal("0")
		discount = Decimal("0")
		total = None
		for line in text_lines:
			lowered = line.lower()
			if "tax" in lowered or "gst" in lowered or "vat" in lowered:
				line_amount = _extract_amount_from_line(line)
				if line_amount is not None:
					tax = line_amount
			if "discount" in lowered:
				line_amount = _extract_amount_from_line(line)
				if line_amount is not None:
					discount = line_amount
			if "total" in lowered and "subtotal" not in lowered:
				line_amount = _extract_amount_from_line(line)
				if line_amount is not None:
					total = line_amount

		subtotal = sum((item["amount"] for item in items), Decimal("0")) if items else Decimal("0")
		subtotal = _quantize_money(subtotal)
		tax = _quantize_money(_to_decimal(tax) or Decimal("0"))
		discount = _quantize_money(_to_decimal(discount) or Decimal("0"))
		if total is None:
			total = subtotal + tax - discount
		total = _quantize_money(_to_decimal(total) or Decimal("0"))

		if not items:
			items = [{"name": "OCR Item", "quantity": 1, "amount": total or Decimal("0")}]

		invoice = Invoice(
			business_id=payload.business_id,
			customer_id=None,
			payment_id=None,
			status=InvoiceStatus.PENDING,
			source=InvoiceSource.OCR,
			subtotal=subtotal,
			tax=tax,
			discount=discount,
			total=total,
		)
		db.add(invoice)
		await db.flush()

		unknown_items: list[dict] = []
		for item in items:
			product = await _match_product_by_name(db, payload.business_id, item["name"])
			invoice_item = InvoiceItem(
				invoice_id=invoice.id,
				product_id=product.id if product else None,
				quantity=item["quantity"],
			)
			db.add(invoice_item)

			if not product:
				unknown_items.append(item)
			elif payload.deduct_from_stock:
				if product.stock < item["quantity"]:
					raise HTTPException(
						status_code=status.HTTP_400_BAD_REQUEST,
						detail=f"Insufficient stock for product {product.id}",
					)
				product.stock -= item["quantity"]

		invoice.notes = json.dumps(
			{
				"ocr_confidence": avg_conf,
				"ocr_text": "\n".join(text_lines),
				"unknown_items": unknown_items,
			},
			ensure_ascii=True,
			default=str,
		)

		await db.commit()
		result = await db.execute(
			select(Invoice)
			.options(
				selectinload(Invoice.items).selectinload(InvoiceItem.product),
				selectinload(Invoice.customer)
			)
			.where(Invoice.id == invoice.id)
		)
		invoice = result.scalar_one()
		return invoice
	except HTTPException:
		await db.rollback()
		raise
	except Exception as exc:
		await db.rollback()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		) from exc


async def list_invoices(
	db: AsyncSession,
	business_id: int,
	current_user_id: int,
) -> list[Invoice]:
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

	result = await db.execute(
		select(Invoice)
		.options(
			selectinload(Invoice.items).selectinload(InvoiceItem.product),
			selectinload(Invoice.customer)
		)
		.where(Invoice.business_id == business_id)
		.order_by(Invoice.created_at.desc())
	)
	return list(result.scalars().all())