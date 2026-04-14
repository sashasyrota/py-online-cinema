from pydantic import BaseModel


class OrderItemCreateSchema(BaseModel):
    movie_id: int