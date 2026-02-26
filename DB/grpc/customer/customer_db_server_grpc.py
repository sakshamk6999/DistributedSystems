from concurrent import futures
from google.cloud.sql.connector import Connector
import grpc
import customer_db_pb2
import customer_db_pb2_grpc
import sqlalchemy
import logging

# 1. Setup Connector and Engine
connector = Connector()

INSTANCE_CONNECTION_NAME = "distributedsystemsassi:us-central1:customer-db-1"

def getconn():
    return connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user="saksham_user",
        password="Customer-db-1",
        db="customer_db"
    )

pool_customer = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

# --- New Product DB Setup ---
# Replace with your actual Product Instance connection name
INSTANCE_PRODUCT = "distributedsystemsassi:us-central1:product-db-1" 
pool_product = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=lambda: connector.connect(
        INSTANCE_PRODUCT, "pymysql", user="saksham_user", password="Product-db-1", db="product_db"
    ),
)

def setup_databases():
    # --- Setup Customer DB ---
    with pool_customer.begin() as conn:
        print("Initializing Customer Database tables...")
        
        # Split into individual execute calls
        tables = [
            '''CREATE TABLE IF NOT EXISTS sellers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(32) NOT NULL UNIQUE,
                password VARCHAR(32) NOT NULL,
                name VARCHAR(32) NOT NULL,
                thumbs_up INT DEFAULT 0,
                thumbs_down INT DEFAULT 0,
                items_sold INT DEFAULT 0
            )''',
            '''CREATE TABLE IF NOT EXISTS buyers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(32) NOT NULL UNIQUE,
                password VARCHAR(32) NOT NULL,
                name VARCHAR(32) NOT NULL
            )''',
            '''CREATE TABLE IF NOT EXISTS purchases (
                purchase_id INT AUTO_INCREMENT PRIMARY KEY,
                buyer_id INT NOT NULL,
                item_id INT NOT NULL,
                quantity INT NOT NULL,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS buyer_cart (
              user_id INT PRIMARY KEY,
              items VARCHAR(255)
            )''',
            '''CREATE TABLE IF NOT EXISTS session_cart (
              session_id INT AUTO_INCREMENT PRIMARY KEY,
              user_id INT NOT NULL,
              items VARCHAR(255)
            )''',
            '''CREATE TABLE IF NOT EXISTS seller_session (
              session_id INT AUTO_INCREMENT PRIMARY KEY,
              seller_id INT NOT NULL,
              items VARCHAR(255)
            )'''
        ]
        
        for table_sql in tables:
            conn.execute(sqlalchemy.text(table_sql))
        print("Customer DB initialization complete.")

    # --- Setup Product DB ---
    # Ensure this uses pool_product!
    with pool_product.begin() as conn:
        print("Initializing Product Database tables...")
        conn.execute(sqlalchemy.text('''
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
            )
        '''))
        print("Product DB initialization complete.")

