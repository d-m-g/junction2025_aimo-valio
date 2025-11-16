-- Создаем таблицу заказов
CREATE TABLE IF NOT EXISTS orders (
    order_id        VARCHAR(50) PRIMARY KEY,
    customer_id     VARCHAR(50) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL,
    delivery_date   DATE NOT NULL,
    phone           VARCHAR(50),
    email           VARCHAR(255),
    language        VARCHAR(10)
);

-- Таблица позиций заказа
CREATE TABLE IF NOT EXISTS order_items (
    id              SERIAL PRIMARY KEY,
    order_id        VARCHAR(50) NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    line_id         INT NOT NULL,
    product_code    VARCHAR(50) NOT NULL,
    name            VARCHAR(255) NOT NULL,
    qty             NUMERIC(12, 2) NOT NULL,
    unit            VARCHAR(10) NOT NULL,
    short_pick      BOOLEAN NOT NULL DEFAULT FALSE
);

ALTER TABLE order_items
    ADD COLUMN IF NOT EXISTS short_pick BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS warehouse_items (
    line_id      INT PRIMARY KEY,           -- тех. ID товара на складе
    product_code VARCHAR(50) NOT NULL,      -- артикул / код товара
    name         VARCHAR(255) NOT NULL,     -- название
    qty          NUMERIC(12, 2) NOT NULL,   -- количество на складе
    unit         VARCHAR(10) NOT NULL       -- единица измерения, например 'ST'
);

-- Пример: вставляем твой заказ
INSERT INTO orders (
    order_id,
    customer_id,
    created_at,
    delivery_date,
    phone,
    email,
    language
) VALUES (
    '10000000',
    '33258',
    '2024-09-01T00:03:36Z',
    '2024-09-02',
    '+358401234567',
    'chef@example.com',
    'fi'
) ON CONFLICT (order_id) DO NOTHING;

INSERT INTO order_items (
    order_id,
    line_id,
    product_code,
    name,
    qty,
    unit
) VALUES (
    '10000000',
    1,
    '6407850050058',
    'Mestari Forsman Lasagne 3kg',
    5.0,
    'RAS'
) ON CONFLICT DO NOTHING;


