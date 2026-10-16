from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.shared import KnowledgeDocument, Merchant
from backend.app.services.document_processor import DocumentProcessor
from backend.app.api.deps import get_current_merchant
from backend.app.guardrails.audit_logger import AuditLogger

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

class FAQCreateRequest(BaseModel):
    title: str
    doc_type: str = "faq"  # 'faq', 'policy', 'offer'
    content: str

class PublishUpdateRequest(BaseModel):
    is_published: bool

@router.get("/documents")
async def list_documents(
    doc_type: Optional[str] = None,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """List knowledge documents for the active merchant."""
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.merchant_id == merchant.id)
    if doc_type:
        stmt = stmt.where(KnowledgeDocument.doc_type == doc_type)

    res = await db.execute(stmt)
    docs = res.scalars().all()

    return [
        {
            "id": d.id,
            "title": d.title,
            "doc_type": d.doc_type,
            "file_name": d.file_name,
            "content": d.content,
            "extracted_text": d.extracted_text,
            "embedding_status": d.embedding_status,
            "is_published": d.is_published,
            "created_at": d.created_at.isoformat()
        }
        for d in docs
    ]

@router.post("/faq")
async def create_faq(
    req: FAQCreateRequest,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Add a structured FAQ, policy, or offer note."""
    doc = KnowledgeDocument(
        merchant_id=merchant.id,
        title=req.title,
        doc_type=req.doc_type,
        content=req.content,
        embedding_status="indexed",
        is_published=True
    )
    db.add(doc)
    await db.commit()
    return {"id": doc.id, "title": doc.title, "status": "indexed"}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Upload and extract knowledge from PDF, TXT, MD, CSV, or JSON."""
    file_bytes = await file.read()
    file_name = file.filename or "uploaded_file"

    res = DocumentProcessor.process_file_content(file_name, file_bytes)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("error", "Failed to process document")
        )

    doc = KnowledgeDocument(
        merchant_id=merchant.id,
        title=title or file_name,
        doc_type=file_name.split(".")[-1].lower(),
        file_name=file_name,
        content=res.get("extracted_text", ""),
        extracted_text=res.get("extracted_text", ""),
        metadata_json=res.get("metadata", {}),
        embedding_status="indexed",
        is_published=True
    )
    db.add(doc)
    await db.commit()

    await AuditLogger.log_event(
        action="KNOWLEDGE_DOCUMENT_UPLOADED",
        resource_type="knowledge_document",
        merchant_id=merchant.id,
        resource_id=doc.id,
        details={"file_name": file_name, "size": len(file_bytes)}
    )

    return {
        "id": doc.id,
        "title": doc.title,
        "file_name": file_name,
        "extracted_text_preview": doc.content[:200],
        "status": "indexed"
    }

@router.put("/documents/{doc_id}/publish")
async def toggle_publish_status(
    doc_id: str,
    req: PublishUpdateRequest,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Publish or unpublish knowledge document."""
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.merchant_id == merchant.id, KnowledgeDocument.id == doc_id)
    doc = (await db.execute(stmt)).scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.is_published = req.is_published
    await db.commit()
    return {"id": doc.id, "is_published": doc.is_published}

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Remove a knowledge document."""
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.merchant_id == merchant.id, KnowledgeDocument.id == doc_id)
    doc = (await db.execute(stmt)).scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.delete(doc)
    await db.commit()
    return {"id": doc_id, "status": "deleted"}
