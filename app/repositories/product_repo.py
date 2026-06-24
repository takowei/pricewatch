"""Product repository — pure DB access, no business logic."""

from __future__ import annotations

from datetime import date

from sqlmodel import Session, select

from app.models.price_history import PriceHistory
from app.models.product import Product


def get_product_by_id(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def get_product_by_url(db: Session, url: str) -> Product | None:
    return db.exec(select(Product).where(Product.product_url == url)).first()


def upsert_product(db: Session, data: dict) -> Product:
    """Insert or update a product keyed on product_url (idempotent)."""
    product = get_product_by_url(db, data["product_url"])
    if product is None:
        product = Product(**data)
        db.add(product)
    else:
        for key, value in data.items():
            setattr(product, key, value)
        db.add(product)
    db.commit()
    db.refresh(product)
    return product


def upsert_price_history(
    db: Session,
    product_id: int,
    sale_price: int | None,
    discount: int | None,
    recorded_date: date,
) -> PriceHistory:
    """Insert or overwrite the price record for (product_id, recorded_date)."""
    existing = db.exec(
        select(PriceHistory).where(
            PriceHistory.product_id == product_id,
            PriceHistory.recorded_date == recorded_date,
        )
    ).first()

    if existing is None:
        ph = PriceHistory(
            product_id=product_id,
            sale_price=sale_price,
            discount=discount,
            recorded_date=recorded_date,
        )
        db.add(ph)
    else:
        existing.sale_price = sale_price
        existing.discount = discount
        db.add(existing)
    db.commit()
    return existing or ph  # type: ignore[return-value]


def list_products(
    db: Session,
    brand: str | None = None,
    keyword: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[Product]:
    q = select(Product)
    if brand:
        q = q.where(Product.brand == brand)
    if keyword:
        q = q.where(Product.name.ilike(f"%{keyword}%"))  # type: ignore[union-attr]
    q = q.offset(offset).limit(limit)
    return list(db.exec(q).all())


def get_price_history(db: Session, product_id: int) -> list[PriceHistory]:
    return list(
        db.exec(
            select(PriceHistory)
            .where(PriceHistory.product_id == product_id)
            .order_by(PriceHistory.recorded_date)
        ).all()
    )
