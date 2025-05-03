from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: str
    username: str
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
