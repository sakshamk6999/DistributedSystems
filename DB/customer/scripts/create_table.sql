CREATE DATABASE IF NOT EXISTS customer_db;
USE customer_db;

CREATE TABLE IF NOT EXISTS sellers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(32) NOT NULL UNIQUE,
    password VARCHAR(32) NOT NULL,
    name VARCHAR(32) NOT NULL,
    thumbs_up INT DEFAULT 0,
    thumbs_down INT DEFAULT 0,
    items_sold INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS buyers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(32) NOT NULL UNIQUE,
    password VARCHAR(32) NOT NULL,
    name VARCHAR(32) NOT NULL,
    purchases VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS buyer_cart (
  user_id INT PRIMARY KEY,
  items VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS session_cart (
  session_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  items VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS seller_session (
  session_id INT AUTO_INCREMENT PRIMARY KEY,
  seller_id INT NOT NULL
);