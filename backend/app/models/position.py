from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TradingSettings(Base):
    __tablename__ = "trading_settings"
    __table_args__ = (UniqueConstraint("user_id", name="uq_trading_settings_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    batch_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    live_trading_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    selected_strategy_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    batch_interval_seconds: Mapped[int] = mapped_column(Integer, default=10)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TradingSignal(Base):
    __tablename__ = "trading_signals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    strategy_id: Mapped[str] = mapped_column(String(80), index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(100))
    side: Mapped[str] = mapped_column(String(10), default="buy")
    signal: Mapped[str] = mapped_column(String(255))
    current_price: Mapped[float] = mapped_column(Float)
    trigger_price: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    execution_mode: Mapped[str] = mapped_column(String(20), default="signal_only")
    status: Mapped[str] = mapped_column(String(30), default="captured")
    risk_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class TradingBatchRun(Base):
    __tablename__ = "trading_batch_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="completed")
    live_trading_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    selected_strategy_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    captured_signal_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
