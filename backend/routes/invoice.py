from fastapi import Depends, APIRouter, Response, status, HTTPException
from middlewares.auth import current_user
from db.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.invoice import Customer
from models.user import Business
from schemas.invoice import (
    InvoiceCreatePayload,
    InvoiceMetadata,
    InvoiceOCRPayload,
    InvoiceResponse,
    InvoiceUpdate,
    CustomerOut,
)
from services.invoice import (
    create_invoice,
    create_invoice_ocr as create_invoice_ocr_service,
    get_invoice_by_id,
    get_invoice_metadata,
    update_invoice as update_invoice_service,
    list_invoices,
)

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
    business_result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = business_result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if business.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    result = await db.execute(
        select(Customer)
        .where(Customer.business_id == business_id)
        .order_by(Customer.name.asc())
    )
    return list(result.scalars().all())


@router.get('/list', response_model=list[InvoiceResponse])
async def list_invoices_route(
    business_id: int,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[InvoiceResponse]:
    return await list_invoices(db, business_id, current_user_id)




# get invoice details
@router.get('/{invoice_id}', response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, current_user_id:int=Depends(current_user),db: AsyncSession = Depends(get_async_db))->InvoiceResponse:
    return await get_invoice_by_id(db, invoice_id, current_user_id)




# get invoice metadata(dashboard)
@router.get('/',response_model=InvoiceMetadata)
async def invoice_metadata(business_id:int, current_user_id:int=Depends(current_user),db:AsyncSession=Depends(get_async_db))->InvoiceMetadata:
    return await get_invoice_metadata(db, business_id, current_user_id)


# post invoice
@router.post('/', response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice_route(
    payload: InvoiceCreatePayload,
    response: Response,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
) -> InvoiceResponse:
    invoice, status_code = await create_invoice(db, payload, current_user_id)
    if status_code == status.HTTP_202_ACCEPTED:
        response.status_code = status.HTTP_202_ACCEPTED
    return invoice

# post-ocr
@router.post('/ocr/',response_model=InvoiceResponse)
async def create_invoice_ocr(
    payload: InvoiceOCRPayload,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db)
)->InvoiceResponse:
    return await create_invoice_ocr_service(payload, current_user_id, db)

# patch invoice(status,etc)
@router.patch('/{invoice_id}', response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    payload: InvoiceUpdate,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
) -> InvoiceResponse:
    return await update_invoice_service(db, invoice_id, payload, current_user_id)
