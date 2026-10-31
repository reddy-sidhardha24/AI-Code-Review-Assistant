CREATE DATABASE shopdb;

USE shopdb;

CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    price DOUBLE,
    stock INT
);

CREATE TABLE orders (
    id INT PRIMARY KEY,
    product_id INT,
    quantity INT,
    total DOUBLE
);

INSERT INTO products VALUES
(1, 'Laptop', 55000, 10),
(2, 'Mobile', 25000, 20),
(3, 'Headphones', 1500, 30);

INSERT INTO orders(product_id, quantity, total)
VALUES (1, 2, 110000);

UPDATE products
SET stock = stock - 5
WHERE id = 1;

SELECT * FROM products
WHERE name LIKE '%Laptop%';

SELECT * FROM orders
WHERE product_id = 1;

DELETE FROM products;