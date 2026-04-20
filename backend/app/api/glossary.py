from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import GlossaryCategory, GlossaryTerm, User
from app.schemas.glossary import GlossaryCategoryOut, GlossaryGroupedOut, GlossaryTermOut

router = APIRouter(prefix="/glossary", tags=["glossary"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[GlossaryGroupedOut])
def list_terms(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[GlossaryGroupedOut]:
    categories = list(
        db.scalars(select(GlossaryCategory).options(selectinload(GlossaryCategory.terms)).order_by(GlossaryCategory.sort_order))
    )
    return [
        GlossaryGroupedOut(
            category=GlossaryCategoryOut.model_validate(category),
            terms=[GlossaryTermOut.model_validate(term) for term in sorted(category.terms, key=lambda item: item.term_ko)],
        )
        for category in categories
    ]


@router.get("/categories", response_model=list[GlossaryCategoryOut])
def list_categories(db: Session = Depends(get_db)) -> list[GlossaryCategory]:
    return list(db.scalars(select(GlossaryCategory).order_by(GlossaryCategory.sort_order)))


@router.get("/search", response_model=list[GlossaryTermOut])
def search_terms(q: str, db: Session = Depends(get_db)) -> list[GlossaryTerm]:
    query = f"%{q}%"
    return list(
        db.scalars(
            select(GlossaryTerm)
            .options(selectinload(GlossaryTerm.category))
            .where(or_(GlossaryTerm.term_ko.ilike(query), GlossaryTerm.term_en.ilike(query)))
            .order_by(GlossaryTerm.term_ko)
        )
    )


@router.get("/{term_id}", response_model=GlossaryTermOut)
def get_term(term_id: int, db: Session = Depends(get_db)) -> GlossaryTerm:
    term = db.scalar(select(GlossaryTerm).options(selectinload(GlossaryTerm.category)).where(GlossaryTerm.id == term_id))
    if term is None:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    return term

