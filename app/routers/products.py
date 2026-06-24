"""Products router: list, detail, price history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.deps import get_db
from app.repositories.product_repo import (
    get_price_history,
    get_product_by_id,
    list_products,
)
from app.schemas.product import PriceHistoryPoint, ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
def list_products_endpoint(
    brand: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list:
    return list_products(db, brand=brand, keyword=keyword, offset=offset, limit=limit)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.get("/{product_id}/history", response_model=list[PriceHistoryPoint])
def get_product_history(product_id: int, db: Session = Depends(get_db)):
    return get_price_history(db, product_id)
