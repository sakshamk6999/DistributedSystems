import socket
import threading
import argparse
import json
import uuid
import os
import pymysql

CUSTOMER_DB_CONFIG = {
    "host": os.getenv("CUSTOMER_DB_HOST", "0.0.0.0"),
    "port": os.getenv("CUSTOMER_DB_PORT", 8000),
    "user": "root",
    "password": os.getenv("CUSTOMER_DB_PASSWORD", "my-secret-pw"),
    "database": "customer_db",
    "cursorclass": pymysql.cursors.DictCursor
}

PRODUCT_DB_CONFIG = {
    "host": os.getenv("PRODUCT_DB_HOST", "0.0.0.0"),
    "port": os.getenv("PRODUCT_DB_PORT", 8001),
    "user": "root",
    "password": os.getenv("PRODUCT_DB_PASSWORD", "my-secret-pw"),
    "database": "product_db",
    "cursorclass": pymysql.cursors.DictCursor
}

def create_customer_db_connection():
    """Create a new MySQL connection for each thread."""
    try:
        connection = pymysql.connect(**CUSTOMER_DB_CONFIG)
        print(f"Successfully connected to the customer db")
        return connection
    except pymysql.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def create_product_db_connection():
    """Create a new MySQL connection for each thread."""
    try:
        connection = pymysql.connect(**PRODUCT_DB_CONFIG)
        print(f"Successfully connected to the product db")
        return connection
    except pymysql.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def return_session_id(**request_body):
    user_session_id = request_body.get("session_id", None)
    return user_session_id

#Handle account registeration
def handle_account_registeration(**request_body):
    conn = create_customer_db_connection()
    username = request_body.get("username")
    password = request_body.get("password")
    name = request_body.get("name")
    
    with conn.cursor() as cursor:
        try:
            cursor.execute(
                f"INSERT INTO sellers (username, password, name) VALUES (%s, %s, %s)",
                    (username, password, name),
            )

            seller_id = cursor.lastrowid
            print("Seller id", seller_id)
            # cursor.execute(
            #     f"INSERT INTO seller_session (seller_id) VALUES (%s)",
            #     (seller_id)
            # )

            conn.commit()

            return {"status": "OK", "message": f"Buyer created with username: {username}", "id": seller_id}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        finally:
            if "conn" in locals() and conn.open:
                conn.close()

