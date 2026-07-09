from fastapi import APIRouter, Depends, status, HTTPException
from middlewares.auth import current_user
from schemas.products import ProductCreate, ProductOut, ProductUpdate, PaginatedProducts
from db.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.products import (
    create_product as create_product_service,
    delete_product as delete_product_service,
    get_product_by_id as get_product_service,
    list_products as list_products_service,
    search_products as search_products_service,
    update_product as update_product_service,
    count_products as count_products_service,
)
from exceptions.business import BusinessException
from exceptions.pruduct import ProductException
from exceptions.database import DatabaseIntegrityException, DatabaseUnexpectedException
router=APIRouter(
    prefix='/products',
    tags=['products']
)
@router.get('/', response_model=PaginatedProducts)
async def get_all_prods(
    business_id: int,
    page: int | None = None,
    limit: int | None = None,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        items = await list_products_service(db, business_id, current_user_id, page, limit)
        total = await count_products_service(db, business_id)
        return {
            "items": items,
            "total": total,
            "page": page if page is not None else 1,
            "limit": limit if limit is not None else total
        }
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )
    

@router.get('/search', response_model=list[ProductOut])
async def search_products(
    business_id: int,
    sku: str | None = None,
    barcode: str | None = None,
    name: str | None = None,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await search_products_service(
            db,
            business_id,
            sku,
            barcode,
            name,
            current_user_id,
        )
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )


@router.get('/{product_id}', response_model=ProductOut)
async def get_product(product_id: int, current_user_id: int = Depends(current_user), db: AsyncSession = Depends(get_async_db)):
    try:
        return await get_product_service(db, product_id, current_user_id)
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )
    except ProductException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )

@router.post('/', response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate,
                         current_user_id: int = Depends(current_user),
                         db: AsyncSession = Depends(get_async_db)) -> ProductOut:
    try:
        return await create_product_service(db, payload, current_user_id)
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )
    except DatabaseIntegrityException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )
    except DatabaseUnexpectedException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        )


@router.patch('/{product_id}', response_model=ProductOut)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await update_product_service(db, product_id, payload, current_user_id)
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )
    except ProductException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )
    except DatabaseIntegrityException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )
    except DatabaseUnexpectedException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        )


@router.delete('/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await delete_product_service(db, product_id, current_user_id)
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )
    except ProductException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )
    except DatabaseUnexpectedException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        )

    
    