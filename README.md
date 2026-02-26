The application consists of 2 REST service as middleware for the Buyer and the Seller  use cases. Each server is developed using the 'Quart' framework, which is the reimplimentation of the FLASK framework to make it asynchronous. The Buyer and Seller Rest clients provide an interactive CLI for the user. 

 Google Cloud SQL is used to host the Product and Customer DBs, and google cloud sql connector, Pymysql, and SQLAlchemy is used to connect each gRPC VM instance to the DBs.

The middleware paths: 
For Buyer: DB/grpc/customer/buyer_middleware.py
For Seller: DB/grpc/customer/seller_middleware.py

The gRPC protos: Protos/

gRPC Servers: DB/grpc/customer/customer_db_server_grpc.py

Frontend CLI services: Frontend/

