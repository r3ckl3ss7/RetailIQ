from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.products import Product as ProductModel
from models.user import Business
from schemas.products import ProductCreate, ProductUpdate


async def _get_business_for_user(
	db: AsyncSession,
	business_id: int,
	current_user_id: int,
) -> Business:
	result = await db.execute(
		select(Business).where(Business.id == business_id)
	)
	business = result.scalar_one_or_none()
	if not business:
		raise HTTPException(status_code=404, detail="Business does not exist")
	if current_user_id != business.user_id:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Access Forbidden | Business does not belong to logged in user!",
		)
	return business


async def list_products(
	db: AsyncSession,
	business_id: int,
	current_user_id: int,
) -> list[ProductModel]:
	await _get_business_for_user(db, business_id, current_user_id)
	result = await db.execute(
		select(ProductModel).where(ProductModel.business_id == business_id)
	)
	return result.scalars().all()


async def search_products(
	db: AsyncSession,
	business_id: int,
	sku: str | None,
	barcode: str | None,
	name: str | None,
	current_user_id: int,
) -> list[ProductModel]:
	await _get_business_for_user(db, business_id, current_user_id)
	query = select(ProductModel).where(ProductModel.business_id == business_id)
	filters = []
	if sku:
		filters.append(ProductModel.sku == sku)
	if barcode:
		filters.append(ProductModel.barcode == barcode)
	if name:
		filters.append(ProductModel.name.ilike(f"%{name}%"))
	if filters:
		query = query.where(or_(*filters))
	result = await db.execute(query)
	return result.scalars().all()


async def get_product_by_id(
	db: AsyncSession,
	product_id: int,
	current_user_id: int,
) -> ProductModel:
	result = await db.execute(
		select(ProductModel).where(ProductModel.id == product_id)
	)
	product = result.scalar_one_or_none()
	if not product:
		raise HTTPException(status_code=404, detail="Product not found")
	await _get_business_for_user(db, product.business_id, current_user_id)
	return product


async def create_product(
	db: AsyncSession,
	payload: ProductCreate,
	current_user_id: int,
) -> ProductModel:
	try:
		business = await _get_business_for_user(
			db,
			payload.business_id,
			current_user_id,
		)

		product = ProductModel(
			name=payload.name,
			business_id=business.id,
			original_price=payload.original_price,
			selling_price=payload.selling_price,
			stock=payload.stock,
			category=payload.category,
			sku=payload.sku,
			barcode=payload.barcode,
			description=payload.description,
		)
		db.add(product)
		await db.commit()
		await db.refresh(product)
		return product
	except HTTPException:
		await db.rollback()
		raise
	except Exception as exc:
		await db.rollback()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		) from exc


async def update_product(
	db: AsyncSession,
	product_id: int,
	payload: ProductUpdate,
	current_user_id: int,
) -> ProductModel:
	result = await db.execute(
		select(ProductModel).where(ProductModel.id == product_id)
	)
	product = result.scalar_one_or_none()
	if not product:
		raise HTTPException(status_code=404, detail="Product not found")
	await _get_business_for_user(db, product.business_id, current_user_id)
	update_data = payload.model_dump(exclude_unset=True)
	for key, value in update_data.items():
		setattr(product, key, value)
	await db.commit()
	await db.refresh(product)
	return product


async def delete_product(
	db: AsyncSession,
	product_id: int,
	current_user_id: int,
) -> None:
	result = await db.execute(
		select(ProductModel).where(ProductModel.id == product_id)
	)
	product = result.scalar_one_or_none()
	if not product:
		raise HTTPException(status_code=404, detail="Product not found")
	await _get_business_for_user(db, product.business_id, current_user_id)
	await db.delete(product)
	await db.commit()