class BuyerDBService(customer_db_pb2_grpc.CustomerDBServicer):
    
    def Register(self, request, context):
        try:
            with pool_customer.begin() as conn:
                print("params received register", request)
                if request.customer_type == customer_db_pb2.CustomerType.BUYER:
                    # Insert Buyer
                    result = conn.execute(
                        sqlalchemy.text("INSERT INTO buyers (username, password, name) VALUES (:u, :p, :n)"),
                        {"u": request.username, "p": request.password, "n": request.name}
                    )
                    user_id = result.lastrowid
                    
                    # Insert Initial Cart
                    conn.execute(
                        sqlalchemy.text("INSERT INTO buyer_cart (user_id, items) VALUES (:id, :items)"),
                        {"id": user_id, "items": ""}
                    )
                    
                    return customer_db_pb2.RegisterResponse(
                        status=customer_db_pb2.Status.OK, 
                        message=f"Buyer created: {request.username}", 
                        id=int(user_id)
                    )
                else:
                    result = conn.execute(
                        sqlalchemy.text("INSERT INTO sellers (username, password, name) VALUES (:u, :p, :n)"),
                        {"u": request.username, "p": request.password, "n": request.name}
                    )
                    user_id = result.lastrowid

                    # conn.execute(
                    #     sqlalchemy.text("INSERT INTO seller_session (seller, items) VALUES (:seller_id, "")"),
                    #     {"seller_id": request.seller_id}
                    # )
                    return customer_db_pb2.RegisterResponse(
                        status=customer_db_pb2.Status.OK, 
                        message=f"Seller created: {request.username}", 
                        id=int(user_id)
                    )
        except Exception as e:
            return customer_db_pb2.RegisterResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    def Login(self, request, context):
        try:
            print("params received login", request)
            with pool_customer.begin() as conn:
                if request.customer_type == customer_db_pb2.CustomerType.BUYER:
                    # Fetch User using mappings to access by key
                    user_res = conn.execute(
                        sqlalchemy.text("SELECT * FROM buyers WHERE username=:u AND password=:p"),
                        {"u": request.username, "p": request.password}
                    ).mappings().fetchone()

                    if user_res:
                        # Fetch Cart
                        cart_res = conn.execute(
                            sqlalchemy.text("SELECT * FROM buyer_cart WHERE user_id=:id"),
                            {"id": user_res['id']}
                        ).mappings().fetchone()

                        # Create Session
                        session_res = conn.execute(
                            sqlalchemy.text("INSERT INTO session_cart (user_id, items) VALUES (:uid, :items)"),
                            {"uid": user_res['id'], "items": cart_res['items'] if cart_res else ""}
                        )
                        
                        return customer_db_pb2.UserResponse(
                            status=customer_db_pb2.Status.OK, 
                            message="Login Successful", 
                            session_id=session_res.lastrowid
                        )
                    else:
                        return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.ERROR, message="Invalid Credentials")
                else:
                    # Fetch User using mappings to access by key
                    user_res = conn.execute(
                        sqlalchemy.text("SELECT * FROM sellers WHERE username=:u AND password=:p"),
                        {"u": request.username, "p": request.password}
                    ).mappings().fetchone()

                    if user_res:
                        # Create Session
                        session_res = conn.execute(
                            sqlalchemy.text("INSERT INTO seller_session (seller_id, items) VALUES (:uid, "")"),
                            {"uid": user_res['id']}
                        )
                        
                        return customer_db_pb2.UserResponse(
                            status=customer_db_pb2.Status.OK, 
                            message="Login Successful", 
                            session_id=session_res.lastrowid
                        )
                    else:
                        return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.ERROR, message="Invalid Credentials")
        except Exception as e:
            return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    def Logout(self, request, context):
        try:
            print("params received logout", request)
            with pool_customer.begin() as conn:
                if request.customer_type == customer_db_pb2.CustomerType.BUYER:
                    conn.execute(
                        sqlalchemy.text("DELETE FROM session_cart where session_id=:sid"),
                        {"sid": request.session_id}
                    )

                    return customer_db_pb2.UserResponse(
                        status=customer_db_pb2.Status.OK, 
                        message="Logout Successful"
                    )
                else:
                    conn.execute(
                        sqlalchemy.text("DELETE FROM seller_session where session_id=:sid"),
                        {"sid": request.session_id}
                    )

                    return customer_db_pb2.UserResponse(
                        status=customer_db_pb2.Status.OK, 
                        message="Logout Successful"
                    )
        except Exception as e:
            return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    def ProductSearch(self, request, context):
        try:
            print("params received product search", request)
            with pool_product.connect() as conn:
                # Core dynamic query logic
                query_str = "SELECT * FROM items WHERE category=:cat AND quantity > 0"
                params = {"cat": request.category}

                if request.keywords:
                    # Caution: Keyword partial matching is better handled via specific SQLAlchemy constructs, 
                    # but here is a safe way to format it:
                    conditions = []
                    for i, kw in enumerate(request.keywords):
                        key = f"kw{i}"
                        conditions.append(f"keywords LIKE :{key}")
                        params[key] = f"'%{kw}%'"
                    query_str += " AND (" + " OR ".join(conditions) + ")"
                print("query string ", query_str)
                result = conn.execute(sqlalchemy.text(query_str), params).mappings().all()
                
                if not result:
                    return customer_db_pb2.ProductSearchResponse(status=customer_db_pb2.Status.ERROR)

                # Assuming you want the first item as per your original logic
                items = []

                for r in result:
                    item = dict(r)
                    item["keywords"] = item["keywords"].split(",") if item["keywords"] else []
                    items.append(item)
                
                return customer_db_pb2.ListProductResponse(status=customer_db_pb2.Status.OK, items=items)
        except Exception as e:
            return customer_db_pb2.ProductSearchResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    def ClearCart(self, request, context):
        
        try:
            with pool_customer.begin() as conn:
                print("params received clear cart", request)
                res = conn.execute(
                    sqlalchemy.text("SELECT * FROM session_cart WHERE session_id = :sid"),
                    {"sid": request.session_id}
                ).mappings().fetchone()

                conn.execute(
                    sqlalchemy.text("UPDATE session_cart SET items='' WHERE user_id = :sid"),
                    {"sid": res['user_id']}
                )

                return customer_db_pb2.ClearCartResponse(status=customer_db_pb2.Status.OK, message="Cart cleared")
        except Exception as e:
            return customer_db_pb2.ClearCartResponse(status=customer_db_pb2.Status.ERROR, message=str(e))
    
    def RemoveItemFromCart(self, request, context):
        try:
            with pool_customer.begin() as conn:
                print("params received remove item", request)
                # 1. Fetch current items in the session
                res = conn.execute(
                    sqlalchemy.text("SELECT * FROM session_cart WHERE session_id = :sid"),
                    {"sid": request.session_id}
                ).mappings().fetchone()

                if not res:
                    return customer_db_pb2.RemoveItemFromCartResponse(
                        status=customer_db_pb2.Status.ERROR, 
                        message="Session not found"
                    )

                # 2. Logic to filter out the item
                # Items are stored as "id|qty;id|qty"
                current_items = res['items'].split(";") if res['items'] else []
                updated_items = []
                
                for entry in current_items:
                    if not entry: continue
                    item_id, quantity = entry.split("|")
                    if item_id != str(request.item_id):
                        updated_items.append(entry)

                # 3. Update the database
                conn.execute(
                    sqlalchemy.text("UPDATE session_cart SET items = :items WHERE session_id = :sid"),
                    {"items": ";".join(updated_items), "sid": request.session_id}
                )

                return customer_db_pb2.RemoveItemFromCartResponse(
                    status=customer_db_pb2.Status.OK, 
                    message=f"Item {request.item_id} removed"
                )
        except Exception as e:
            return customer_db_pb2.RemoveItemFromCartResponse(
                status=customer_db_pb2.Status.ERROR, 
                message=str(e)
            )

    def SaveCart(self, request, context):
        try:
            with pool_customer.begin() as conn:
                print("params received save cart", request)
                # 1. Get items from the active session
                session_res = conn.execute(
                    sqlalchemy.text("SELECT * FROM session_cart WHERE session_id = :sid"),
                    {"sid": request.session_id}
                ).mappings().fetchone()

                if not session_res:
                    return customer_db_pb2.SaveCartResponse(
                        status=customer_db_pb2.Status.ERROR, 
                        message="Invalid Session ID"
                    )

                # 2. Persist session items into the permanent buyer_cart
                conn.execute(
                    sqlalchemy.text("UPDATE buyer_cart SET items = :items WHERE user_id = :uid"),
                    {"items": session_res['items'], "uid": session_res['user_id']}
                )

                return customer_db_pb2.SaveCartResponse(
                    status=customer_db_pb2.Status.OK, 
                    message="Cart saved successfully"
                )
        except Exception as e:
            return customer_db_pb2.SaveCartResponse(
                status=customer_db_pb2.Status.ERROR, 
                message=str(e)
            )

    def DisplayCart(self, request, context):
        try:
            with pool_customer.connect() as conn: # connect() is enough for SELECT
                print("params received display cart", request)
                res = conn.execute(
                    sqlalchemy.text("SELECT * FROM session_cart WHERE session_id = :sid"),
                    {"sid": request.session_id}
                ).mappings().fetchone()

                if not res:
                    return customer_db_pb2.DisplayCartResponse(
                        status=customer_db_pb2.Status.ERROR, 
                        message="Session not found"
                    )

                # Parse "id|qty;id|qty" into list of message objects
                items_list = []
                raw_items = res['items'].split(";") if res['items'] else []
                
                for entry in raw_items:
                    if "|" in entry:
                        i_id, i_qty = entry.split("|")
                        items_list.append({
                            'item_id': i_id,
                            'quantity': int(i_qty)
                        })

                return customer_db_pb2.DisplayCartResponse(
                    status=customer_db_pb2.Status.OK, 
                    items=items_list
                )
        except Exception as e:
            return customer_db_pb2.DisplayCartResponse(
                status=customer_db_pb2.Status.ERROR, 
                message=str(e)
            )
    
    def GetItem(self, request, context):
        try:
            # Connect to Product DB for read-only query
            with pool_product.connect() as conn:
                print("params received get item", request)
                result = conn.execute(
                    sqlalchemy.text("SELECT * FROM items WHERE id = :id"),
                    {"id": request.item_id}
                ).mappings().fetchone()

                if not result:
                    # Return an empty response or handle as 404
                    return customer_db_pb2.GetItemResponse()

                item_data = dict(result)
                # Handle keywords if they exist as a comma-separated string
                if "keywords" in item_data and item_data["keywords"]:
                    item_data["keywords"] = item_data["keywords"].split(",")
                else:
                    item_data["keywords"] = []

                return customer_db_pb2.GetItemResponse(status=customer_db_pb2.Status.OK, item=item_data)
        except Exception as e:
            print(f"GetItem Error: {e}")
            # You might want to return an error status in your proto instead of an empty object
            return customer_db_pb2.GetItemResponse(status=customer_db_pb2.Status.OK, message=str(e))
        
    def AddItemToCart(self, request, context):
        try:
            # 1. Verify availability in Product DB
            with pool_product.connect() as prod_conn:
                print("params received add item cart", request)
                product = prod_conn.execute(
                    sqlalchemy.text("SELECT * FROM items WHERE id = :id AND quantity >= :qty"),
                    {"id": request.item_id, "qty": request.item_quantity}
                ).mappings().fetchone()

                if not product:
                    return customer_db_pb2.AddItemToCartResponse(
                        status=customer_db_pb2.Status.ERROR, 
                        message=f"Item {request.item_id} not available in requested quantity"
                    )

            # 2. Update the session in Customer DB
            with pool_customer.begin() as cust_conn:
                res = cust_conn.execute(
                    sqlalchemy.text("SELECT * FROM session_cart WHERE session_id = :sid"),
                    {"sid": request.session_id}
                ).mappings().fetchone()

                if res is None:
                    return customer_db_pb2.AddItemToCartResponse(
                        status=customer_db_pb2.Status.ERROR, 
                        message="Invalid Session ID"
                    )

                # Parse existing items and append the new one
                current_items_str = res['items'] if res['items'] else ""
                new_entry = f"{request.item_id}|{request.item_quantity}"
                
                updated_items_str = f"{current_items_str};{new_entry}" if current_items_str else new_entry

                cust_conn.execute(
                    sqlalchemy.text("UPDATE session_cart SET items = :items WHERE session_id = :sid"),
                    {"items": updated_items_str, "sid": request.session_id}
                )

                return customer_db_pb2.AddItemToCartResponse(
                    status=customer_db_pb2.Status.OK, 
                    message=f"Added {request.item_quantity} of {request.item_id} to cart"
                )

        except Exception as e:
            print(f"AddItemToCart Error: {e}")
            return customer_db_pb2.AddItemToCartResponse(
                status=customer_db_pb2.Status.ERROR, 
                message=str(e)
            )

    def MakePurchase(self, request, context):
        try:
            # 1. Fetch Session Data (Need user_id and items)
            with pool_customer.connect() as conn:
                print("params received make purchase", request)
                res = conn.execute(
                    sqlalchemy.text("SELECT * FROM session_cart WHERE session_id = :sid"),
                    {"sid": request.session_id}
                ).mappings().fetchone()

                if not res or not res['items']:
                    return customer_db_pb2.MakePurchaseResponse(
                        status=customer_db_pb2.Status.ERROR, 
                        message="Cart is empty or session invalid"
                    )

                user_id = res['user_id']
                raw_items = res['items'].split(";")

            # 2. Update Product DB (Deduct Inventory)
            # We do this first because inventory is the most likely thing to fail/conflict
            with pool_product.begin() as prod_conn:
                for entry in raw_items:
                    if "|" in entry:
                        item_id, item_qty = entry.split("|")
                        prod_conn.execute(
                            sqlalchemy.text("UPDATE items SET quantity = quantity - :qty WHERE id = :id"),
                            {"qty": int(item_qty), "id": item_id}
                        )

            # 3. Update Customer DB (Purchases & Clear Carts)
            with pool_customer.begin() as cust_conn:
                for entry in raw_items:
                    if "|" in entry:
                        item_id, item_qty = entry.split("|")
                        # Add to Purchase History
                        cust_conn.execute(
                            sqlalchemy.text("INSERT INTO purchases (buyer_id, item_id, quantity) VALUES (:bid, :iid, :qty)"),
                            {"bid": user_id, "iid": item_id, "qty": int(item_qty)}
                        )

                # Clear both carts
                cust_conn.execute(
                    sqlalchemy.text("UPDATE session_cart SET items='' WHERE user_id = :uid"),
                    {"uid": user_id}
                )

                cust_conn.execute(
                    sqlalchemy.text("UPDATE buyer_cart SET items='' WHERE user_id=:uid"),
                    {"uid": user_id}
                )

            return customer_db_pb2.MakePurchaseResponse(
                status=customer_db_pb2.Status.OK, 
                message="Purchase successful! Inventory updated and carts cleared."
            )

        except Exception as e:
            print(f"Purchase Error: {e}")
            return customer_db_pb2.MakePurchaseResponse(
                status=customer_db_pb2.Status.ERROR, 
                message=f"Transaction Failed: {str(e)}"
            )
    
    def GetSellerRating(self, request, context):
        try:
            with pool_customer.connect() as conn:
                print("params received seller rating", request)
                # 1. Verify seller session and get seller_id
                session_res = conn.execute(
                    sqlalchemy.text("SELECT * FROM seller_session WHERE session_id = :sid"),
                    {"sid": request.session_id}
                ).mappings().fetchone()

                if not session_res:
                    return customer_db_pb2.GetSellerRatingResponse(
                        status=customer_db_pb2.Status.ERROR, 
                        message="Invalid seller session"
                    )

                # 2. Fetch rating from sellers table
                seller_res = conn.execute(
                    sqlalchemy.text("SELECT * FROM sellers WHERE id = :id"),
                    {"id": session_res['seller_id']}
                ).mappings().fetchone()

                return customer_db_pb2.GetSellerRatingResponse(
                    status=customer_db_pb2.Status.OK,
                    message=f"User Rating Fetched",
                    thumbs_up=int(seller_res['thumbs_up']),
                    thumbs_down=int(seller_res['thumbs_down'])
                )
        except Exception as e:
            return customer_db_pb2.GetSellerRatingResponse(
                status=customer_db_pb2.Status.ERROR, 
                message=str(e)
            )

    def RegisterItemForSale(self, request, context):
        try:
            # 1. Identify seller via Customer DB
            with pool_customer.connect() as cust_conn:
                print("params received register item", request)
                seller_res = cust_conn.execute(
                    sqlalchemy.text("SELECT * FROM seller_session WHERE session_id = :sid"),
                    {"sid": request.session_id}
                ).mappings().fetchone()

                if not seller_res:
                    return customer_db_pb2.RegisterItemResponse(
                        status=customer_db_pb2.Status.ERROR, 
                        message="Unauthorized: Seller session not found"
                    )
                
                seller_id = seller_res['seller_id']
                
            # 2. Insert item into Product DB
            with pool_product.begin() as prod_conn:
                # Convert list of keywords to comma-separated string
                keyword_str = ",".join(request.keywords) if request.keywords else ""
                
                result = prod_conn.execute(
                    sqlalchemy.text("""
                        INSERT INTO items (category, name, keywords, condition_val, sale_price, quantity, seller_id) 
                        VALUES (:cat, :name, :key, :cond, :price, :qty, :sid)
                    """),
                    {
                        "cat": request.category,
                        "name": request.name,
                        "key": keyword_str,
                        "cond": request.condition,
                        "price": request.sale_price,
                        "qty": request.quantity,
                        "sid": seller_id
                    }
                )
                
                return customer_db_pb2.RegisterItemResponse(
                    status=customer_db_pb2.Status.OK,
                    item_id=result.lastrowid,
                    message="Item registered successfully"
                )
        except Exception as e:
            return customer_db_pb2.RegisterItemResponse(
                status=customer_db_pb2.Status.ERROR, 
                message=str(e)
            )

    def ChangeItemPrice(self, request, context):
        try:

            with pool_customer.connect() as cust_conn:
                seller_res = cust_conn.execute(
                    sqlalchemy.text("SELECT * FROM seller_session WHERE session_id = :sid"),
                    {"sid": request.session_id}
                ).mappings().fetchone()

                if not seller_res:
                    return customer_db_pb2.StatusResponse(
                        status=customer_db_pb2.Status.ERROR, 
                        message="Unauthorized: Seller session not found"
                    )
                
            with pool_product.begin() as conn:
                result = conn.execute(
                    sqlalchemy.text("UPDATE items SET sale_price = :price WHERE id = :id"),
                    {"price": request.sale_price, "id": request.item_id}
                )
                
                if result.rowcount == 0:
                    return customer_db_pb2.StatusResponse(
                        status=customer_db_pb2.Status.ERROR, 
                        message="Item not found"
                    )

                return customer_db_pb2.StatusResponse(
                    status=customer_db_pb2.Status.OK, 
                    message="Price updated successfully"
                )
        except Exception as e:
            return customer_db_pb2.StatusResponse(
                status=customer_db_pb2.Status.ERROR, 
                message=str(e)
            )



def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    customer_db_pb2_grpc.add_CustomerDBServicer_to_server(BuyerDBService(), server)
    # Important: Listen on [::] for cross-VM communication
    server.add_insecure_port("[::]:50051")
    print("gRPC Server started on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    setup_databases()
    serve()