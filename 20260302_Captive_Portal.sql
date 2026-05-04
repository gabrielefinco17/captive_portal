CREATE ROLE normal LOGIN PASSWORD 'qwerty';
CREATE ROLE super_user LOGIN PASSWORD 'qwerty';

CREATE TABLE cp_user (
    email VARCHAR(40) PRIMARY KEY, 
    user_name VARCHAR(40) NOT NULL,
    user_surname VARCHAR(40) NOT NULL,
    user_role VARCHAR(20) NOT NULL,
    department VARCHAR(20),

    CONSTRAINT check_role
        CHECK (user_role IN ('normal', 'super_user'))
);



CREATE TABLE meeting (
    id SERIAL PRIMARY KEY,
    meeting_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    participant_count INTEGER DEFAULT 0,

    president_email VARCHAR(40),

    CONSTRAINT fk_president
        FOREIGN KEY (president_email) REFERENCES "cp_user"(email) ON DELETE SET NULL,

    CONSTRAINT check_time
        CHECK (end_time > start_time)
);




CREATE TABLE proposal (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    proposal_description TEXT,
    attachment VARCHAR(100),
    meeting_id INTEGER NOT NULL,
    CONSTRAINT fk_proposal_meeting
        FOREIGN KEY (meeting_id)
        REFERENCES meeting(id)
        ON DELETE CASCADE
);



CREATE TABLE token (
    code VARCHAR(100) PRIMARY KEY,
    generated_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,

    user_email VARCHAR(40) NOT NULL,
    meeting_id INTEGER NOT NULL,

    CONSTRAINT fk_token_user
        FOREIGN KEY (user_email) REFERENCES "cp_user"(email) ON DELETE CASCADE,

    CONSTRAINT fk_token_meeting 
        FOREIGN KEY (meeting_id) REFERENCES meeting(id) ON DELETE CASCADE,

    CONSTRAINT check_expiration
        CHECK (expires_at > generated_at)
);



CREATE TABLE participation (
    meeting_id INTEGER,
    user_email VARCHAR(40),
    vote BOOLEAN,
    PRIMARY KEY (meeting_id, user_email),
    CONSTRAINT fk_participation_meeting
        FOREIGN KEY (meeting_id) REFERENCES meeting(id) ON DELETE CASCADE,

    CONSTRAINT fk_participation_user
        FOREIGN KEY (user_email) REFERENCES "cp_user"(email) ON DELETE CASCADE
);


GRANT SELECT ON cp_user TO normal;
GRANT SELECT ON meeting TO normal;


GRANT SELECT ON cp_user TO super_user;
GRANT SELECT ON meeting TO super_user;
GRANT SELECT ON token TO super_user;
GRANT SELECT ON participation TO super_user;
GRANT SELECT ON proposal TO super_user;
