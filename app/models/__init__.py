"""ORM models package — import all so Alembic can discover them."""

from app.models.alert import Alert
from app.models.price_history import PriceHistory
from app.models.product import Product
from app.models.user import User
from app.models.watchlist import Watchlist

__all__ = ["Alert", "PriceHistory", "Product", "User", "Watchlist"]