#Handle user login
def handle_login( **request_body):
    conn = create_customer_db_connection()
    username = request_body.get("username")
    password = request_body.get("password")

    with conn.cursor() as cursor:
        try:
            cursor.execute(
                f"SELECT * FROM sellers WHERE username=%s AND password=%s",
                    (username, password),
            )

            user = cursor.fetchone()
            
            if user:
                cursor.execute(
                    f"INSERT INTO seller_session (seller_id) values (%s)",
                    (user['id'])
                )

                session_id = cursor.lastrowid
                conn.commit()
                return {"status": "OK", "message": f"User Login Successful", "session_id": session_id}
            else:
                return {"status": "ERROR", "message": f"User Login Unsuccessful: Invalid Creds"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        finally:
            if "conn" in locals() and conn.open:
                conn.close()

#Handle user logout
def handle_logout(**request_body):
    conn = create_customer_db_connection()
    user_session_id = request_body.get("session_id")

    with conn.cursor() as cursor:
        try:

            cursor.execute(
                f"DELETE FROM seller_session where session_id=%s",
                (user_session_id)
            )
            
            conn.commit()

            return {"status": "OK", "message": f"User Logout Successful"}
        except Exception as e:
                return {"status": "ERROR", "message": str(e)}
        finally:
            if "conn" in locals() and conn.open:
                conn.close()


#Handle user logout
def handle_get_seller_rating(**request_body):
    conn = create_customer_db_connection()
    user_session_id = request_body.get("session_id")

    if user_session_id == None:
        return {"status": "ERROR", "message": "No session id"}
    
    with conn.cursor() as cursor:
        try:
            cursor.execute(
                f"SELECT * FROM seller_session where session_id=%s",
                (user_session_id)
            )

            seller = cursor.fetchone()

            if not seller:
                return {"status": "ERROR", "message": "Invalid session id"}
            
            cursor.execute(
                f"SELECT * FROM sellers where id=%s",
                (seller['seller_id'])
            )
            
            seller = cursor.fetchone()

            return {"status": "OK", "message": f"User Rating Fetched", "thumbs_up": seller['thumbs_up'], "thumbs_down": seller['thumbs_down']}
        except Exception as e:
                return {"status": "ERROR", "message": str(e)}
        finally:
            if "conn" in locals() and conn.open:
                conn.close()

# Register Item for Sale
def handle_register_item_for_sale(**request_body):
    user_conn = create_customer_db_connection()
    prod_conn = create_product_db_connection()
    user_session_id = request_body.get("session_id")

    if user_session_id == None:
        return {"status": "ERROR", "message": "No session id"}
    
    with user_conn.cursor() as cursor:
        try:
            cursor.execute(
                f"SELECT * FROM seller_session where session_id=%s",
                (user_session_id)
            )

            seller = cursor.fetchone()

            if not seller:
                return {"status": "ERROR", "message": "Invalid session id"}
            

            item_name = request_body.get('name')
            category = int(request_body.get('category'))
            keywords = ','.join(request_body.get('keywords'))
            condition_val = int(request_body.get('condition'))
            sale_price = float(request_body.get('sale_price'))
            quantity = int(request_body.get('quantity'))
            
            with prod_conn.cursor() as prod_cursor:
                prod_cursor.execute(
                    f"INSERT INTO items (category, name, keywords, condition_val, sale_price, quantity, seller_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (category, item_name, keywords, condition_val, sale_price, quantity, seller['seller_id'])
                )

                prod_id = prod_cursor.lastrowid
                
                prod_conn.commit()

                return {"status": "OK", "message": "Registered item for sale", "item_id": prod_id}
        except Exception as e:
                return {"status": "ERROR", "message": str(e)}
        finally:
            if "user_conn" in locals() and user_conn.open:
                user_conn.close()
            
            if "prod_conn" in locals() and prod_conn.open:
                prod_conn.close()

# Update Item ID
def handle_update_item_price(**request_body):
    prod_conn = create_product_db_connection()
    user_session_id = request_body.get("session_id")

    if user_session_id == None:
        return {"status": "ERROR", "message": "No session id"}
    
    item_id = request_body.get("item_id")
    new_value = request_body.get("sale_price")
    with prod_conn.cursor() as prod_cursor:
        try:
            prod_cursor.execute(
                "UPDATE items SET sale_price=%s WHERE id=%s",
                (float(new_value), int(item_id))
            )

            prod_conn.commit()

            return {"status": "SUCCESS", "message": "Updated Successfully"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        finally:
            if "prod_conn" in locals() and prod_conn.open:
                prod_conn.close()

# Display items for sale
def handle_display_items_for_sale(**request_body):
    user_conn = create_customer_db_connection()
    prod_conn = create_product_db_connection()

    user_session_id = request_body.get("session_id")

    if user_session_id == None:
        return {"status": "ERROR", "message": "No session id"}
    
    with user_conn.cursor() as cursor:
        try:
            cursor.execute(
                f"SELECT * FROM seller_session where session_id=%s",
                (user_session_id)
            )

            seller = cursor.fetchone()

            if not seller:
                return {"status": "ERROR", "message": "Invalid session id"}
            
            with prod_conn.cursor() as prod_cursor:
                prod_cursor.execute(
                    f"SELECT * from items where seller_id=%s",
                    (seller['seller_id'])
                )

                item = prod_cursor.fetchone()
                

                return {"status": "OK", "message": "Got item for sale", "item": item}
        except Exception as e:
                return {"status": "ERROR", "message": str(e)}
        finally:
            if "user_conn" in locals() and user_conn.open:
                user_conn.close()
            
            if "prod_conn" in locals() and prod_conn.open:
                prod_conn.close()

# Update Item ID
def handle_update_item_quantity(**request_body):
    prod_conn = create_product_db_connection()
    user_session_id = request_body.get("session_id")

    if user_session_id == None:
        return {"status": "ERROR", "message": "No session id"}
    
    item_id = request_body.get("item_id")
    new_value = request_body.get("item_quantity")
    with prod_conn.cursor() as prod_cursor:
        try:
            prod_cursor.execute(
                "UPDATE items SET quantity=%s WHERE id=%s",
                (float(new_value), int(item_id))
            )

            prod_conn.commit()

            return {"status": "ERROR", "message": "Updated Quantity Successfully"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        finally:
            if "prod_conn" in locals() and prod_conn.open:
                prod_conn.close()

            
def handle_client(client_socket, addr):
    print(f"[+] New thread started for {addr[0]}:{addr[1]}")
    db_conn_customer = create_customer_db_connection()
    db_conn_product = create_product_db_connection()

    if not db_conn_product or not db_conn_customer:
        client_socket.sendall(b"Database connection failed. Closing.\n")
        client_socket.close()
        return

    try:
        while True:
            request = client_socket.recv(1024)

            if not request:
                client_socket.close()
                print(f"Connection to client ({addr[0]}:{addr[1]}) closed")
                return
            
            print(f"Received {request}")
            decoded_string = request.decode("utf-8")
            json_object = json.loads(decoded_string)

            print("json decoded is", json_object)

            if json_object['action'] == "REGISTER":
                response = handle_account_registeration(**json_object)
            elif json_object['action'] == "LOGIN":
                response = handle_login(**json_object)
            elif json_object['action'] == "LOGOUT":
                response = handle_logout(**json_object)
            elif json_object['action'] == "GET_RATING":
                response = handle_get_seller_rating(**json_object)
            elif json_object['action'] == "REGISTER_PRODUCT":
                response = handle_register_item_for_sale(**json_object)
            elif json_object['action'] == "CHANGE_ITEM_PRICE":
                response = handle_update_item_price(**json_object)
            elif json_object['action'] == "UPDATE_UNITS_FOR_SALE":
                respons = handle_update_item_quantity(**json_object)
            elif json_object['action'] == "DISPLAY_ITEMS_FOR_SALE":
                response = handle_display_items_for_sale(**json_object)

            json_respond = json.dumps(response)
            data_bytes = json_respond.encode('utf-8')
            # print("THE RESPONSE IS")
            # print(response)
            client_socket.send(data_bytes)
    except Exception as e:
        print(f"Error when hanlding client: {e}")
    finally:
        client_socket.close()
        print(f"Connection to client ({addr[0]}:{addr[1]}) closed")

def run_server(host: str, port: int):
    try:
        print("in the run_server")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        print(f"Listening on port {port} and host {host}")
        while True:
            client_socket, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, addr,))
            thread.start()
    except Exception as e:
        print(f"Error is {e}")
    finally:
        server.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--HOST", type=str, default='0.0.0.0')
    parser.add_argument("--PORT", type=int, default=50001)
    args = parser.parse_args()
    # print("ARGS")
    run_server(args.HOST, args.PORT)

if __name__ == "__main__":
    main()