CREATE TABLE flights (
    id               BIGSERIAL     PRIMARY KEY,
    flight_number    VARCHAR(10)   NOT NULL,
    origin           VARCHAR(3)    NOT NULL,
    destination      VARCHAR(3)    NOT NULL,
    departure_time   TIMESTAMPTZ   NOT NULL,
    arrival_time     TIMESTAMPTZ   NOT NULL,
    departure_date   DATE          NOT NULL,
    total_seats      INT           NOT NULL CHECK (total_seats > 0),
    available_seats  INT           NOT NULL CHECK (available_seats >= 0),
    price            NUMERIC(10,2) NOT NULL CHECK (price > 0),
    status           VARCHAR(20)   NOT NULL DEFAULT 'SCHEDULED',
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CHECK (available_seats <= total_seats)
);

CREATE UNIQUE INDEX uq_flight_number_date
    ON flights (flight_number, departure_date);

CREATE TABLE seat_reservations (
    id          BIGSERIAL   PRIMARY KEY,
    flight_id   BIGINT      NOT NULL REFERENCES flights(id),
    booking_id  UUID        NOT NULL UNIQUE,
    seat_count  INT         NOT NULL CHECK (seat_count > 0),
    status      VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reservations_flight  ON seat_reservations(flight_id);
CREATE INDEX idx_reservations_booking ON seat_reservations(booking_id);
