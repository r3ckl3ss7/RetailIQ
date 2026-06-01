from fastapi import APIRouter, Depends, status
from middlewares.auth import current_user
from schemas.products import ProductCreate, ProductOut, ProductUpdate
from db.database import get_db
from sqlalchemy.orm import Session
from services.products import (
    create_product as create_product_service,
    delete_product as delete_product_service,
    get_product_by_id as get_product_service,
    list_products as list_products_service,
    search_products as search_products_service,
    update_product as update_product_service,
)
router=APIRouter(
    prefix='/products',
    tags=['products']
)
@router.get('/', response_model=list[ProductOut])
async def get_all_prods(business_id: int, current_user_id: int = Depends(current_user), db: Session = Depends(get_db)):
    return list_products_service(db, business_id, current_user_id)

@router.get('/search', response_model=list[ProductOut])
def search_products(
    business_id: int,
    sku: str | None = None,
    barcode: str | None = None,
    name: str | None = None,
    current_user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    return search_products_service(
        db,
        business_id,
        sku,
        barcode,
        name,
        current_user_id,
    )


@router.get('/{product_id}', response_model=ProductOut)
def get_product(product_id: int, current_user_id: int = Depends(current_user), db: Session = Depends(get_db)):
    return get_product_service(db, product_id, current_user_id)

@router.post('/', response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate,
                         current_user_id: int = Depends(current_user),
                         db: Session = Depends(get_db)) -> ProductOut:
    return create_product_service(db, payload, current_user_id)


@router.patch('/{product_id}', response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    return update_product_service(db, product_id, payload, current_user_id)


@router.delete('/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    current_user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    return delete_product_service(db, product_id, current_user_id)

    
    