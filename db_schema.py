from sqlalchemy import Table, Column, Integer, String, Float, MetaData
import sqlalchemy

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("username", String, unique=True, index=True),
    Column("hashed_password", String),
)

locations = Table(
    "locations",
    metadata,
    Column("id", sqlalchemy.Integer, primary_key=True),
    Column("name", String),
    Column("latitude", Float),
    Column("longitude", Float),
)
