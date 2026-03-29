import grpc
# Import the generated modules
import grpc_stubs.customer_db_pb2_grpc
import grpc_stubs.customer_db_pb2

async def run():
    # 1. Create a channel to the server
    # Use grpc.secure_channel for production with credentials
    channel = grpc.aio.insecure_channel('127.0.0.1:50051')
        # 2. Create a stub (client proxy)
    stub = grpc_stubs.customer_db_pb2_grpc.CustomerDBStub(channel)

    # 3. Create a request message
    request_data = grpc_stubs.customer_db_pb2.RegisterRequest(username='saksham', password='pwd123', name='saksham')

    # 4. Call the RPC method
    try:
        print("sending request")
        response = await stub.Register(request_data)
        print(f"Greeter client received: {response.message}")
    except grpc.RpcError as e:
        print(f"RPC failed: {e.code()} - {e.details()}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(run())
