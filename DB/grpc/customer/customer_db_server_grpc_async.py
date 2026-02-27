import asyncio
import logging
import sqlalchemy
import grpc
from grpc import aio
from concurrent import futures
from google.cloud.sql.connector import Connector

# Generated proto imports
import customer_db_pb2
import customer_db_pb2_grpc

# 1. Setup Connector and Engine
connector = Connector()

INSTANCE_CONNECTION_NAME = "distributedsystemsassi:us-central1:customer-db-1"
INSTANCE_PRODUCT = "distributedsystemsassi:us-central1:product-db-1"

def getconn_customer():
    return connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user="saksham_user",
        password="Customer-db-1",
        db="customer_db"
    )

def getconn_product():
    return connector.connect(
        INSTANCE_PRODUCT, 
        "pymysql", 
        user="saksham_user", 
        password="Product-db-1", 
        db="product_db"
    )

pool_customer = sqlalchemy.create_engine("mysql+pymysql://", creator=getconn_customer)
pool_product = sqlalchemy.create_engine("mysql+pymysql://", creator=getconn_product)

def setup_databases():
    with pool_customer.begin() as conn:
        print("Initializing Customer Database tables...")
        tables = [
            'CREATE TABLE IF NOT EXISTS sellers (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(32) NOT NULL UNIQUE, password VARCHAR(32) NOT NULL, name VARCHAR(32) NOT NULL, thumbs_up INT DEFAULT 0, thumbs_down INT DEFAULT 0, items_sold INT DEFAULT 0)',
            'CREATE TABLE IF NOT EXISTS buyers (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(32) NOT NULL UNIQUE, password VARCHAR(32) NOT NULL, name VARCHAR(32) NOT NULL)',
            'CREATE TABLE IF NOT EXISTS purchases (purchase_id INT AUTO_INCREMENT PRIMARY KEY, buyer_id INT NOT NULL, item_id INT NOT NULL, quantity INT NOT NULL, purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
            'CREATE TABLE IF NOT EXISTS buyer_cart (user_id INT PRIMARY KEY, items VARCHAR(255))',
            'CREATE TABLE IF NOT EXISTS session_cart (session_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, items VARCHAR(255))',
            'CREATE TABLE IF NOT EXISTS seller_session (session_id INT AUTO_INCREMENT PRIMARY KEY, seller_id INT NOT NULL, items VARCHAR(255))'
        ]
        for table_sql in tables:
            conn.execute(sqlalchemy.text(table_sql))

    with pool_product.begin() as conn:
        print("Initializing Product Database tables...")
        conn.execute(sqlalchemy.text('''
            CREATE TABLE IF NOT EXISTS items (
                id INT AUTO_INCREMENT PRIMARY KEY, seller_id INT NOT NULL, category INT NOT NULL,
                name VARCHAR(32) NOT NULL, keywords VARCHAR(255), condition_val INT NOT NULL,
                sale_price FLOAT NOT NULL, quantity INT NOT NULL, thumbs_up INT DEFAULT 0, thumbs_down INT DEFAULT 0
            )
        '''))

