import asyncio
import grpc
import customer_db_pb2
import customer_db_pb2_grpc
from quart import Quart, request, jsonify
from google.protobuf.json_format import MessageToDict

app = Quart(__name__)

# --- Global gRPC Async State ---
# We use a global variable to store the async channel and stub
grpc_state = {
    "channel": None,
    "stub": None
}

@app.before_serving
async def startup():
    """Initialize the async gRPC channel when the server starts."""
    grpc_state["channel"] = grpc.aio.insecure_channel("localhost:50051")
    grpc_state["stub"] = customer_db_pb2_grpc.CustomerDBStub(grpc_state["channel"])
    print("Async gRPC channel opened.")

@app.after_serving
async def shutdown():
    """Clean up the channel when the server stops."""
    await grpc_state["channel"].close()
    print("Async gRPC channel closed.")

def proto_to_dict(response):
    return MessageToDict(response, preserving_proto_field_name=True)

# --- Async Routes ---
@app.route('/register', methods=['POST'])
async def register():
    # request.get_json() is a coroutine in Quart
    data = await request.get_json()
    print("data is", data)
    # We await the gRPC call so the event loop can handle other requests while waiting for the DB
    try:
        response = await grpc_state["stub"].Register(customer_db_pb2.RegisterRequest(
            username=data.get("username"),
            password=data.get("password"),
            name=data.get("name")
        ))

        print("Response is", response)
        # print("Response", response.se)
        return jsonify(proto_to_dict(response))
    except grpc.RpcError as e:
        return jsonify({"error": str(e.code()), "details": e.details()}), 500

# --- Async Routes ---
@app.route('/login', methods=['POST'])
async def login():
    # request.get_json() is a coroutine in Quart
    data = await request.get_json()
    print("data is", data)
    # We await the gRPC call so the event loop can handle other requests while waiting for the DB
    try:
        response = await grpc_state["stub"].Login(customer_db_pb2.LoginRequest(
            username=data.get("username"),
            password=data.get("password")
        ))

        print("Response is", response)
        # print("Response", response.se)
        return jsonify(proto_to_dict(response))
    except grpc.RpcError as e:
        return jsonify({"error": str(e.code()), "details": e.details()}), 500

@app.route('/products/search', methods=['GET'])
async def product_search():
    print("request args", request.args)
    category = request.args.get("category")
    keywords = request.args.getlist("keywords")
    session_id = request.headers.get("Authorization")
    
    response = await grpc_state["stub"].ProductSearch(customer_db_pb2.ProductSearchRequest(
        session_id=session_id, 
        category=category, 
        keywords=keywords
    ))
    return jsonify(proto_to_dict(response))


@app.route('/item/get', methods=['POST'])
async def get_item():
    data = await request.get_json() 
    session_id = data.get("session_id")

    # This call is non-blocking to the server's main thread
    response = await grpc_state["stub"].GetItem(customer_db_pb2.GetItemRequest(
        item_id=data.get("item_id"),
        session_id=session_id
    ))
    return jsonify(proto_to_dict(response))


@app.route('/cart/add', methods=['POST'])
async def add_to_cart():
    data = await request.get_json()
    session_id = data.get("session_id")

    # This call is non-blocking to the server's main thread
    response = await grpc_state["stub"].AddItemToCart(customer_db_pb2.AddItemToCartRequest(
        item_id=data.get("item_id"),
        quantity=data.get("item_quantity"),
        session_id=session_id
    ))
    return jsonify(proto_to_dict(response))

@app.route('/cart/remove', methods=['POST'])
async def remove_item_from_cart():
    data = await request.get_json()
    session_id = data.get("session_id")

    # This call is non-blocking to the server's main thread
    response = await grpc_state["stub"].RemoveItemFromCart(customer_db_pb2.RemoveItemFromCartRequest(
        item_id=data.get("item_id"),
        session_id=session_id
    ))
    return jsonify(proto_to_dict(response))

@app.route('/cart/save', methods=['POST'])
async def save_cart():
    data = await request.get_json()
    session_id = data.get("session_id")

    # This call is non-blocking to the server's main thread
    response = await grpc_state["stub"].SaveCart(customer_db_pb2.UserRequest(
        session_id=session_id
    ))
    return jsonify(proto_to_dict(response))

@app.route('/cart/display', methods=['POST'])
async def display_cart():
    data = await request.get_json()
    session_id = data.get("session_id")

    # This call is non-blocking to the server's main thread
    response = await grpc_state["stub"].DisplayCart(customer_db_pb2.UserRequest(
        session_id=session_id
    ))
    return jsonify(proto_to_dict(response))

if __name__ == "__main__":
    # Quart uses an asyncio event loop internally
    app.run(host='0.0.0.0', port=50000)