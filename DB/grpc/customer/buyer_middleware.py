import os
import grpc
import logging
import customer_db_pb2
import customer_db_pb2_grpc
from quart import Quart, request, jsonify
from google.protobuf.json_format import MessageToDict

from zeep import Client
import asyncio

BANK_WSDL_URL = os.getenv("BANK_WSDL_URL", "http://localhost:8000/?wsdl")

app = Quart(__name__)

# --- Configuration ---
GRPC_SERVER_ADDR = os.getenv("GRPC_SERVER_ADDR", "localhost:50051")

class GRPCManager:
    def __init__(self):
        self.channel = None
        self.stub = None

    async def init(self):
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
    return MessageToDict(response, 
                         preserving_proto_field_name=True)

async def handle_grpc_call(rpc_method, proto_request):
    try:
        response = await rpc_method(proto_request)
        return jsonify(proto_to_dict(response))
    except grpc.RpcError as e:
        status_code = 500
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            status_code = 401
        elif e.code() == grpc.StatusCode.NOT_FOUND:
            status_code = 404
        return jsonify({"error": str(e.code()), "details": e.details()}), status_code

# --- Account Routes ---

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

# --- Product Routes ---

@app.route('/products/search', methods=['GET'])
async def product_search():
    category = request.args.get("category")
    keywords = request.args.getlist("keywords")
    # Using Authorization header as a fallback for session tracking on GETs
    session_id = request.headers.get("Authorization") or request.args.get("session_id")
    
    return await handle_grpc_call(
        grpc_manager.stub.ProductSearch,
        customer_db_pb2.ProductSearchRequest(
            category=int(category) if category else 0, 
            keywords=keywords,
            session_id=session_id
        )
    )

@app.route('/item/get', methods=['GET'])
async def get_item():
    # GET request using query params
    item_id = request.args.get("item_id")
    return await handle_grpc_call(
        grpc_manager.stub.GetItem,
        customer_db_pb2.GetItemRequest(item_id=str(item_id))
    )

# --- Cart Routes ---

@app.route('/cart/add', methods=['POST'])
async def add_to_cart():
    data = await request.get_json()
    return await handle_grpc_call(
        grpc_manager.stub.AddItemToCart,
        customer_db_pb2.AddItemToCartRequest(
            item_id=str(data.get("item_id")),
            item_quantity=int(data.get("item_quantity", 1)),
            session_id=data.get("session_id")
        )
    )

@app.route('/cart/remove', methods=['POST'])
async def remove_from_cart():
    data = await request.get_json()
    return await handle_grpc_call(
        grpc_manager.stub.RemoveItemFromCart,
        customer_db_pb2.RemoveItemFromCartRequest(
            item_id=str(data.get("item_id")),
            session_id=data.get("session_id")
        )
    )

@app.route('/cart/display', methods=['POST'])
async def display_cart():
    data = await request.get_json()
    # Note: Using UserRequest as per your gRPC definition
    return await handle_grpc_call(
        grpc_manager.stub.DisplayCart,
        customer_db_pb2.UserRequest(session_id=data.get("session_id"))
    )

@app.route('/cart/save', methods=['POST'])
async def save_cart():
    data = await request.get_json()
    return await handle_grpc_call(
        grpc_manager.stub.SaveCart,
        customer_db_pb2.UserRequest(session_id=data.get("session_id"))
    )

@app.route('/cart/clear', methods=['POST'])
async def clear_cart():
    data = await request.get_json()
    return await handle_grpc_call(
        grpc_manager.stub.ClearCart,
        customer_db_pb2.UserRequest(session_id=data.get("session_id"))
    )

@app.route('/cart/purchase', methods=['POST'])
async def make_purchase():
    data = await request.get_json()
    session_id = data.get("session_id")
    
    # We'll use these for the SOAP call (dummy data or real values)
    card_number = data.get("card_number", "0000-0000-0000-0000")
    amount = data.get("amount", "0.00")

    try:
        # 1. Call the SOAP Service (Emulated Bank)
        # We run this in a thread because Zeep is synchronous
        def call_soap():
            client = Client(BANK_WSDL_URL)
            # Match the method name 'process_payment' from the SOAP script
            return client.service.process_payment(card_number, amount)

        bank_response = await asyncio.to_thread(call_soap)

        # 2. Check if Bank said "yes"
        if bank_response.lower() == "yes":
            # 3. Call the gRPC Service to finalize the purchase
            return await handle_grpc_call(
                grpc_manager.stub.MakePurchase,
                customer_db_pb2.UserRequest(session_id=session_id)
            )
        else:
            # Bank returned "no" (10% chance)
            return jsonify({
                "status": "ERROR",
                "message": "Bank transaction failed: Payment declined by emulated bank."
            }), 402  # 402 Payment Required

    except Exception as e:
        logging.error(f"Purchase flow error: {e}")
        return jsonify({
            "status": "ERROR", 
            "message": f"Middleware error during purchase: {str(e)}"
        }), 500


if __name__ == "__main__":
    # Ensure port 50000 is open in GCE Firewall
    app.run(host='0.0.0.0', port=50000)