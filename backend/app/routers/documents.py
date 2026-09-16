from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import DocumentResponse
from app.models import Transaction
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/documents/{transaction_id}", response_model=List[DocumentResponse])
def get_documents(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """Get all documents for a transaction."""
    
    transaction = db.query(Transaction).filter(
        Transaction.transaction_id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    document_service = DocumentService(db)
    documents = document_service.get_documents(transaction_id)
    
    return [
        DocumentResponse(
            document_id=doc.document_id,
            document_type=doc.document_type,
            url=doc.url,
            status=doc.status,
            created_at=doc.created_at
        )
        for doc in documents
    ]
