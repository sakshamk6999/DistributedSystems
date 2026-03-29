python -m grpc_tools.protoc -I./protos --python_out=./grpc_stubs/ --pyi_out=./grpc_stubs/ --grpc_python_out=./grpc_stubs/ ./protos/customer_db.proto

python -m grpc_tools.protoc -I./protos --python_out=./grpc_stubs/ --pyi_out=./grpc_stubs/ --grpc_python_out=./grpc_stubs/ ./protos/message_struct.proto ./protos/customer_db.proto
