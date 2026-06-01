from fastapi import Depends, APIRouter, Response, status
from middlewares.auth import current_user
from db.database import get_db
from sqlalchemy.orm import Session
from schemas.invoice import InvoiceCreatePayload, InvoiceMetadata, InvoiceResponse, InvoiceUpdate
from services.invoice import (
    create_invoice,
    get_invoice_by_id,
    get_invoice_metadata,
    update_invoice as update_invoice_service,
)

router = APIRouter(
    prefix="/invoice",
    tags=["invoice"]
)



# get invoice details
@router.get('/{invoice_id}', response_model=InvoiceResponse)
def get_invoice(invoice_id: int, current_user_id:int=Depends(current_user),db: Session = Depends(get_db))->InvoiceResponse:
    return get_invoice_by_id(db, invoice_id)




# get invoice metadata(dashboard)
@router.get('/',response_model=InvoiceMetadata)
def invoice_metadata(business_id:int, current_user_id:int=Depends(current_user),db:Session=Depends(get_db))->InvoiceMetadata:
    return get_invoice_metadata(db, business_id, current_user_id)


# post invoice
@router.post('/', response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice_route(
    payload: InvoiceCreatePayload,
    response: Response,
    current_user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
) -> InvoiceResponse:
    invoice, status_code = create_invoice(db, payload, current_user_id)
    if status_code == status.HTTP_202_ACCEPTED:
        response.status_code = status.HTTP_202_ACCEPTED
    return invoice

# patch invoice(status,etc)
@router.patch('/{invoice_id}', response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    payload: InvoiceUpdate,
    current_user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
) -> InvoiceResponse:
    return update_invoice_service(db, invoice_id, payload, current_user_id)
