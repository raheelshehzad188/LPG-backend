from pydantic import BaseModel


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    token: str
    user: dict


class PartnerLoginRequest(BaseModel):
    email: str
    password: str


class PartnerLoginResponse(BaseModel):
    token: str
    agent: dict
