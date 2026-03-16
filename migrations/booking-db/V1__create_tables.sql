CREATE TABLE bookings (
    id              UUID           PRIMARY KEY,
    user_id         BIGINT         NOT NULL,
    flight_id       BIGINT         NOT NULL,
    passenger_name  VARCHAR(255)   NOT NULL,
    passenger_email VARCHAR(255)   NOT NULL,
    seat_count      INT            NOT NULL CHECK (seat_count > 0),
    total_price     NUMERIC(10,2)  NOT NULL CHECK (total_price > 0),
    status          VARCHAR(20)    NOT NULL DEFAULT 'CONFIRMED',
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bookings_user   ON bookings(user_id);
CREATE INDEX idx_bookings_flight ON bookings(flight_id);
