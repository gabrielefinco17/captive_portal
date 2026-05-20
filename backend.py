from typing import Literal
import psycopg2
from fastapi import FastAPI, Request, Header
from pydantic import BaseModel, Field


# -----------------------------------------------------------
# MODELS
# -----------------------------------------------------------

class LoginRequest(BaseModel):
    token: str = Field(..., min_length=1)


class UserCreate(BaseModel):
    token: str = Field(..., min_length=1)
    email: str = Field(..., min_length=7)
    user_name: str = Field(..., min_length=1)
    user_surname: str = Field(..., min_length=1)
    user_role: Literal["teacher", "principal"]
    user_department: str = Field(..., min_length=1)


class UserRead(BaseModel):
    email: str
    user_name: str
    user_surname: str
    user_role: str
    user_department: str


class MeetingCreate(BaseModel):
    meeting_date: str = Field(..., min_length=10)
    start_time: str = Field(..., min_length=8)
    end_time: str | None = Field(default=None)
    president_email: str | None = Field(default=None, max_length=40)


class ProposalCreate(BaseModel):
    title: str = Field(..., min_length=1)
    proposal_description: str = Field(..., min_length=1)
    attachment: str
    meeting_id: int = Field(..., gt=0)


class ProposalUpdate(BaseModel):
    title: str = Field(min_length=1)
    proposal_description: str = Field(min_length=1)
    attachment: str
    meeting_id: int = Field(gt=0)


class VoteCreate(BaseModel):
    token: str = Field(..., min_length=1)
    account_email: str = Field(..., min_length=1, max_length=40)
    proposal_id: int = Field(..., gt=0)
    preference: Literal[0, 1, 2]


class VoteRead(BaseModel):
    account_email: str
    proposal_id: int
    preference: int


class VoteSubmitRequest(BaseModel):
    proposal_id: int = Field(..., gt=0)
    preference: str = Field(..., min_length=1)


class AttendanceRequest(BaseModel):
    status: Literal["present", "exited"]


# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------

teacher_pass = "praga"
principal_pass = "praga"
host_ip = "127.0.0.1"
port = 5432

def get_password(role: str) -> str:
    return principal_pass if role == "principal" else teacher_pass

def get_db_conn(role: str = "principal"):
    return psycopg2.connect(
        database="captive_portal",
        user=role,
        password=get_password(role),
        host=host_ip,
        port=port,
        connect_timeout=5
    )


# -----------------------------------------------------------
# ENDPOINTS
# -----------------------------------------------------------

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Captive Portal 5D")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/login")
def login(request: LoginRequest):
    conn = None
    cursor = None
    try:
        user = check_token(request.token)
        if user:
            conn = get_db_conn(user[1])
            cursor = conn.cursor()
            cursor.execute(
                """
                    INSERT INTO participation(meeting_id, user_email)
                    SELECT meeting_id, user_email
                    FROM token
                    WHERE code = %s
                    ON CONFLICT DO NOTHING
                """,
                [request.token]
            )
            cursor.connection.commit()
            return {"login_status": "OK"}
        else:
            return {"login_status": "NO_AUTH"}
    except Exception as e:
        if cursor:
            cursor.connection.rollback()
        return {"error": f"Internal server error: {str(e)}"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.post("/create_meeting")
def create_meeting(request: MeetingCreate, authorization: str = Header(...)):
    conn = None
    cursor = None
    user = check_token(authorization.replace("Bearer ", ""))
    if user:
        if user[1] == "principal":
            conn = get_db_conn(user[1])
            cursor = conn.cursor()
            try:
                president_email = request.president_email if request.president_email else user[0]
                cursor.execute(
                    """
                        INSERT INTO meeting(
                            meeting_date,
                            start_time,
                            end_time,
                            president_email
                        )
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """,
                    [
                        request.meeting_date,
                        request.start_time,
                        request.end_time,
                        president_email,
                    ]
                )
                meeting_id = cursor.fetchone()[0]
                cursor.connection.commit()
                return {"create_status": "OK", "meeting_id": meeting_id}
            except Exception as e:
                cursor.connection.rollback()
                return {"error": f"Internal server error: {str(e)}"}
            finally:
                cursor.close()
                conn.close()
        else:
            return {"create_status": "FORBIDDEN"}
    else:
        return {"create_status": "NO_AUTH"}


@app.post("/create_proposal")
def create_proposal(request: ProposalCreate, authorization: str = Header(...)):
    conn = None
    cursor = None
    user = check_token(authorization.replace("Bearer ", ""))
    if user:
        if user[1] == "principal":
            conn = get_db_conn(user[1])
            cursor = conn.cursor()
            try:
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
                    ]
                )
                cursor.connection.commit()
                return {"insert_status": "OK"}
            except Exception:
                cursor.connection.rollback()
                return {"error": "Internal server error"}
            finally:
                cursor.close()
                conn.close()
        else:
            return {"insert_status": "FORBIDDEN"}
    else:
        return {"insert_status": "NO_AUTH"}


