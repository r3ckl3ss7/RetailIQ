from fastapi import Depends, APIRouter, Response, status, HTTPException
from middlewares.auth import current_user
from db.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.invoice import (
    InvoiceCreatePayload,
    InvoiceMetadata,
    InvoiceResponse,
    InvoiceUpdate,
    CustomerOut,
    InvoiceStatus,
    PaginatedInvoices,
)
from services.invoice import (
    create_invoice,
    get_invoice_by_id,
    get_invoice_metadata,
    update_invoice as update_invoice_service,
    list_invoices,
    list_customers as list_customers_service,
    count_invoices as count_invoices_service,
)
from exceptions.business import BusinessException
from exceptions.invoice import InvoiceException
from exceptions.database import DatabaseUnexpectedException

router = APIRouter(
    prefix="/invoice",
    tags=["invoice"]
)


@router.get('/customers', response_model=list[CustomerOut])
async def list_customers(
    business_id: int,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[CustomerOut]:
    try:
        return await list_customers_service(db, business_id, current_user_id)
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )


@router.get('/list', response_model=PaginatedInvoices)
async def list_invoices_route(
    business_id: int,
    page: int | None = None,
    limit: int | None = None,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        items = await list_invoices(db, business_id, current_user_id, page, limit)
        total = await count_invoices_service(db, business_id)
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




@router.get('/{invoice_id}', response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, current_user_id:int=Depends(current_user),db: AsyncSession = Depends(get_async_db))->InvoiceResponse:
    try:
        return await get_invoice_by_id(db, invoice_id, current_user_id)
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )
    except InvoiceException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )
    except DatabaseUnexpectedException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        )




@router.get('/',response_model=InvoiceMetadata)
async def invoice_metadata(business_id:int, current_user_id:int=Depends(current_user),db:AsyncSession=Depends(get_async_db))->InvoiceMetadata:
    try:
        return await get_invoice_metadata(db, business_id, current_user_id)
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )
    except InvoiceException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )


@router.post('/', response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice_route(
    payload: InvoiceCreatePayload,
    response: Response,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
) -> InvoiceResponse:
    try:
        invoice = await create_invoice(db, payload, current_user_id)
        if invoice.status == InvoiceStatus.PENDING:
            response.status_code = status.HTTP_202_ACCEPTED
        return invoice
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )
    except InvoiceException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )
    except DatabaseUnexpectedException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        )


@router.patch('/{invoice_id}', response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    payload: InvoiceUpdate,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
) -> InvoiceResponse:
    try:
        return await update_invoice_service(db, invoice_id, payload, current_user_id)
    except BusinessException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.error_message,
        )
    except InvoiceException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )
    except DatabaseUnexpectedException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        )
