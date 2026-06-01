from fastapi import Depends, APIRouter, HTTPException, Response, status
from sqlalchemy import select, text
from middlewares.auth import current_user
from db.database import get_db
from sqlalchemy.orm import Session
from models.invoice import Invoice, InvoiceItem
from models.user import Business
from schemas.invoice import InvoiceCreatePayload, InvoiceMetadata, InvoiceResponse, InvoiceUpdate
from services.invoice import create_invoice

router = APIRouter(
    prefix="/invoice",
    tags=["invoice"]
)



# get invoice details
@router.get('/{invoice_id}', response_model=InvoiceResponse)
def get_invoice(invoice_id: int, current_user_id:int=Depends(current_user),db: Session = Depends(get_db))->InvoiceResponse:
    try:
        inv=db.query(Invoice).filter(Invoice.id==invoice_id).first()
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid invoice id"
            )
        return inv
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )




# get invoice metadata(dashboard)
@router.get('/',response_model=InvoiceMetadata)
def invoice_metadata(business_id:int, current_user_id:int=Depends(current_user),db:Session=Depends(get_db))->InvoiceMetadata:
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business does not exist"
        )
    if current_user_id != business.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Forbidden | Business does not belong to logged in user!"
        )

    invoice = (
        db.query(Invoice)
        .filter(Invoice.business_id == business_id)
        .order_by(Invoice.created_at.desc())
        .first()
    )
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No invoices found for this business"
        )

    customer_name = invoice.customer.name if invoice.customer else "Walk-in"
    return InvoiceMetadata(
        customer_name=customer_name,
        status=invoice.status,
        tax=invoice.tax or 0,
        discount=invoice.discount or 0,
        total=invoice.total or 0,
    )


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
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invoice id",
        )

    business = db.query(Business).filter(Business.id == invoice.business_id).first()
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

    db.commit()
    db.refresh(invoice)
    return invoice
