from pydantic import BaseModel


class PaymentCreateSchema(BaseModel):
    order_id: int


class RefundRequestSchema(BaseModel):
    order_id: int