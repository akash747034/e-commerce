from pydantic import BaseModel, ConfigDict


class WishlistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