@app.put("/update_proposal")
def update_proposal(request: ProposalUpdate, id: int, authorization: str = Header(...)):
    conn = None
    cursor = None
    user = check_token(authorization.replace("Bearer ", ""))
    if user:
        if user[1] == "principal":
            conn = get_db_conn(user[1])
            cursor = conn.cursor()
            try:
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
                    ]
                )
                cursor.connection.commit()
                return {"update_status": "OK"}
            except Exception:
                cursor.connection.rollback()
                return {"error": "Internal server error"}
            finally:
                cursor.close()
                conn.close()
        else:
            return {"update_status": "FORBIDDEN"}
    else:
        return {"update_status": "NO_AUTH"}


@app.get("/read_proposal")
def read_all_proposals(request: Request):
    conn = None
    cursor = None
    try:
        auth = request.headers.get("Authorization", "")
        user = check_token(auth.replace("Bearer ", ""))
        if user:
            conn = get_db_conn(user[1])
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM proposal")
            list_tup = cursor.fetchall()
            for i in range(len(list_tup)):
                list_tup[i] = {
                    "id": list_tup[i][0],
                    "title": list_tup[i][1],
                    "proposal_description": list_tup[i][2],
                    "attachment": list_tup[i][3],
                    "meeting_id": list_tup[i][4],
                }
            return list_tup
        else:
            return {"read_status": "NO_AUTH"}
    except Exception:
        return {"error": "Internal server error"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/read_proposal/{proposal_id}")
def read_proposal(proposal_id: int, request: Request):
    conn = None
    cursor = None
    try:
        auth = request.headers.get("Authorization", "")
        user = check_token(auth.replace("Bearer ", ""))
        if user:
            conn = get_db_conn(user[1])
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM proposal WHERE id = %s",
                [proposal_id]
            )
            row = cursor.fetchone()
            if row is None:
                return {"read_status": "NOT_FOUND"}
            return {
                "id": row[0],
                "title": row[1],
                "proposal_description": row[2],
                "attachment": row[3],
                "meeting_id": row[4],
            }
        else:
            return {"read_status": "NO_AUTH"}
    except Exception:
        return {"error": "Internal server error"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/meeting/{meeting_id}/proposals")
def meeting_proposals(meeting_id: int, request: Request):
    conn = None
    cursor = None
    try:
        auth = request.headers.get("Authorization", "")
        user = check_token(auth.replace("Bearer ", ""))
        if user:
            conn = get_db_conn(user[1])
            cursor = conn.cursor()
            cursor.execute(
                """
                    SELECT p.id, p.title, p.proposal_description, p.attachment, p.meeting_id
                    FROM proposal AS p
                    INNER JOIN meeting AS m ON p.meeting_id = m.id
                    WHERE m.id = %s
                """,
                [meeting_id]
            )
            list_tup = cursor.fetchall()
            for i in range(len(list_tup)):
                list_tup[i] = {
                    "id": list_tup[i][0],
                    "title": list_tup[i][1],
                    "proposal_description": list_tup[i][2],
                    "attachment": list_tup[i][3],
                    "meeting_id": list_tup[i][4],
                }
            return list_tup
        else:
            return {"read_status": "NO_AUTH"}
    except Exception:
        return {"error": "Internal server error"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/proposals/{id}/stats")
def proposals_stats(id: int, request: Request):
    conn = None
    cursor = None
    try:
        auth = request.headers.get("Authorization", "")
        user = check_token(auth.replace("Bearer ", ""))
        if user:
            conn = get_db_conn(user[1])
            cursor = conn.cursor()
            cursor.execute(
                """
                    SELECT p.id, p.title, COUNT(pa.user_email) AS participant_count
                    FROM proposal p
                    LEFT JOIN meeting m ON p.meeting_id = m.id
                    LEFT JOIN participation pa ON m.id = pa.meeting_id
                    WHERE p.id = %s
                    GROUP BY p.id, p.title
                    ORDER BY p.id
                """,
                [id]
            )
            row = cursor.fetchone()
            
            cursor.execute(
                """
                    SELECT 
                        COALESCE(SUM(CASE WHEN preference = 2 THEN 1 ELSE 0 END), 0) AS in_favour,
                        COALESCE(SUM(CASE WHEN preference = 0 THEN 1 ELSE 0 END), 0) AS against,
                        COALESCE(SUM(CASE WHEN preference = 1 THEN 1 ELSE 0 END), 0) AS abstained
                    FROM vote
                    WHERE proposal_id = %s
                """,
                [id]
            )
            vote_row = cursor.fetchone()
            
            if row:
                vote_data = vote_row if vote_row else (0, 0, 0)
                return {
                    "id": row[0],
                    "title": row[1],
                    "participant_count": row[2],
                    "favorevole": vote_data[0],
                    "non_favorevole": vote_data[1],
                    "astenuto": vote_data[2]
                }
            return {"read_status": "NOT_FOUND"}
        else:
            return {"read_status": "NO_AUTH"}
    except Exception:
        return {"error": "Internal server error"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/meetings/{id}/stats")
def meetings_stats(id: int, request: Request):
    conn = None
    cursor = None
    try:
        auth = request.headers.get("Authorization", "")
        user = check_token(auth.replace("Bearer ", ""))
        if user:
            conn = get_db_conn(user[1])
            cursor = conn.cursor()
            cursor.execute(
                """
                    SELECT m.id, m.meeting_date, m.start_time, m.end_time, m.president_email, COUNT(p.user_email) AS participant_count
                    FROM meeting m
                    LEFT JOIN participation p ON m.id = p.meeting_id
                    WHERE m.id = %s
                    GROUP BY m.id
                """,
                [id]
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "meeting_date": str(row[1]),
                    "start_time": str(row[2]),
                    "end_time": str(row[3]) if row[3] is not None else None,
                    "president_email": row[4],
                    "participant_count": row[5]
                }
            return {"read_status": "NOT_FOUND"}
        else:
            return {"read_status": "NO_AUTH"}
    except Exception:
        return {"error": "Internal server error"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.put("/meetings/{id}/end")
def end_meeting(id: int, authorization: str = Header(...)):
    conn = None
    cursor = None
    token = authorization.replace("Bearer ", "")
    user = check_token(token)
    if user:
        if user[1] == "principal":
            conn = get_db_conn(user[1])
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                        UPDATE meeting
                        SET end_time = NOW()::TIME
                        WHERE id = %s
                    """,
                    [id]
                )
                cursor.connection.commit()
                return {"end_status": "OK"}
            except Exception as e:
                cursor.connection.rollback()
                return {"error": f"Internal server error: {str(e)}"}
            finally:
                cursor.close()
                conn.close()
        else:
            return {"end_status": "FORBIDDEN"}
    else:
        return {"end_status": "NO_AUTH"}


@app.post("/submit_vote")
def submit_vote(request: VoteSubmitRequest, authorization: str = Header(...)):
    conn = None
    cursor = None
    token = authorization.replace("Bearer ", "")
    user = check_token(token)
    if user:
        conn = get_db_conn(user[1])
        cursor = conn.cursor()
        
        pref_map = {
            "non favorevole": 0,
            "astenuto": 1,
            "favorevole": 2
        }
        num_pref = pref_map.get(request.preference.lower(), 1)
        
        try:
            cursor.execute(
                """
                    INSERT INTO vote(account_email, proposal_id, preference)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (account_email, proposal_id)
                    DO UPDATE SET preference = %s
                """,
                [user[0], request.proposal_id, num_pref, num_pref]
            )
            cursor.connection.commit()
            return {"vote_status": "OK"}
        except Exception as e:
            cursor.connection.rollback()
            return {"error": f"Internal server error: {str(e)}"}
        finally:
            cursor.close()
            conn.close()
    else:
        return {"vote_status": "NO_AUTH"}


@app.get("/meetings/{meeting_id}/attendance")
def get_attendance(meeting_id: int, request: Request):
    conn = None
    cursor = None
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")
    user = check_token(token)
    if user:
        conn = get_db_conn(user[1])
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                    SELECT has_exited 
                    FROM participation 
                    WHERE meeting_id = %s AND user_email = %s
                """,
                [meeting_id, user[0]]
            )
            row = cursor.fetchone()
            if row is not None:
                has_exited = row[0]
                return {"isPresent": not has_exited, "hasExited": has_exited}
            else:
                return {"isPresent": False, "hasExited": False}
        except Exception as e:
            return {"error": f"Internal server error: {str(e)}"}
        finally:
            cursor.close()
            conn.close()
    else:
        return {"isPresent": False, "hasExited": False}


@app.post("/meetings/{meeting_id}/attendance")
def set_attendance(meeting_id: int, request: AttendanceRequest, authorization: str = Header(...)):
    conn = None
    cursor = None
    token = authorization.replace("Bearer ", "")
    user = check_token(token)
    if user:
        conn = get_db_conn(user[1])
        cursor = conn.cursor()
        has_exited = True if request.status == "exited" else False
        try:
            cursor.execute(
                """
                    INSERT INTO participation(meeting_id, user_email, has_exited)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (meeting_id, user_email)
                    DO UPDATE SET has_exited = %s
                """,
                [meeting_id, user[0], has_exited, has_exited]
            )
            cursor.connection.commit()
            return {"attendance_status": "OK"}
        except Exception as e:
            cursor.connection.rollback()
            return {"error": f"Internal server error: {str(e)}"}
        finally:
            cursor.close()
            conn.close()
    else:
        return {"attendance_status": "NO_AUTH"}


@app.post("/logout")
def logout(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    conn = None
    cursor = None
    try:
        user = check_token(token)
        if user:
            conn = get_db_conn(user[1])
            cursor = conn.cursor()
            cursor.execute(
                """
                    UPDATE token
                    SET expires_at = NOW()
                    WHERE code = %s
                """,
                [token]
            )
            cursor.connection.commit()
            return {"logout_status": "OK"}
        else:
            return {"logout_status": "NO_AUTH"}
    except Exception:
        if cursor:
            cursor.connection.rollback()
        return {"error": "Internal server error"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# -----------------------------------------------------------
# UTILITIES
# -----------------------------------------------------------

def check_token(tok: str):
    conn = None
    cursor = None
    try:
        conn = get_db_conn("principal")
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT account.email, account.user_role, token.code
                FROM token
                INNER JOIN account ON account.email = token.user_email
                WHERE token.code = %s
                AND token.expires_at > NOW()
            """,
            [tok]
        )
        return cursor.fetchone()  # None if not found
    except Exception as e:
        print(f"check_token FAILED: {type(e).__name__}: {e}")
        if cursor:
            cursor.connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()