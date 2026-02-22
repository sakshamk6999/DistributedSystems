from concurrent import futures
from google.cloud.sql.connector import Connector
import grpc
import customer_db_pb2
import customer_db_pb2_grpc
import os
import json
import logging
import pymysql

CUSTOMER_DB_CONFIG = {
    "host": os.getenv("CUSTOMER_DB_HOST", "136.116.96.33"),
    "port": os.getenv("CUSTOMER_DB_PORT", 3306),
    "user": "root",
    "password": os.getenv("CUSTOMER_DB_PASSWORD", "Customer-db-1"),
    "database": "customer_db",
    "cursorclass": pymysql.cursors.DictCursor
}

connector = Connector()
INSTANCE_CONNECTION_NAME = "distributedsystemsassignments:us-central1-c:customer-db-1"

def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user="root",
        password="Customer-db-1",
        db="customer_db"
    )
    return conn

def create_customer_db_connection():
    """Create a new MySQL connection for each thread."""
    try:
        # connection = pymysql.connect(**CUSTOMER_DB_CONFIG)
        # # print(f"Successfully connected to the customer db")
        # return connection
        return getconn()
    except pymysql.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def setup_databses():
    conn = create_customer_db_connection()
    with conn.cursor() as cursor:
        print("creating sellers table")

        cursor.execute(f'''
CREATE TABLE IF NOT EXISTS sellers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(32) NOT NULL UNIQUE,
    password VARCHAR(32) NOT NULL,
    name VARCHAR(32) NOT NULL,
    thumbs_up INT DEFAULT 0,
    thumbs_down INT DEFAULT 0,
    items_sold INT DEFAULT 0
);
''')
        conn.commit()

        print("created sellers")

def return_session_id(request_body):
    user_session_id = request_body.session_id
    return user_session_id

