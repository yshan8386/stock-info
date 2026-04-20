from pydantic import BaseModel


class GlossaryCategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    icon: str | None = None
    sort_order: int

    model_config = {"from_attributes": True}


class GlossaryTermOut(BaseModel):
    id: int
    category_id: int
    term_ko: str
    term_en: str | None = None
    short_desc: str
    detail_markdown: str | None = None
    formula: str | None = None
    example: str | None = None
    related_term_ids: list[int] | None = None
    category: GlossaryCategoryOut | None = None

    model_config = {"from_attributes": True}


class GlossaryGroupedOut(BaseModel):
    category: GlossaryCategoryOut
    terms: list[GlossaryTermOut]

