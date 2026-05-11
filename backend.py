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


class Meeting_create(BaseModel):
    meeting_date: str = Field(..., min_length=10)
    start_time: str = Field(..., min_length=8)
    end_time: str = Field(min_length=8)
    president_email: str = Field(..., max_length=40)


class Proposal_create(BaseModel):
    title: str = Field(..., min_length=1)
    proposal_description: str = Field(..., min_length=1)
    attachment: str 
    meeting_id: int = Field(..., gt=0)


# -----------------------------------------------------------
# DB CONNECTION
# -----------------------------------------------------------

global conn, cursor
conn = psycopg2.connect(
    database="captive_portal",
    user="postgres",
    password="a",
    host="127.0.0.1",
    port=5432,
)
cursor = conn.cursor()

# -----------------------------------------------------------
# ENDPOINTS
# -----------------------------------------------------------

app = FastAPI(title="Captive Portal 5D")


@app.post("/login/")
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




@app.post("/create_meeting")
def create_meeting(request: Meeting_create):
    cursor.execute(
        """
        INSERT INTO meeting(
            meeting_date,
            start_time,
            end_time,
            president_email
        )
        VALUES (%s, %s, %s, %s)
        """,
        [
            request.meeting_date,
            request.start_time,
            request.end_time,
            request.president_email,
        ],
    )
    conn.commit()
    return {"message": "OK"}


@app.post("/create_proposal")
def create_proposal(request: Proposal_create):
    cursor.execute(
        """
        INSERT INTO proposal(
            title,
            proposal_description,
            attachment,
            meeting_id
        )
        VALUES (%s, %s, %s, %s)
        """,
        [
            request.title,
            request.proposal_description,
            request.attachment,
            request.meeting_id,
        ],
    )
    conn.commit()
    return {"message": "OK"}

@app.put("/update_proposal")
def update_proposal(request: Proposal_create, id : int):
    cursor.execute(
        """
        UPDATE proposal
        SET title = %s,
            proposal_description = %s,
            attachment = %s,
            meeting_id = %s
        WHERE id = %s
        """,
        [
            request.title,
            request.proposal_description,
            request.attachment,
            request.meeting_id,
            id,
        ],
    )
    conn.commit()
    return {"message": "OK"}


@app.get("/read_proposal")
def read_proposal():
    cursor.execute(
        """
        SELECT * 
        FROM proposal;
        """
    )
    list_tup = cursor.fetchall()
    for i in range(0, len(list_tup)):
        list_tup[i] = {
            "id": list_tup[i][0],
            "title": list_tup[i][1],
            "proposal_description": list_tup[i][2],
            "attachment": list_tup[i][3],
            "meeting_id": list_tup[i][4]
        }

    return list_tup

@app.get("/read_proposal/{proposal_id}")
def read_proposal(proposal_id: int):
    cursor.execute(
        f"SELECT * FROM proposal WHERE id = {proposal_id}"
    )
    conn.commit()
    
    list_tup = cursor.fetchall()
    list_tup = {
        "id": list_tup[0][0],
        "title": list_tup[0][1],
        "proposal_description": list_tup[0][2],
        "attachment": list_tup[0][3],
        "meeting_id": list_tup[0][4]
    }

    return list_tup


@app.get("/meetings/{meeting_id}/proposals")
def meetings_proposals(meeting_id: int):
    cursor.execute(
        f"SELECT p.id, p.title, p.proposal_description, p.attachment, p.meeting_id FROM proposal AS p INNER JOIN meeting AS m ON p.meeting_id = m.id WHERE m.id = {meeting_id}"
    )
    list_tup = cursor.fetchall()
    for i in range(0, len(list_tup)):
        list_tup[i] = {
            "id": list_tup[i][0],
            "title": list_tup[i][1],
            "proposal_description": list_tup[i][2],
            "attachment": list_tup[i][3],
            "meeting_id": list_tup[i][4]
        }
    return list_tup