from typing import Literal

import psycopg2
from fastapi import FastAPI, Response
from pydantic import BaseModel, Field


class Request(BaseModel):
    token: str = Field(..., min_length=1)


class UserCreate(BaseModel):
    email: str = Field(..., min_length=7)
    user_name: str = Field(..., min_length=1)
    user_surname: str = Field(..., min_length=1)
    user_role: Literal["normal", "super_user"]
    user_department: str = Field(..., min_length=1)


class UserRead(BaseModel):
    email: str
    user_name: str
    user_surname: str
    user_role: str
    user_department: str


# -----------------------------------------------------------
# DB CONNECTION
# -----------------------------------------------------------

global conn, cursor
conn = psycopg2.connect(
    database="captive_portal",
    user="postgres",
    password="",
    host="127.0.0.1",
    port=5432,
)
cursor = conn.cursor()

# -----------------------------------------------------------
# ENDPOINTS
# -----------------------------------------------------------

app = FastAPI(title="Captive Portal 5D")


@app.post("/login")
def login(request: Request, response: Response):

    cursor.execute(
        """
        SELECT code
        FROM token 
        WHERE code = %s
        """,
        [request.token],
    )
    res = cursor.fetchone()[0]

    if res is not None:
        response.set_cookie(key="token_session", value=str(request.token))
        return {"message": "OK"}
    else:
        return {"error": "Invalid Token"}


@app.get("/test")
def test():
    cursor.execute(
        """
        SELECT * 
        FROM cp_user;
        """
    )
    # conn.commit()
    return cursor.fetchall()
