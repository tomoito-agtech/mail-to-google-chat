CREATE TABLE received_mails (
    id IDENTITY PRIMARY KEY,
    received_dt TIMESTAMP,
    received_account VARCHAR(255),
    subject VARCHAR(255),
    body LONGVARCHAR,
    created_at TIMESTAMP
);