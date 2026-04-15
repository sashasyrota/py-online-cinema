from pydantic import BaseModel


class PaymentCreateSchema(BaseModel):
    order_id: int