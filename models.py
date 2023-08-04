from pydantic import BaseModel

class LocationIn(BaseModel):
    name: str
    latitude: float
    longitude: float

class Location(LocationIn):
    id: int
    
class RegisterRequest(BaseModel):
    username: str
    password: str