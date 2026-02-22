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

pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

def setup_databses():
    with pool.begin() as conn:
        conn.execute(sqlalchemy.text('''
            CREATE TABLE IF NOT EXISTS sellers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(32) NOT NULL UNIQUE,
                password VARCHAR(32) NOT NULL,
                name VARCHAR(32) NOT NULL,
                thumbs_up INT DEFAULT 0,
                thumbs_down INT DEFAULT 0,
                items_sold INT DEFAULT 0
            );
        '''))

class BuyerDBService(customer_db_pb2_grpc.CustomerDBServicer):
    
    def Register(self, request, context):
        try:
            with pool.begin() as conn:
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
                    id=user_id
                )
        except Exception as e:
            return customer_db_pb2.RegisterResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    def Login(self, request, context):
        try:
            with pool.begin() as conn:
                # Fetch User using mappings to access by key
                user_res = conn.execute(
                    sqlalchemy.text("SELECT id, username FROM buyers WHERE username=:u AND password=:p"),
                    {"u": request.username, "p": request.password}
                ).mappings().fetchone()

                if user_res:
                    # Fetch Cart
                    cart_res = conn.execute(
                        sqlalchemy.text("SELECT items FROM buyer_cart WHERE user_id=:id"),
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
        except Exception as e:
            return customer_db_pb2.UserResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

    def ProductSearch(self, request, context):
        try:
            with pool.connect() as conn:
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
                        params[key] = f"%{kw}%"
                    query_str += " AND (" + " OR ".join(conditions) + ")"

                result = conn.execute(sqlalchemy.text(query_str), params).mappings().all()
                
                if not result:
                    return customer_db_pb2.ProductSearchResponse(status=customer_db_pb2.Status.ERROR)

                # Assuming you want the first item as per your original logic
                item = dict(result[0])
                item["keywords"] = item["keywords"].split(",") if item["keywords"] else []
                
                return customer_db_pb2.ProductSearchResponse(status=customer_db_pb2.Status.OK, **item)
        except Exception as e:
            return customer_db_pb2.ProductSearchResponse(status=customer_db_pb2.Status.ERROR)

    def ClearCart(self, request, context):
        try:
            with pool.begin() as conn:
                conn.execute(
                    sqlalchemy.text("UPDATE session_cart SET items='' WHERE session_id=:sid"),
                    {"sid": request.session_id}
                )
                return customer_db_pb2.ClearCartResponse(status=customer_db_pb2.Status.OK, message="Cart cleared")
        except Exception as e:
            return customer_db_pb2.ClearCartResponse(status=customer_db_pb2.Status.ERROR, message=str(e))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    customer_db_pb2_grpc.add_CustomerDBServicer_to_server(BuyerDBService(), server)
    # Important: Listen on [::] for cross-VM communication
    server.add_insecure_port("[::]:50051")
    print("gRPC Server started on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    setup_databses()
    serve()