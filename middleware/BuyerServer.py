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
        # print(f"Successfully connected to the customer db")
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
        # print(f"Error connecting to MySQL: {err}")
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
                f"INSERT INTO buyers (username, password, name) VALUES (%s, %s, %s)",
                    (username, password, name),
            )

            user_id = cursor.lastrowid

            cursor.execute(
                f"INSERT INTO buyer_cart (user_id, items) VALUES (%s, %s)",
                (user_id, "")
            )

            print("inserted into buyer_cart", user_id)
            # user_id = cursor.lastrowid
            conn.commit()
            
            return {"status": "OK", "message": f"Buyer created with username: {username}", "id": user_id}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        finally:
            if "conn" in locals() and conn.open:
                conn.close()

#Handle user login
def handle_login(**request_body):

    conn = create_customer_db_connection()
    username = request_body.get("username")
    password = request_body.get("password")

    with conn.cursor() as cursor:
        try:
            cursor.execute(
                "SELECT * FROM buyers WHERE username=%s AND password=%s",
                (username, password)
            )

            user = cursor.fetchone()
            print("user", user)
            if user:
                cursor.execute(
                    "SELECT * from buyer_cart where user_id=%s",
                    (int(user['id']))
                )

                cart = cursor.fetchone()
                print("cart", cart)
                cursor.execute(
                    "INSERT INTO session_cart (user_id, items) values (%s, %s)",
                    (user['id'], cart['items'])
                )

                session_id = cursor.lastrowid
                print("session_id", session_id)
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

            cursor.execute(f"DELETE FROM session_cart WHERE session_id={user_session_id}")


            conn.commit()
            
            return {"status": "OK", "message": f"User Logout Successful"}
        except Exception as e:

                return {"status": "ERROR", "message": str(e)}

#Handle Product Search
def handle_product_search(**request_body):
    conn = create_product_db_connection()
    category = request_body.get("category")
    keywords = request_body.get("keywords", [])
    if isinstance(keywords, str):
        keywords = [keywords]
    with conn.cursor() as cursor:
        try:
            query = f"SELECT * FROM items WHERE category={int(category)} AND quantity > 0"
            query_var = [category]

            keyword_query = "" + ' OR '.join(list(map(lambda x: f"keywords LIKE '%{x}%'", keywords)))
            # query_var.extend(keywords)
            if keyword_query != "":
                query += f" AND ({keyword_query})"
            print("query is", query, query_var)
            cursor.execute(query)
            items = cursor.fetchall()
            for item in items:
                item["keywords"] = item["keywords"].split(",") if item["keywords"] else []
            return {"status": "OK", "items": items}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        finally:
            if "conn" in locals() and conn.open:
                conn.close()

# Handle Get Item
def handle_get_item(**request_body):
    conn = create_product_db_connection()
    item_id = request_body.get("item_id")

    with conn.cursor() as cursor:
        try:
            query = "SELECT * FROM items WHERE id=%s"
            query_var = (item_id)

            cursor.execute(query, query_var)
            item = cursor.fetchone()

            return {"status": "OK", "item": item}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        finally:
            if "conn" in locals() and conn.open:
                conn.close()
    

#Add item to cart, 
def handle_add_item_to_cart(**request_body):
    user_conn = create_customer_db_connection()
    product_conn = create_product_db_connection()
    session_id = return_session_id(**request_body)


    if session_id == None:
        return {"status": "ERROR", "message": "No session id"}
    
    # item = {"id": str, "quantity": int}
    item_id = request_body.get("item_id")
    item_quantity = request_body.get("item_quantity")

    with user_conn.cursor() as cursor:
        try:
            cursor.execute(
                f"SELECT * FROM session_cart WHERE session_id=%s",
                (session_id)
            )

            session_items = cursor.fetchone()

            if session_items['items']:
                print("Current session items", session_items['items'])
                session_items = session_items['items'].split(";")
            else:
                session_items = []

            with product_conn.cursor() as product_cursor:
                product_cursor.execute(
                    f"SELECT * FROM items WHERE id=%s and quantity>=%s",
                    (item_id, item_quantity)
                )

                if product_cursor.fetchone():
                    session_items.append(f"{item_id}|{item_quantity}")

                    cursor.execute(
                        f"UPDATE session_cart set items=%s where session_id=%s",
                        (';'.join(session_items), session_id)
                    )
                    user_conn.commit()
                    return {"status": "OK", "message": f"Item {item_id} added to cart with quantity {item_quantity}"}
                else:
                    return {"status": "ERROR", "message": f"Item {item_id} with quantity {item_quantity} not found"}

        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        finally:
            if "user_conn" in locals() and user_conn.open:
                user_conn.close()

            if "product_conn" in locals() and product_conn.open:
                product_conn.close()

