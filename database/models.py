"""
SQLAlchemy ORM Models for Tewabu ERP.
Ensures strict user and business data isolation with full audit timestamps.
"""

from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(64), nullable=True)
    full_name = Column(String(128), nullable=True)
    language = Column(String(8), default="am", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    business = relationship("Business", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User telegram_id={self.telegram_id} lang={self.language}>"

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    name = Column(String(128), default="የተዋቡ ስፌት ቤት", nullable=False)
    currency = Column(String(8), default="ETB", nullable=False)
    default_profit_margin = Column(Numeric(6, 4), default=Decimal("0.25"), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="business")
    designs = relationship("Design", back_populates="business", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="business", cascade="all, delete-orphan")
    financial_records = relationship("FinancialRecord", back_populates="business", cascade="all, delete-orphan")
    settings = relationship("BusinessSetting", back_populates="business", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Business id={self.id} name='{self.name}'>"

class Design(Base):
    __tablename__ = "designs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)
    customer_name = Column(String(128), nullable=True)
    order_id_code = Column(String(64), nullable=True)
    image_file_id = Column(String(256), nullable=True)
    gender = Column(String(16), nullable=True)  # MALE, FEMALE
    clothing_item = Column(String(64), nullable=True)  # 1ቲሸርት (ተከፋች), 2ቲሸርት (ያለተከፋች), 3ጃኬት, 4ሱሪ, ወዘተ
    measurements_json = Column(Text, nullable=True)  # JSON string of tailoring measurements
    
    target_profit_margin = Column(Numeric(6, 4), default=Decimal("0.25"), nullable=False)
    total_cost = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    break_even_price = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    optimal_price = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    actual_selling_price = Column(Numeric(12, 2), nullable=True)
    actual_profit = Column(Numeric(12, 2), nullable=True)
    profit_margin_pct = Column(Numeric(6, 2), nullable=True)
    status = Column(String(32), nullable=True)  # ProfitStatus enum name
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    business = relationship("Business", back_populates="designs")
    expenses = relationship("Expense", back_populates="design", cascade="all, delete-orphan", order_by="Expense.id")
    orders = relationship("Order", back_populates="design")

    def __repr__(self) -> str:
        return f"<Design id={self.id} name='{self.name}' cost={self.total_cost}>"

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    design_id = Column(Integer, ForeignKey("designs.id", ondelete="CASCADE"), nullable=False, index=True)
    category_key = Column(String(64), nullable=False)  # menen_gever, thread, sewing, etc.
    category_name = Column(String(128), nullable=False)
    amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    is_custom = Column(Boolean, default=False, nullable=False)
    note = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    design = relationship("Design", back_populates="expenses")

    def __repr__(self) -> str:
        return f"<Expense {self.category_key}={self.amount}>"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    design_id = Column(Integer, ForeignKey("designs.id", ondelete="SET NULL"), nullable=True, index=True)
    order_number = Column(String(64), nullable=False, index=True)
    customer_name = Column(String(128), nullable=False)
    customer_phone = Column(String(32), nullable=True)
    status = Column(String(32), default="PENDING", nullable=False, index=True)  # OrderStatus
    agreed_price = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    advance_payment = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    balance_due = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    due_date = Column(Date, nullable=True)
    reminder_5d_sent = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    business = relationship("Business", back_populates="orders")
    design = relationship("Design", back_populates="orders")
    financial_records = relationship("FinancialRecord", back_populates="order")

    def __repr__(self) -> str:
        return f"<Order #{self.order_number} status={self.status} due={self.balance_due}>"

class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    design_id = Column(Integer, ForeignKey("designs.id", ondelete="SET NULL"), nullable=True, index=True)
    record_type = Column(String(16), nullable=False)  # INCOME, EXPENSE
    amount = Column(Numeric(12, 2), nullable=False)
    category = Column(String(64), nullable=False)
    description = Column(String(256), nullable=True)
    record_date = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    business = relationship("Business", back_populates="financial_records")
    order = relationship("Order", back_populates="financial_records")

    def __repr__(self) -> str:
        return f"<FinancialRecord {self.record_type} amount={self.amount}>"

class BusinessSetting(Base):
    __tablename__ = "business_settings"
    __table_args__ = (UniqueConstraint("business_id", "key", name="uq_business_key"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(64), nullable=False)
    value = Column(String(256), nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    business = relationship("Business", back_populates="settings")

    def __repr__(self) -> str:
        return f"<BusinessSetting {self.key}={self.value}>"
