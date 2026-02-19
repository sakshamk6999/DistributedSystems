CREATE DATABASE IF NOT EXISTS product_db;
USE product_db;

CREATE TABLE IF NOT EXISTS items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seller_id INT NOT NULL,
    category INT NOT NULL,
    name VARCHAR(32) NOT NULL,
    keywords VARCHAR(255),
    condition_val INT NOT NULL,
    sale_price FLOAT NOT NULL,
    quantity INT NOT NULL,
    thumbs_up INT DEFAULT 0,
    thumbs_down INT DEFAULT 0
);