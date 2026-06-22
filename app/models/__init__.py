# Import all models here so Django can discover them via `app.models`
from app.models.customer import User

__all__ = ["User"]
