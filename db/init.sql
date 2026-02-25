CREATE TABLE IF NOT EXISTS transactions (
    id               SERIAL PRIMARY KEY,
    transaction_date DATE,
    description      TEXT,
    amount           NUMERIC(15, 2),
    transaction_type VARCHAR(10),
    balance          NUMERIC(15, 2)
);
