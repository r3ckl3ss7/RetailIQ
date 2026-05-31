from fastapi import APIRouter, HTTPException, Depends, status
from models.user import Business
from middlewares.auth import current_user
from schemas.products import ProductCreate, ProductOut, ProductUpdate
from models.products import Product as ProductModel
from db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import or_
router=APIRouter(
    prefix='/products',
    tags=['products']
)
from datetime import datetime

@router.get('/', response_model=list[ProductOut])
async def get_all_prods(business_id: int, current_user_id: int = Depends(current_user), db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail='Business does not exist')
    if current_user_id != business.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access Forbidden | Business does not belong to logged in user!'
        )
    products = db.query(ProductModel).filter(ProductModel.business_id == business_id).all()
    return products

@router.get('/search', response_model=list[ProductOut])
def search_products(
    business_id: int,
    sku: str | None = None,
    barcode: str | None = None,
    name: str | None = None,
    current_user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail='Business does not exist')
    if current_user_id != business.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access Forbidden | Business does not belong to logged in user!'
        )
    query = db.query(ProductModel).filter(ProductModel.business_id == business_id)
    filters = []
    if sku:
        filters.append(ProductModel.sku == sku)
    if barcode:
        filters.append(ProductModel.barcode == barcode)
    if name:
        filters.append(ProductModel.name.ilike(f'%{name}%'))
    if filters:
        query = query.filter(or_(*filters))
    return query.all()


@router.get('/{product_id}', response_model=ProductOut)
def get_product(product_id: int, current_user_id: int = Depends(current_user), db: Session = Depends(get_db)):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    business = db.query(Business).filter(Business.id == product.business_id).first()
    if not business or current_user_id != business.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access Forbidden | Business does not belong to logged in user!'
        )
    return product

@router.post('/', response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate,
                         current_user_id: int = Depends(current_user),
                         db: Session = Depends(get_db)) -> ProductOut:
    try:
        business_id = payload.business_id
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise HTTPException(
                status_code=404,
                detail="Business does not exist"
            )
        if current_user_id != business.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Forbidden | Business does not belong to logged in user!"
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
        db.commit()
        db.refresh(product)
        return product
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch('/{product_id}', response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    business = db.query(Business).filter(Business.id == product.business_id).first()
    if not business or current_user_id != business.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access Forbidden | Business does not belong to logged in user!'
        )
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete('/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    current_user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    business = db.query(Business).filter(Business.id == product.business_id).first()
    if not business or current_user_id != business.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access Forbidden | Business does not belong to logged in user!'
        )
    db.delete(product)
    db.commit()
    return None

    
    