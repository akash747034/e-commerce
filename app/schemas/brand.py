
from pydantic import BaseModel, ConfigDict


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    logo_url: str | None
    website: str | None
    is_active: bool
