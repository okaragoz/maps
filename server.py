import os
from fastapi import FastAPI
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from databases import Database
from typing import List
from sqlalchemy import create_engine, MetaData, Table, Column, Float, String
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from auth import Token, User, UserInDB, UserCreate, verify_password, get_password_hash, create_access_token
from db_schema import users, locations
from models import Location, LocationIn, RegisterRequest
from starlette.middleware.sessions import SessionMiddleware
from fastapi import HTTPException

# Database
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
database = Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

app = FastAPI()
app.add_middleware(
    SessionMiddleware, secret_key="your-secret-key", https_only=False
)

async def get_user_by_username(username: str):
    query = users.select().where(users.c.username == username)
    return await database.fetch_one(query)
async def get_current_user(request: Request):
    username = request.session.get("username")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = await get_user_by_username(username=username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user

async def authenticate_user(username: str, password: str):
    query = users.select().where(users.c.username == username)
    user_record = await database.fetch_one(query)
    if not user_record or not verify_password(password, user_record.hashed_password):
        return False
    return user_record
    
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
        )
    request.session["username"] = user.username
    response = RedirectResponse(url="/maps")
    return response

app.mount("/page", StaticFiles(directory="page"), name="page")

@app.get("/")
def login_page():
    return FileResponse("./page/index.html")

@app.get("/maps")
def read_root(request: Request, current_user: User = Depends(get_current_user)):
    return FileResponse("./page/maps.html")

@app.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    hashed_password = get_password_hash(user.password)
    query = users.insert().values(username=user.username, hashed_password=hashed_password)
    await database.execute(query)
    return {"username": user.username}

@app.post("/token/")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    request.session["username"] = user.username
    return {"message": "Login successful", "redirect_url": "/maps"}


@app.post("/location/", response_model=Location)
async def create_location(request: Request, location: LocationIn, current_user: User = Depends(get_current_user)):
    query = locations.insert().values(name=location.name, latitude=location.latitude, longitude=location.longitude)
    last_record_id = await database.execute(query)
    return {**location.dict(), "id": last_record_id}

@app.get("/location/", response_model=List[Location])
async def get_locations(request: Request, current_user: User = Depends(get_current_user)):
    query = locations.select()
    return await database.fetch_all(query)

@app.get("/location/{location_id}", response_model=Location)
async def get_location(request: Request, location_id: int, current_user: User = Depends(get_current_user)):
    query = locations.select().where(locations.c.id == location_id)
    return await database.fetch_one(query)

@app.put("/location/{location_id}", response_model=Location)
async def update_location(request: Request, location_id: int, location: LocationIn, current_user: User = Depends(get_current_user)):
    query = locations.update().where(locations.c.id == location_id).values(name=location.name, latitude=location.latitude, longitude=location.longitude)
    await database.execute(query)
    return {**location.dict(), "id": location_id}

@app.delete("/location/{location_id}")
async def delete_location(request: Request, location_id: int, current_user: User = Depends(get_current_user)):
    query = locations.delete().where(locations.c.id == location_id)
    await database.execute(query)
    return {"message": "Location deleted"}

@app.post("/register/")
async def register(request: RegisterRequest):
    hashed_password = get_password_hash(request.password)
    query = users.insert().values(username=request.username, hashed_password=hashed_password)
    await database.execute(query)
    return {"username": request.username}

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/logout/")
async def logout(request: Request):
    request.session.pop("username", None)  # Remove the username from the session
    return RedirectResponse(url="/")  # Redirect back to the login page or wherever you want