class BuyerDBService(customer_db_pb2_grpc.CustomerDBServicer):
    def Register(self, request, context):
        conn = create_customer_db_connection()
        username = request.username
        password = request.password
        name = request.name

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
                return customer_db_pb2.RegisterResponse(status=customer_db_pb2.Status.OK, message=f"Buyer created with username: {username}", id= user_id)
            except Exception as e:
                return customer_db_pb2.RegisterResponse(status=customer_db_pb2.Status.ERROR, message=str(e))
            finally:
                if "conn" in locals() and conn.open:
                    conn.close()
    
    def Login(self, request, context):
        conn = create_customer_db_connection()
        username = request.username
        password = request.password

        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    "SELECT * FROM buyers WHERE username=%s AND password=%s",
                    (username, password)
                )

                user = cursor.fetchone()
                # print("user", user)
                if user:
                    cursor.execute(
                        "SELECT * from buyer_cart where user_id=%s",
                        (int(user['id']))
                    )

                    cart = cursor.fetchone()
                    # print("cart", cart)
                    cursor.execute(
                        "INSERT INTO session_cart (user_id, items) values (%s, %s)",
                        (user['id'], cart['items'])
                    )

                    session_id = cursor.lastrowid

                    conn.commit()
                    return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.OK, message="User Login Successful", session_id=session_id)
                else:
                    return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.ERROR, message="User Login Unsuccessful: Invalid Creds")
            except Exception as e:
                return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.ERROR, message=str(e))
            finally:
                if "conn" in locals() and conn.open:
                    conn.close()
    
    def ProductSearch(self, request, context):
        conn = create_customer_db_connection()
        category = request.category
        keywords = request.keywords

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
                # return {"status": "OK", "items": items}
                return customer_db_pb2.ProductSearchResponse(status=customer_db_pb2.Status.OK, **items[0])
            except Exception as e:
                # return {"status": "ERROR", "message": str(e)}
                return customer_db_pb2.ProductSearchResponse(status=customer_db_pb2.Status.ERROR)
            finally:
                if "conn" in locals() and conn.open:
                    conn.close()
    
    # def GetItem(self, request: customer_db_pb2.GetItemRequest, context):
    #     conn = create_product_db_connection()
    #     item_id = request.item_id

    #     with conn.cursor() as cursor:
    #         try:
    #             query = "SELECT * FROM items WHERE id=%s"
    #             query_var = (item_id)

    #             cursor.execute(query, query_var)
    #             item = cursor.fetchone()

    #             return customer_db_pb2.GetItemResponse(**item)
    #         except Exception as e:
    #             # return {"status": "ERROR", "message": str(e)}
    #             return customer_db_pb2.GetItemResponse(**item)
    #         finally:
    #             if "conn" in locals() and conn.open:
    #                 conn.close()

    # def AddItemToCart(self, request: customer_db_pb2.AddItemToCartRequest, context):
    #     user_conn = create_customer_db_connection()
    #     product_conn = create_product_db_connection()
    #     session_id = return_session_id(request)

    #     if session_id == None:
    #         return customer_db_pb2.AddItemToCartResponse(status=customer_db_pb2.Status.ERROR)
        
    #     item_id = request.item_id
    #     item_quantity = request.item_quantity

    #     with user_conn.cursor() as cursor:
    #         try:
    #             cursor.execute(
    #                 f"SELECT * FROM session_cart WHERE session_id=%s",
    #                 (session_id)
    #             )

    #             session_items = cursor.fetchone()

    #             if session_items['items']:
    #                 # print("Current session items", session_items['items'])
    #                 session_items = session_items['items'].split(";")
    #             else:
    #                 session_items = []

    #             with product_conn.cursor() as product_cursor:
    #                 product_cursor.execute(
    #                     f"SELECT * FROM items WHERE id=%s and quantity>=%s",
    #                     (item_id, item_quantity)
    #                 )

    #                 if product_cursor.fetchone():
    #                     session_items.append(f"{item_id}|{item_quantity}")

    #                     cursor.execute(
    #                         f"UPDATE session_cart set items=%s where session_id=%s",
    #                         (';'.join(session_items), session_id)
    #                     )
    #                     user_conn.commit()
    #                     # return {"status": "OK", "message": f"Item {item_id} added to cart with quantity {item_quantity}"}
    #                     return customer_db_pb2.AddItemToCartResponse(status=customer_db_pb2.Status.OK, message= f"Item {item_id} added to cart with quantity {item_quantity}")
    #                 else:
    #                     # return {"status": "ERROR", "message": f"Item {item_id} with quantity {item_quantity} not found"}
    #                     return customer_db_pb2.AddItemToCartResponse(status=customer_db_pb2.Status.ERROR, message= f"Item {item_id} with quantity {item_quantity} not found")

    #         except Exception as e:
    #             # return {"status": "ERROR", "message": str(e)}
    #             return customer_db_pb2.AddItemToCartResponse(status=customer_db_pb2.Status.ERROR, message= str(e))
    #         finally:
    #             if "user_conn" in locals() and user_conn.open:
    #                 user_conn.close()

    #             if "product_conn" in locals() and product_conn.open:
    #                 product_conn.close()
    
    def RemoveItemFromCart(self, request: customer_db_pb2.RemoveItemFromCartRequest, context):
        user_conn = create_customer_db_connection()
        session_id = return_session_id(request)

        if session_id == None:
            return {"status": "ERROR", "message": "No session id"}
        
        item_id = request.item_id

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
                # return {"status": "OK", "message": f"Item removed successfully from session cart"}
                return customer_db_pb2.RemoveItemFromCartResponse(status=customer_db_pb2.Status.OK, message=f"Item removed successfully from session cart")
            except Exception as e:
                    # return {"status": "ERROR", "message": str(e)}
                return customer_db_pb2.RemoveItemFromCartResponse(status=customer_db_pb2.ERROR, message=str(e))
    
    def SaveCart(self, request: customer_db_pb2.UserRequest, context):
        user_conn = create_customer_db_connection()
        session_id = return_session_id(request)

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
                    # return {"status": "ERROR", "message": f"Session ID is not correct"}
                    return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.ERROR, message=f"Session ID is not correct")

                cursor.execute(
                    f"UPDATE buyer_cart SET items=%s where user_id=%s",
                    (user_cart['items'], user_cart['user_id'])
                )
                user_conn.commit()
                # return {"status": "OK", "message": f"Cart saved successfully"}
                return customer_db_pb2.SaveCartResponse(status=customer_db_pb2.Status.OK, message=f"Cart saved successfully")
            except Exception as e:
                    # return {"status": "ERROR", "message": str(e)}
                return customer_db_pb2.SaveCartResponse(status=customer_db_pb2.Status.ERROR, message=str(e))
    
    def ClearCart(self, request, context):
        user_conn = create_customer_db_connection()
        session_id = return_session_id(request)

        if session_id == None:
            # return {"status": "ERROR", "message": "No session id"}
            return customer_db_pb2.ClearCartResponse(status=customer_db_pb2.Status.ERROR, message=f"Session ID is not correct")

        with user_conn.cursor() as cursor:
            try:
                cursor.execute(
                    f"UPDATE session_cart SET items=%s where session_id=%s",
                    ("", session_id)
                )
                user_conn.commit()
                # return {"status": "OK", "message": f"Cart cleared successfully"}
                return customer_db_pb2.ClearCartResponse(status=customer_db_pb2.Status.OK, message=f"Cart cleared successfully")
            except Exception as e:
                    # return {"status": "ERROR", "message": str(e)}
                return customer_db_pb2.ClearCartResponse(status=customer_db_pb2.Status.ERROR, message=str(e))
    
    def DisplayCart(self, request, context):
        user_conn = create_customer_db_connection()
        session_id = return_session_id(request)

        if session_id == None:
            # return {"status": "ERROR", "message": "No session id"}
            return customer_db_pb2.DisplayCartResponse(status=customer_db_pb2.Status.ERROR, message="No session id")

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

                # return {"status": "OK", "message": f"Items from current cart successfully fetched", "items": items}
                return customer_db_pb2.DisplayCartResponse(status=customer_db_pb2.Status.OK, items=items)
            except Exception as e:
                    # return {"status": "ERROR", "message": str(e)}
                return customer_db_pb2.DisplayCartResponse(status=customer_db_pb2.Status.ERROR, message=str(e))


def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    customer_db_pb2_grpc.add_CustomerDBServicer_to_server(
        BuyerDBService(), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    print("creating database")
    setup_databses()
    serve()
