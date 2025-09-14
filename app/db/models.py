from sqlalchemy import Column, BigInteger, Text, Numeric, DateTime, func
from .db import Base

class GoldPrice(Base):
    __tablename__ = "gold_prices"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(Text, nullable=False, index=True)
    price = Column(Numeric(18, 6), nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