# Handle Remove Item from Cart
def handle_remove_item_from_cart(**request_body):
    user_conn = create_customer_db_connection()
    session_id = return_session_id(**request_body)

    if session_id == None:
        return {"status": "ERROR", "message": "No session id"}
    
    item_id = request_body.get("item_id")

    with user_conn.cursor() as cursor:
        try:
            cursor.execute(
                f"SELECT * FROM session_cart where session_id=%s",
                (session_id)
            )
            
            session_items = cursor.fetchone()['items'].split(";")
            updated_items = []
            for i in session_items:
                item, quantity = i.split("|")[0], i.split("|")[1]

                if item != item_id:
                    updated_items.append(f"{item}|{quantity}")
            
                cursor.execute(
                    f"UPDATE session_cart SET items=%s where session_id=%s",
                    (';'.join(updated_items), session_id)
                )

                user_conn.commit()
            return {"status": "OK", "message": f"Item removed successfully from session cart"}
        except Exception as e:
                return {"status": "ERROR", "message": str(e)}


# Save Cart
def handle_save_cart(**request_body):
    user_conn = create_customer_db_connection()
    session_id = return_session_id(**request_body)

    if session_id == None:
        return {"status": "ERROR", "message": "No session id"}

    with user_conn.cursor() as cursor:
        try:
            cursor.execute(
                f"SELECT * from session_cart where session_id=%s",
                (session_id)
            )

            user_cart = cursor.fetchone()

            if not user_cart:
                return {"status": "ERROR", "message": f"Session ID is not correct"}

            cursor.execute(
                f"UPDATE buyer_cart SET items=%s where user_id=%s",
                (user_cart['items'], user_cart['user_id'])
            )
            user_conn.commit()
            return {"status": "OK", "message": f"Cart saved successfully"}
        except Exception as e:
                return {"status": "ERROR", "message": str(e)}

# Handle Clear Cart
def handle_clear_cart(**request_body):
    user_conn = create_customer_db_connection()
    session_id = return_session_id(**request_body)

    if session_id == None:
        return {"status": "ERROR", "message": "No session id"}

    with user_conn.cursor() as cursor:
        try:
            cursor.execute(
                f"UPDATE session_cart SET items=%s where session_id=%s",
                ("", session_id)
            )
            user_conn.commit()
            return {"status": "OK", "message": f"Cart cleared successfully"}
        except Exception as e:
                return {"status": "ERROR", "message": str(e)}

# Handle Display Cart
def handle_display_cart(**request_body):
    user_conn = create_customer_db_connection()
    session_id = return_session_id(**request_body)

    if session_id == None:
        return {"status": "ERROR", "message": "No session id"}

    with user_conn.cursor() as cursor:
        try:
            cursor.execute(
                f"SELECT * from session_cart where session_id=%s",
                (session_id)
            )

            user_cart = cursor.fetchone()

            items = []

            for item in user_cart['items'].split(";"):
                if len(item.split("|")) > 1:
                    items.append({
                        'item_id': item.split("|")[0],
                        'quantity': item.split("|")[1]
                    })
                    # items.append(item.split("|")[0], item.split("|")[1])

            return {"status": "OK", "message": f"Items from current cart successfully fetched", "items": items}
        except Exception as e:
                return {"status": "ERROR", "message": str(e)}

