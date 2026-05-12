from typing import Literal

import psycopg2
from fastapi import FastAPI, Header, Response
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
    try:
        cursor.execute(
            """
            SELECT code
            FROM token 
            WHERE code = %s
            """,
            [request.token],
        )
        res = cursor.fetchone()

        if res is not None:
            cursor.execute(
                """
                INSERT INTO participation(meeting_id, user_email)
                    SELECT meeting_id, user_email
                    FROM token
                    WHERE code = %s
                """,
                [request.token],
            )
            cursor.connection.commit()
            response.set_cookie(key="token_session", value=str(request.token))
            return {"message": "OK"}
        else:
            return {"error": "Invalid Token"}
    except Exception as e:
        print(f"[ERROR] /login: {e}")
        return {"errore": "Internal server error"}


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


@app.get("/proposals/{id}/stats")
def proposals_stats(id: int):
    cursor.execute(
        """
        SELECT p.id,p.title,m.participant_count
        FROM proposal p 
        LEFT JOIN meetings m ON p.meeting_id = m.id
        WHERE p.id = %s
        ORDER BY p.id
        """,
        [id],
    )
    return cursor.fetchone()


@app.get("/meetings/{id}/stats")
def meetings_stats(id: int):
    cursor.execute(
        """
        SELECT
            m.id, m.meeting_date, m.start_time,m.end_time,m.president_email, m.participant_count
            FROM meeting m 
            LEFT JOIN participation p ON m.id = p.meeting_id
            WHERE m.id = %s
            GROUP BY m.id
        """,
        [id],
    )

    return cursor.fetchone()


@app.post("/logout")
def logout(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    try:
        cursor.execute(
            """
                    UPDATE token 
                    SET expires_at = NOW() 
                    WHERE code = %s
                """,
            [token],
        )
        cursor.connection.commit()
    except Exception as e:
        cursor.connection.rollback()
        print(f"[ERROR] /login: {e}")
        return {"errore": "Internal server error"}