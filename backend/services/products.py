from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.products import Product as ProductModel
from models.user import Business
from schemas.products import ProductCreate, ProductUpdate


def _get_business_for_user(
	db: Session,
	business_id: int,
	current_user_id: int,
) -> Business:
	business = db.query(Business).filter(Business.id == business_id).first()
	if not business:
		raise HTTPException(status_code=404, detail="Business does not exist")
	if current_user_id != business.user_id:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Access Forbidden | Business does not belong to logged in user!",
		)
	return business


def list_products(
	db: Session,
	business_id: int,
	current_user_id: int,
) -> list[ProductModel]:
	_get_business_for_user(db, business_id, current_user_id)
	return (
		db.query(ProductModel)
		.filter(ProductModel.business_id == business_id)
		.all()
	)


def search_products(
	db: Session,
	business_id: int,
	sku: str | None,
	barcode: str | None,
	name: str | None,
	current_user_id: int,
) -> list[ProductModel]:
	_get_business_for_user(db, business_id, current_user_id)
	query = db.query(ProductModel).filter(ProductModel.business_id == business_id)
	filters = []
	if sku:
		filters.append(ProductModel.sku == sku)
	if barcode:
		filters.append(ProductModel.barcode == barcode)
	if name:
		filters.append(ProductModel.name.ilike(f"%{name}%"))
	if filters:
		query = query.filter(or_(*filters))
	return query.all()


def get_product_by_id(
	db: Session,
	product_id: int,
	current_user_id: int,
) -> ProductModel:
	product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
	if not product:
		raise HTTPException(status_code=404, detail="Product not found")
	_get_business_for_user(db, product.business_id, current_user_id)
	return product


def create_product(
	db: Session,
	payload: ProductCreate,
	current_user_id: int,
) -> ProductModel:
	try:
		business = _get_business_for_user(db, payload.business_id, current_user_id)

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
		db.commit()
		db.refresh(product)
		return product
	except HTTPException:
		db.rollback()
		raise
	except Exception as exc:
		db.rollback()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		) from exc


def update_product(
	db: Session,
	product_id: int,
	payload: ProductUpdate,
	current_user_id: int,
) -> ProductModel:
	product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
	if not product:
		raise HTTPException(status_code=404, detail="Product not found")
	_get_business_for_user(db, product.business_id, current_user_id)
	update_data = payload.model_dump(exclude_unset=True)
	for key, value in update_data.items():
		setattr(product, key, value)
	db.commit()
	db.refresh(product)
	return product


def delete_product(
	db: Session,
	product_id: int,
	current_user_id: int,
) -> None:
	product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
	if not product:
		raise HTTPException(status_code=404, detail="Product not found")
	_get_business_for_user(db, product.business_id, current_user_id)
	db.delete(product)
	db.commit()
