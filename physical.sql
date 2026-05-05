-- --------------------------------- TABLES ---------------------------------

CREATE TABLE account(
    email        VARCHAR(40) PRIMARY KEY, 
    user_name    VARCHAR(40) NOT NULL,
    user_surname VARCHAR(40) NOT NULL,
    user_role    VARCHAR(20) NOT NULL,
    department   VARCHAR(20),

    CONSTRAINT check_role
        CHECK (user_role IN ('docente', 'dirigente'))
);


CREATE TABLE meeting(
    id                SERIAL PRIMARY KEY,
    meeting_date      DATE NOT NULL,
    start_time        TIME NOT NULL,
    end_time          TIME,
    participant_count INTEGER DEFAULT 0, -- NOT UPDATED YET (TO-DO in application)
    president_email   VARCHAR(40),

    CONSTRAINT fk_president
        FOREIGN KEY (president_email)
        REFERENCES account(email)
        ON DELETE SET NULL,

    CONSTRAINT check_time
        CHECK (end_time > start_time)
);


CREATE TABLE proposal(
    id                   SERIAL PRIMARY KEY,
    title                VARCHAR(100) NOT NULL,
    proposal_description TEXT,
    attachment           TEXT,
    meeting_id           INTEGER NOT NULL,

    CONSTRAINT fk_proposal_meeting
        FOREIGN KEY (meeting_id)
        REFERENCES meeting(id)
        ON DELETE CASCADE
);


CREATE TABLE token(
    code         VARCHAR(100) PRIMARY KEY,
    generated_at TIMESTAMP NOT NULL,
    expires_at   TIMESTAMP NOT NULL,
    user_email   VARCHAR(40) NOT NULL,
    meeting_id   INTEGER NOT NULL,

    CONSTRAINT fk_token_user
        FOREIGN KEY (user_email)
        REFERENCES account(email)
        ON DELETE CASCADE,

    CONSTRAINT fk_token_meeting 
        FOREIGN KEY (meeting_id)
        REFERENCES meeting(id)
        ON DELETE CASCADE,
        
    CONSTRAINT check_expiration
        CHECK (expires_at > generated_at),

    CONSTRAINT unique_token_in_meeting 
        UNIQUE (user_email, meeting_id)
);


CREATE TABLE participation(
    meeting_id INTEGER,
    user_email VARCHAR(40),

    PRIMARY KEY (meeting_id, user_email),

    CONSTRAINT fk_participation_meeting
        FOREIGN KEY (meeting_id) 
        REFERENCES meeting(id) 
        ON DELETE CASCADE,

    CONSTRAINT fk_participation_user
        FOREIGN KEY (user_email)
        REFERENCES account(email)
        ON DELETE CASCADE
);


CREATE TABLE vote(
    account_email VARCHAR(40),
    proposal_id INT,
    preference INT NOT NULL

    PRIMARY KEY (account_email, proposal_id)

    CONSTRAINT preference_options
        CHECK (preference IN ( 0, 1, 2)),

    CONSTRAINT fk_account_email
        FOREIGN KEY (account_email)
        REFERENCES account(email),

    CONSTRAINT fk_proposal_id
        FOREIGN KEY (proposal_id)
        REFERENCES proposal(id)
)


-- --------------------------------- ROLES ---------------------------------

CREATE ROLE teacher LOGIN PASSWORD 'praga';
GRANT SELECT ON meeting, proposal, account TO teacher;
GRANT SELECT, INSERT ON participation TO teacher;
GRANT UPDATE (vote) ON participation TO teacher;


-- CREATE ROLE secretary LOGIN PASSWORD 'praga';
-- GRANT SELECT ON meeting, account TO secretary;
-- GRANT SELECT, INSERT ON participation TO secretary;
-- GRANT SELECT, INSERT, UPDATE (title, proposal_description, attachment) ON proposal TO secretary;
-- GRANT USAGE ON SEQUENCE proposal_id_seq TO secretary;   -- fundamental for INSERT INTO
-- GRANT SELECT, INSERT ON token TO secretary;


CREATE ROLE principal LOGIN PASSWORD 'praga';
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO principal;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO principal;
