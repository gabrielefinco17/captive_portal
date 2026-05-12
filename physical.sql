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
    preference INT NOT NULL,

    PRIMARY KEY (account_email, proposal_id),

    CONSTRAINT preference_options
        CHECK (preference IN ( 0, 1, 2)),

    CONSTRAINT fk_account_email
        FOREIGN KEY (account_email)
        REFERENCES account(email),

    CONSTRAINT fk_proposal_id
        FOREIGN KEY (proposal_id)
        REFERENCES proposal(id)
);


-- --------------------------------- ROLES ---------------------------------

CREATE ROLE teacher LOGIN PASSWORD 'praga';
GRANT SELECT ON meeting, proposal, account TO teacher;
GRANT SELECT, INSERT ON participation TO teacher;
GRANT SELECT, INSERT ON vote TO teacher;

-- CREATE ROLE secretary LOGIN PASSWORD 'praga';
-- GRANT SELECT ON meeting, account TO secretary;
-- GRANT SELECT, INSERT ON participation TO secretary;
-- GRANT SELECT, INSERT, UPDATE (title, proposal_description, attachment) ON proposal TO secretary;
-- GRANT USAGE ON SEQUENCE proposal_id_seq TO secretary;   -- fundamental for INSERT INTO
-- GRANT SELECT, INSERT ON token TO secretary;


CREATE ROLE principal LOGIN PASSWORD 'praga';
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO principal;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO principal;



--------------------------------------------------
--         QUERY DI TEST PER FILLARE IL DB
--------------------------------------------------


-- 1. Inserimento degli Account (docenti, verbalisti, dirigenti)
INSERT INTO account (email, user_name, user_surname, user_role, department) VALUES
('mario.rossi@scuola.it', 'Mario', 'Rossi', 'dirigente', 'Presidenza'),
('luigi.verdi@scuola.it', 'Luigi', 'Verdi', 'verbalista', 'Segreteria'),
('giulia.bianchi@scuola.it', 'Giulia', 'Bianchi', 'docente', 'Matematica'),
('anna.neri@scuola.it', 'Anna', 'Neri', 'docente', 'Lettere'),
('paolo.gialli@scuola.it', 'Paolo', 'Gialli', 'docente', 'Scienze');

-- 2. Inserimento di un Meeting (Riunione)
-- Nota: 'id' è SERIAL, quindi si autoincrementerà a partire da 1 (se la tabella è vuota).
INSERT INTO meeting (meeting_date, start_time, end_time, participant_count, president_email) VALUES
('2026-06-10', '10:00:00', '12:00:00', 4, 'mario.rossi@scuola.it'),
('2026-06-15', '14:30:00', '16:00:00', 0, 'mario.rossi@scuola.it');

-- 3. Inserimento delle Proposal (Proposte) associate al meeting
-- Assumiamo che gli ID dei meeting creati sopra siano 1 e 2.
INSERT INTO proposal (title, proposal_description, attachment, meeting_id) VALUES
('Approvazione Bilancio', 'Discussione e approvazione del bilancio preventivo per il prossimo anno.', 'bilancio_2027.pdf', 1),
('Gite Scolastiche', 'Definizione delle mete per le gite delle classi quinte.', NULL, 1),
('Adozione Libri', 'Scelta dei libri di testo per le materie scientifiche.', 'elenco_libri.pdf', 2);

-- 4. Inserimento delle Partecipazioni (Participation)
-- Rappresentano chi partecipa (o dovrebbe partecipare) a quale meeting
INSERT INTO participation (meeting_id, user_email, vote) VALUES
(1, 'mario.rossi@scuola.it', TRUE),
(1, 'luigi.verdi@scuola.it', TRUE),
(1, 'giulia.bianchi@scuola.it', FALSE),
(1, 'anna.neri@scuola.it', TRUE),
(2, 'paolo.gialli@scuola.it', FALSE);

-- 5. Inserimento dei Token di accesso
-- Ricorda il check: expires_at > generated_at
INSERT INTO token (code, generated_at, expires_at, user_email, meeting_id) VALUES
('tok_123abc', '2026-06-10 09:30:00', '2026-06-10 13:00:00', 'giulia.bianchi@scuola.it', 1),
('tok_456def', '2026-06-10 09:30:00', '2026-06-10 13:00:00', 'anna.neri@scuola.it', 1),
('tok_789ghi', '2026-06-15 14:00:00', '2026-06-15 16:30:00', 'paolo.gialli@scuola.it', 2);

-- 6. Inserimento dei Voti (Vote) sulle proposte
-- Assumiamo che le proposal inserite in precedenza abbiano ID 1, 2 e 3.
-- Le preferenze ammesse dal vincolo sono (0, 1, 2). Es: 0=Astenuto, 1=Favorevole, 2=Contrario
INSERT INTO vote (account_email, proposal_id, preference) VALUES
('mario.rossi@scuola.it', 1, 1),
('luigi.verdi@scuola.it', 1, 1),
('anna.neri@scuola.it', 1, 2),
('mario.rossi@scuola.it', 2, 1),
('luigi.verdi@scuola.it', 2, 0),
('anna.neri@scuola.it', 2, 1);