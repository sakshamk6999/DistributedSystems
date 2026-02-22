import os
import grpc
import logging
import customer_db_pb2
import customer_db_pb2_grpc
from quart import Quart, request, jsonify
from google.protobuf.json_format import MessageToDict

app = Quart(__name__)

# --- Configuration ---
# Use the Internal IP of your Server VM here
GRPC_SERVER_ADDR = os.getenv("GRPC_SERVER_ADDR", "localhost:50051")

class GRPCManager:
    def __init__(self):
        self.channel = None
        self.stub = None

    async def init(self):
        # We use a single persistent channel for all requests
        self.channel = grpc.aio.insecure_channel(GRPC_SERVER_ADDR)
        self.stub = customer_db_pb2_grpc.CustomerDBStub(self.channel)
        print(f"Connected to gRPC server at {GRPC_SERVER_ADDR}")

    async def close(self):
        if self.channel:
            await self.channel.close()

grpc_manager = GRPCManager()

@app.before_serving
async def startup():
    await grpc_manager.init()

@app.after_serving
async def shutdown():
    await grpc_manager.close()

# --- Helpers ---
def proto_to_dict(response):
    """Converts Protobuf message to JSON-friendly dict."""
    return MessageToDict(response, 
                         preserving_proto_field_name=True, 
                         including_default_value_fields=True)

async def handle_grpc_call(rpc_method, proto_request):
    """Generic wrapper to handle gRPC errors gracefully."""
    try:
        response = await rpc_method(proto_request)
        return jsonify(proto_to_dict(response))
    except grpc.RpcError as e:
        status_code = 500
        # Map gRPC Unauthenticated to HTTP 401
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            status_code = 401
        return jsonify({"error": str(e.code()), "details": e.details()}), status_code

# --- Routes ---

@app.route('/register', methods=['POST'])
async def register():
    data = await request.get_json()
    return await handle_grpc_call(
        grpc_manager.stub.Register,
        customer_db_pb2.RegisterRequest(
            username=data.get("username"),
            password=data.get("password"),
            name=data.get("name")
        )
    )

@app.route('/login', methods=['POST'])
async def login():
    data = await request.get_json()
    return await handle_grpc_call(
        grpc_manager.stub.Login,
        customer_db_pb2.LoginRequest(
            username=data.get("username"),
            password=data.get("password")
        )
    )

@app.route('/products/search', methods=['GET'])
async def product_search():
    # Extract params from Query String
    category = request.args.get("category")
    keywords = request.args.getlist("keywords")
    # Usually better to pass session_id in Headers for GET requests
    session_id = request.headers.get("Authorization")
    
    return await handle_grpc_call(
        grpc_manager.stub.ProductSearch,
        customer_db_pb2.ProductSearchRequest(
            category=int(category) if category else 0, 
            keywords=keywords,
            session_id=session_id
        )
    )

@app.route('/cart/add', methods=['POST'])
async def add_to_cart():
    data = await request.get_json()
    return await handle_grpc_call(
        grpc_manager.stub.AddItemToCart,
        customer_db_pb2.AddItemToCartRequest(
            item_id=str(data.get("item_id")),
            quantity=int(data.get("item_quantity", 1)),
            session_id=data.get("session_id")
        )
    )

@app.route('/cart/display', methods=['POST'])
async def display_cart():
    data = await request.get_json()
    return await handle_grpc_call(
        grpc_manager.stub.DisplayCart,
        customer_db_pb2.UserRequest(session_id=data.get("session_id"))
    )

if __name__ == "__main__":
    # 50000 is a high port, ensure your GCP Firewall allows ingress on this port
    app.run(host='0.0.0.0', port=50000)