class BuyerDBService(customer_db_pb2_grpc.CustomerDBServicer):
    
    async def Register(self, request, context):
        try:
            with pool_customer.begin() as conn:
                if request.customer_type == customer_db_pb2.CustomerType.BUYER:
                    result = conn.execute(
                        sqlalchemy.text("INSERT INTO buyers (username, password, name) VALUES (:u, :p, :n)"),
                        {"u": request.username, "p": request.password, "n": request.name}
                    )
                    user_id = result.lastrowid
                    conn.execute(
                        sqlalchemy.text("INSERT INTO buyer_cart (user_id, items) VALUES (:id, :items)"),
                        {"id": user_id, "items": ""}
                    )
                    return customer_db_pb2.RegisterResponse(status=customer_db_pb2.Status.OK, message=f"Buyer created", id=int(user_id))
                else:
                    result = conn.execute(
                        sqlalchemy.text("INSERT INTO sellers (username, password, name) VALUES (:u, :p, :n)"),
                        {"u": request.username, "p": request.password, "n": request.name}
                    )
                    return customer_db_pb2.RegisterResponse(status=customer_db_pb2.Status.OK, message=f"Seller created", id=int(result.lastrowid))
        except Exception as e:
            return customer_db_pb2.RegisterResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    async def Login(self, request, context):
        try:
            with pool_customer.begin() as conn:
                table = "buyers" if request.customer_type == customer_db_pb2.CustomerType.BUYER else "sellers"
                user_res = conn.execute(
                    sqlalchemy.text(f"SELECT * FROM {table} WHERE username=:u AND password=:p"),
                    {"u": request.username, "p": request.password}
                ).mappings().fetchone()

                if user_res:
                    session_table = "session_cart" if request.customer_type == customer_db_pb2.CustomerType.BUYER else "seller_session"
                    items_val = ""
                    if request.customer_type == customer_db_pb2.CustomerType.BUYER:
                        cart = conn.execute(sqlalchemy.text("SELECT items FROM buyer_cart WHERE user_id=:id"), {"id": user_res['id']}).mappings().fetchone()
                        items_val = cart['items'] if cart else ""

                    session_res = conn.execute(
                        sqlalchemy.text(f"INSERT INTO {session_table} ({'user_id' if table=='buyers' else 'seller_id'}, items) VALUES (:uid, :items)"),
                        {"uid": user_res['id'], "items": items_val}
                    )
                    return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.OK, message="Login Successful", session_id=session_res.lastrowid)
                return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.ERROR, message="Invalid Credentials")
        except Exception as e:
            return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    async def Logout(self, request, context):
        try:
            table = "session_cart" if request.customer_type == customer_db_pb2.CustomerType.BUYER else "seller_session"
            with pool_customer.begin() as conn:
                conn.execute(sqlalchemy.text(f"DELETE FROM {table} WHERE session_id=:sid"), {"sid": request.session_id})
                return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.OK, message="Logout Successful")
        except Exception as e:
            return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    async def ProductSearch(self, request, context):
        try:
            with pool_product.connect() as conn:
                query_str = "SELECT * FROM items WHERE category=:cat AND quantity > 0"
                params = {"cat": request.category}
                if request.keywords:
                    conditions = [f"keywords LIKE :kw{i}" for i, _ in enumerate(request.keywords)]
                    for i, kw in enumerate(request.keywords): params[f"kw{i}"] = f"%{kw}%"
                    query_str += " AND (" + " OR ".join(conditions) + ")"
                
                result = conn.execute(sqlalchemy.text(query_str), params).mappings().all()
                items = []
                for r in result:
                    item = dict(r)
                    item["keywords"] = item["keywords"].split(",") if item["keywords"] else []
                    items.append(item)
                return customer_db_pb2.ListProductResponse(status=customer_db_pb2.Status.OK, items=items)
        except Exception as e:
            return customer_db_pb2.ListProductResponse(status=customer_db_pb2.Status.ERROR)

    async def ClearCart(self, request, context):
        try:
            with pool_customer.begin() as conn:
                res = conn.execute(sqlalchemy.text("SELECT user_id FROM session_cart WHERE session_id = :sid"), {"sid": request.session_id}).mappings().fetchone()
                if res:
                    conn.execute(sqlalchemy.text("UPDATE session_cart SET items='' WHERE user_id = :uid"), {"uid": res['user_id']})
                return customer_db_pb2.ClearCartResponse(status=customer_db_pb2.Status.OK, message="Cart cleared")
        except Exception as e:
            return customer_db_pb2.ClearCartResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    async def DisplayCart(self, request, context):
        try:
            with pool_customer.connect() as conn:
                res = conn.execute(sqlalchemy.text("SELECT items FROM session_cart WHERE session_id = :sid"), {"sid": request.session_id}).mappings().fetchone()
                if not res: return customer_db_pb2.DisplayCartResponse(status=customer_db_pb2.Status.ERROR, message="Session not found")
                
                items_list = []
                raw_items = res['items'].split(";") if res['items'] else []
                for entry in raw_items:
                    if "|" in entry:
                        i_id, i_qty = entry.split("|")
                        items_list.append({'item_id': int(i_id), 'quantity': int(i_qty)})
                return customer_db_pb2.DisplayCartResponse(status=customer_db_pb2.Status.OK, items=items_list)
        except Exception as e:
            return customer_db_pb2.DisplayCartResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    async def AddItemToCart(self, request, context):
        try:
            with pool_product.connect() as prod_conn:
                product = prod_conn.execute(sqlalchemy.text("SELECT id FROM items WHERE id = :id AND quantity >= :qty"),
                    {"id": request.item_id, "qty": request.item_quantity}).mappings().fetchone()
                if not product: return customer_db_pb2.AddItemToCartResponse(status=customer_db_pb2.Status.ERROR, message="Unavailable")

            with pool_customer.begin() as cust_conn:
                res = cust_conn.execute(sqlalchemy.text("SELECT items FROM session_cart WHERE session_id = :sid"), {"sid": request.session_id}).mappings().fetchone()
                if not res: return customer_db_pb2.AddItemToCartResponse(status=customer_db_pb2.Status.ERROR, message="Invalid Session")
                
                updated_items = (res['items'] + ";" if res['items'] else "") + f"{request.item_id}|{request.item_quantity}"
                cust_conn.execute(sqlalchemy.text("UPDATE session_cart SET items = :items WHERE session_id = :sid"), {"items": updated_items, "sid": request.session_id})
                return customer_db_pb2.AddItemToCartResponse(status=customer_db_pb2.Status.OK, message="Added to cart")
        except Exception as e:
            return customer_db_pb2.AddItemToCartResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    async def MakePurchase(self, request, context):
        try:
            with pool_customer.connect() as conn:
                res = conn.execute(sqlalchemy.text("SELECT user_id, items FROM session_cart WHERE session_id = :sid"), {"sid": request.session_id}).mappings().fetchone()
                if not res or not res['items']: return customer_db_pb2.MakePurchaseResponse(status=customer_db_pb2.Status.ERROR, message="Cart empty")
                user_id, raw_items = res['user_id'], res['items'].split(";")

            with pool_product.begin() as prod_conn:
                for entry in raw_items:
                    if "|" in entry:
                        item_id, item_qty = entry.split("|")
                        prod_conn.execute(sqlalchemy.text("UPDATE items SET quantity = quantity - :qty WHERE id = :id"), {"qty": int(item_qty), "id": item_id})

            with pool_customer.begin() as cust_conn:
                for entry in raw_items:
                    if "|" in entry:
                        item_id, item_qty = entry.split("|")
                        cust_conn.execute(sqlalchemy.text("INSERT INTO purchases (buyer_id, item_id, quantity) VALUES (:bid, :iid, :qty)"), {"bid": user_id, "iid": item_id, "qty": int(item_qty)})
                cust_conn.execute(sqlalchemy.text("UPDATE session_cart SET items='' WHERE user_id = :uid"), {"uid": user_id})
                cust_conn.execute(sqlalchemy.text("UPDATE buyer_cart SET items='' WHERE user_id=:uid"), {"uid": user_id})

            return customer_db_pb2.MakePurchaseResponse(status=customer_db_pb2.Status.OK, message="Success")
        except Exception as e:
            return customer_db_pb2.MakePurchaseResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    async def RegisterItemForSale(self, request, context):
        try:
            with pool_customer.connect() as cust_conn:
                seller = cust_conn.execute(sqlalchemy.text("SELECT seller_id FROM seller_session WHERE session_id = :sid"), {"sid": request.session_id}).mappings().fetchone()
                if not seller: return customer_db_pb2.RegisterItemResponse(status=customer_db_pb2.Status.ERROR, message="Unauthorized")
                
            with pool_product.begin() as prod_conn:
                kw_str = ",".join(request.keywords) if request.keywords else ""
                result = prod_conn.execute(sqlalchemy.text("INSERT INTO items (category, name, keywords, condition_val, sale_price, quantity, seller_id) VALUES (:cat, :name, :key, :cond, :price, :qty, :sid)"),
                    {"cat": request.category, "name": request.name, "key": kw_str, "cond": request.condition, "price": request.sale_price, "qty": request.quantity, "sid": seller['seller_id']})
                return customer_db_pb2.RegisterItemResponse(status=customer_db_pb2.Status.OK, item_id=result.lastrowid, message="Registered")
        except Exception as e:
            return customer_db_pb2.RegisterItemResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

# --- Boilerplate methods for brevity, ensure all are 'async def' ---
    async def GetItem(self, request, context): pass
    async def RemoveItemFromCart(self, request, context): pass
    async def SaveCart(self, request, context): pass
    async def GetSellerRating(self, request, context): pass
    async def ChangeItemPrice(self, request, context): pass



async def serve():
    # Initialize the Async Server
    server = aio.server()
    customer_db_pb2_grpc.add_CustomerDBServicer_to_server(BuyerDBService(), server)
    server.add_insecure_port("[::]:50051")
    print("Async gRPC Server started on port 50051")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    setup_databases()
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        print("Server stopped.")