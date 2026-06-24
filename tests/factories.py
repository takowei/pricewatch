"""Test data factories — create ORM objects directly without HTTP."""

from __future__ import annotations

from datetime import date

from sqlmodel import Session

from app.core.security import hash_password
from app.models.price_history import PriceHistory
from app.models.product import Product
from app.models.user import User
from app.models.watchlist import Watchlist


def make_user(
    db: Session,
    email: str = "test@example.com",
    password: str = "password123",
) -> User:
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_product(
    db: Session,
    brand: str = "uniqlo",
    name: str = "Test Pants",
    category: str = "男裝特價",
    product_url: str = "https://example.com/product/1",
    sale_price: int = 590,
    original_price: int = 990,
    discount: int = 40,
) -> Product:
    p = Product(
        brand=brand,
        name=name,
        category=category,
        product_url=product_url,
        image_url="",
        current_sale_price=sale_price,
        original_price=original_price,
        discount=discount,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def make_price_history(
    db: Session,
    product_id: int,
    sale_price: int,
    recorded_date: date,
) -> PriceHistory:
    ph = PriceHistory(
        product_id=product_id,
        sale_price=sale_price,
        discount=0,
        recorded_date=recorded_date,
    )
    db.add(ph)
    db.commit()
    db.refresh(ph)
    return ph


def make_watchlist(
    db: Session,
    user_id: int,
    keyword: str = "Pants",
    max_price: int | None = 800,
) -> Watchlist:
    w = Watchlist(user_id=user_id, keyword=keyword, max_price=max_price)
    db.add(w)
    db.commit()
    db.refresh(w)
    return w
