ALTER TABLE order_tracking
MODIFY COLUMN order_id INT NOT NULL AUTO_INCREMENT;

DROP PROCEDURE IF EXISTS create_order_entry;
DROP PROCEDURE IF EXISTS insert_order_item;

DELIMITER $$

CREATE PROCEDURE create_order_entry(
    IN p_status VARCHAR(255),
    OUT p_order_id INT
)
BEGIN
    INSERT INTO order_tracking (status)
    VALUES (p_status);

    SET p_order_id = LAST_INSERT_ID();
END $$

CREATE PROCEDURE insert_order_item(
    IN p_food_item VARCHAR(255),
    IN p_quantity INT,
    IN p_order_id INT
)
BEGIN
    DECLARE v_item_id INT;
    DECLARE v_price DECIMAL(10, 2);
    DECLARE v_total_price DECIMAL(10, 2);

    SELECT item_id, price
    INTO v_item_id, v_price
    FROM food_items
    WHERE name = p_food_item
    LIMIT 1;

    IF v_item_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Food item not found';
    END IF;

    SET v_total_price = v_price * p_quantity;

    INSERT INTO orders (order_id, item_id, quantity, total_price)
    VALUES (p_order_id, v_item_id, p_quantity, v_total_price);
END $$

DELIMITER ;
