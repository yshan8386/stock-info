from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import RssFeed
from app.schemas.feed import FeedCreate, FeedOut, FeedPatch

router = APIRouter(prefix="/feeds", tags=["feeds"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[FeedOut])
def list_feeds(db: Session = Depends(get_db)) -> list[RssFeed]:
    return list(db.scalars(select(RssFeed).order_by(RssFeed.category, RssFeed.name)))


@router.post("", response_model=FeedOut, status_code=status.HTTP_201_CREATED)
def create_feed(payload: FeedCreate, db: Session = Depends(get_db)) -> RssFeed:
    if db.scalar(select(RssFeed.id).where(RssFeed.url == str(payload.url))):
        raise HTTPException(status_code=400, detail="Feed URL already exists")
    feed = RssFeed(
        name=payload.name,
        url=str(payload.url),
        category=payload.category,
        language=payload.language,
    )
    db.add(feed)
    db.commit()
    db.refresh(feed)
    return feed


@router.patch("/{feed_id}", response_model=FeedOut)
def update_feed(feed_id: int, payload: FeedPatch, db: Session = Depends(get_db)) -> RssFeed:
    feed = db.get(RssFeed, feed_id)
    if feed is None:
        raise HTTPException(status_code=404, detail="Feed not found")
    if payload.is_active is not None:
        feed.is_active = payload.is_active
    db.commit()
    db.refresh(feed)
    return feed


@router.delete("/{feed_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feed(feed_id: int, db: Session = Depends(get_db)) -> None:
    feed = db.get(RssFeed, feed_id)
    if feed is None:
        raise HTTPException(status_code=404, detail="Feed not found")
    db.delete(feed)
    db.commit()