# Handle Provide Feedback
def handle_provide_feedback(**request_body):
    conn = create_product_db_connection()
    session_id = return_session_id(**request_body)

    if session_id == None:
        return {"status": "ERROR", "message": "No session id"}
    
    item_id = request_body.get("item_id")
    feedback = request_body.get("feedback")

    with conn.cursor() as cursor:
        try:
            if feedback == "up":
                query = f"UPDATE items SET thumbs_up = thumbs_up + 1 where id=%s"
            elif feedback == "down":
                query = f"UPDATE items SET thumbs_down = thumbs_down + 1 where id=%s"
            else:
                {"status": "ERROR", "message": "Invalid Feedback"}
            
            cursor.execute(query, (item_id))
            conn.commit()
            return {"status": "OK", "message": "Feedback provided"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        finally:
            if "conn" in locals() and conn.open:
                conn.close()

# Handle Provide Feedback
def handle_get_seller_rating(**request_body):
    conn = create_customer_db_connection()
    session_id = return_session_id(**request_body)

    if session_id == None:
        return {"status": "ERROR", "message": "No session id"}
    
    seller_id = request_body['seller_id']

    with conn.cursor() as cursor:
        try:
            cursor.execute(
                f"SELECT * FROM sellers where id=%s", 
                (seller_id)
            )

            seller = cursor.fetchone()

            if not seller:
                return {"status": "ERROR", "message": "Seller ID invalid"}

            return {"status": "OK", "message": "Seller feedback provided", "thumbs_up": seller["thumbs_up"], "thumbs_down": seller['thumbs_down']}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        finally:
            if "conn" in locals() and conn.open:
                conn.close()

# Handle Buyer Purchases
def handle_get_buyer_purchases(**request_body):
    conn = create_customer_db_connection()
    session_id = return_session_id(**request_body)

    if session_id == None:
        return {"status": "ERROR", "message": "No session id"}

    with conn.cursor() as cursor:
        try:
            cursor.execute(
                f"SELECT * FROM session_cart where session_id=%s", 
                (session_id)
            )

            buyer = cursor.fetchone()

            if not buyer:
                return {"status": "ERROR", "message": "buyer ID invalid"}

            user_id = buyer['user_id']

            cursor.execute(
                f"SELECT * FROM buyers where id=%s", 
                (user_id)
            )

            buyer_info = cursor.fetchone()

            if not buyer_info:
                return {"status": "ERROR", "message": "buyer ID invalid"}
            
            return {"status": "OK", "message": "Buyer purchases are provided", "purchases": buyer_info['purchases']}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        finally:
            if "conn" in locals() and conn.open:
                conn.close()



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
            # print(f"Received {request}")
            decoded_string = request.decode("utf-8")
            json_object = json.loads(decoded_string)

            # print("json decoded is", json_object)

            if json_object['action'] == "REGISTER":
                response = handle_account_registeration(**json_object)
            elif json_object['action'] == "LOGIN":
                response = handle_login(**json_object)
            elif json_object['action'] == "LOGOUT":
                response = handle_logout(**json_object)
            elif json_object['action'] == "PRODUCT_SEARCH":
                response = handle_product_search(**json_object)
            elif json_object['action'] == "ADD_ITEM":
                response = handle_add_item_to_cart(**json_object)
            elif json_object['action'] == "GET_ITEM":
                response = handle_get_item(**json_object)
            elif json_object['action'] == "REMOVE_ITEM":
                response = handle_remove_item_from_cart(**json_object)
            elif json_object['action'] == "SAVE_CART":
                response = handle_save_cart(**json_object)
            elif json_object['action'] == "CLEAR_CART":
                response = handle_clear_cart(**json_object)
            elif json_object['action'] == "DISPLAY_CART":
                response = handle_display_cart(**json_object)
            elif json_object['action'] == "PROVIDE_FEEDBACK":
                response = handle_provide_feedback(**json_object)
            elif json_object['action'] == "GET_SELLER_RATING":
                response = handle_get_seller_rating(**json_object)
            elif json_object['action'] == "GET_BUYER_PURCHASES":
                response = handle_get_buyer_purchases(**json_object)
            elif json_object['action'] == "DISCONNECT":
                client_socket.close()
                print(f"Connection to client ({addr[0]}:{addr[1]}) closed")

            json_respond = json.dumps(response)
            data_bytes = json_respond.encode('utf-8')
            # length prefix => at the start, we can signify the length 
            # DB Locks
            # Asyncio   
            #
            # print("THE RESPONSE IS")
            # print(response)
            client_socket.sendall(data_bytes)
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
    parser.add_argument("--PORT", type=int, default=50000)
    args = parser.parse_args()
    # print("ARGS")
    run_server(args.HOST, args.PORT)

if __name__ == "__main__":
    main()