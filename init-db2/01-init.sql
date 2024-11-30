-- Create schemas
CREATE SCHEMA sales;
COMMENT ON SCHEMA sales IS 'Schema for sales-related tables';

-- Create customers table
CREATE TABLE sales.customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sales.customers IS 'Stores customer information';
COMMENT ON COLUMN sales.customers.customer_id IS 'Primary key for customers';
COMMENT ON COLUMN sales.customers.first_name IS 'Customer first name';
COMMENT ON COLUMN sales.customers.last_name IS 'Customer last name';
COMMENT ON COLUMN sales.customers.email IS 'Customer email address';
COMMENT ON COLUMN sales.customers.phone IS 'Customer phone number';
COMMENT ON COLUMN sales.customers.address IS 'Customer shipping address';

-- Create products table
CREATE TABLE sales.products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    description TEXT,
    price NUMERIC(10,2) NOT NULL,
    stock_quantity INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sales.products IS 'Stores product information';
COMMENT ON COLUMN sales.products.product_id IS 'Primary key for products';
COMMENT ON COLUMN sales.products.product_name IS 'Name of the product';
COMMENT ON COLUMN sales.products.description IS 'Product description';
COMMENT ON COLUMN sales.products.price IS 'Product unit price';
COMMENT ON COLUMN sales.products.stock_quantity IS 'Current stock quantity';

-- Create orders table
CREATE TABLE sales.orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES sales.customers(customer_id),
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(12,2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sales.orders IS 'Stores order information';
COMMENT ON COLUMN sales.orders.order_id IS 'Primary key for orders';
COMMENT ON COLUMN sales.orders.customer_id IS 'Foreign key to customers table';
COMMENT ON COLUMN sales.orders.order_date IS 'Date when order was placed';
COMMENT ON COLUMN sales.orders.total_amount IS 'Total order amount';
COMMENT ON COLUMN sales.orders.status IS 'Current order status';

-- Create order_items table
CREATE TABLE sales.order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES sales.orders(order_id),
    product_id INTEGER REFERENCES sales.products(product_id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sales.order_items IS 'Stores order line items';
COMMENT ON COLUMN sales.order_items.order_item_id IS 'Primary key for order items';
COMMENT ON COLUMN sales.order_items.order_id IS 'Foreign key to orders table';
COMMENT ON COLUMN sales.order_items.product_id IS 'Foreign key to products table';
COMMENT ON COLUMN sales.order_items.quantity IS 'Quantity ordered';
COMMENT ON COLUMN sales.order_items.unit_price IS 'Price per unit at time of order';

-- Insert sample data
INSERT INTO sales.customers (first_name, last_name, email, phone, address) VALUES
    ('Sarah', 'Connor', 'sarah.connor@example.com', '555-0100', '123 Main St'),
    ('James', 'Cameron', 'james.cameron@example.com', '555-0101', '456 Oak Ave'),
    ('Ellen', 'Ripley', 'ellen.ripley@example.com', '555-0102', '789 Pine Rd');

INSERT INTO sales.products (product_name, description, price, stock_quantity) VALUES
    ('Laptop', 'High-performance laptop', 1299.99, 50),
    ('Smartphone', 'Latest model smartphone', 799.99, 100),
    ('Tablet', '10-inch tablet', 499.99, 75),
    ('Headphones', 'Wireless noise-canceling headphones', 199.99, 200);

INSERT INTO sales.orders (customer_id, total_amount, status) VALUES
    (1, 2099.98, 'completed'),
    (2, 799.99, 'processing'),
    (3, 699.98, 'completed');

INSERT INTO sales.order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 1299.99),
    (1, 2, 1, 799.99),
    (2, 2, 1, 799.99),
    (3, 3, 1, 499.99),
    (3, 4, 1, 199.99);

-- Create indexes
CREATE INDEX idx_orders_customer ON sales.orders(customer_id);
CREATE INDEX idx_order_items_order ON sales.order_items(order_id);
CREATE INDEX idx_order_items_product ON sales.order_items(product_id);
