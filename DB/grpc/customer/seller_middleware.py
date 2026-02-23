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
            name=data.get("name"),
            customer_type=customer_db_pb2.CustomerType.SELLER
        )
    )

@app.route('/login', methods=['POST'])
async def login():
    data = await request.get_json()
    return await handle_grpc_call(
        grpc_manager.stub.Login,
        customer_db_pb2.LoginRequest(
            username=data.get("username"),
            password=data.get("password"),
            customer_type=customer_db_pb2.CustomerType.SELLER
        )
    )


@app.route('/seller/rating', methods=['POST'])
async def login():
    data = await request.get_json()
    return await handle_grpc_call(
        grpc_manager.stub.GetSellerRating,
        customer_db_pb2.UserRequest(
            session_id=data.get("session_id")
        )
    )


@app.route('/item/register', methods=['POST'])
async def login():
    data = await request.get_json()
    return await handle_grpc_call(
        grpc_manager.stub.RegisterItemForSale,
        customer_db_pb2.RegisterItemForSaleRequest(
            session_id=data.get("session_id"),
            name=data.get("name"),
            category=data.get("category"),
            keywords=data.get("keywords"),
            condition=data.get("condition"),
            sale_price=data.get("sale_price"),
            quantity=data.get("quantity")
        )
    )


@app.route('/item/change_price', methods=['POST'])
async def login():
    data = await request.get_json()
    return await handle_grpc_call(
        grpc_manager.stub.ChangeItemPrice,
        customer_db_pb2.ChangeItemPriceRequest(
            session_id=data.get("session_id"),
            item_id=data.get("item_id"),
            sale_price=data.get("sale_price")
        )
    )


if __name__ == "__main__":
    # Ensure port 50000 is open in GCE Firewall
    app.run(host='0.0.0.0', port=50000)