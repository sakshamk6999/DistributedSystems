import asyncio
import logging
import grpc
from grpc import aio
from concurrent import futures
import socket
import threading
import argparse
import json
import uuid
import os
import pymysql

import sys
from grpc_stubs.customer_db_pb2_grpc import CustomerDBServicer, add_CustomerDBServicer_to_server
from grpc_stubs.message_struct_pb2 import RequestMessage, ServiceMessage, RequestMetadata, ServiceMetadata, GeneralMessage

CUSTOMER_DB_CONFIG = {
    "host": os.getenv("CUSTOMER_DB_HOST", "0.0.0.0"),
    "port": os.getenv("CUSTOMER_DB_PORT", 8000),
    "user": "root",
    "password": os.getenv("CUSTOMER_DB_PASSWORD", "my-secret-pw"),
    "database": "customer_db",
    "cursorclass": pymysql.cursors.DictCursor
}

IP_ADD_MAP = {
    0: {'IP': '0.0.0.1', 'PORT': 50000},
    1: {'IP': '127.0.0.1', 'PORT': 50001},
    2: {'IP': '127.0.0.1', 'PORT': 50002},
    3: {'IP': '127.0.0.1', 'PORT': 50003},
    4: {'IP': '127.0.0.1', 'PORT': 50004},
    5: {'IP': '127.0.0.1', 'PORT': 50005}
}

local_counter = 0

# sequence message state
# request message state
# local counter
# current state

# on receiving service message, also update the request message state for the corresponding request id.

def create_customer_db_connection():
    """Create a new MySQL connection for each thread."""
    try:
        connection = pymysql.connect(**CUSTOMER_DB_CONFIG)
        print(f"Successfully connected to the customer db")
        return connection
    except pymysql.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

class BuyerDBService(CustomerDBServicer):
    def __init__(self, socket: socket.socket, id: int):
        super().__init__()
        self.socket = socket
        self.id = id

    async def broadcast_message(self):
        pass

    async def Register(self, request, context):
        packet = RequestMessage()

        packet.sender_id = self.id
        packet.local_sequence_num = local_counter
        packet.register_request = request
        serliazed_data = packet.SerializeToString()
        print("sending the request")

        for v in IP_ADD_MAP.items():
            self.socket.sendto(
                serliazed_data,
                (v['IP'], v['PORT'])
            )


async def gpdc_serve(id: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    # Initialize the Async Server
    server = aio.server(options=(('grpc.so_reuseport', 0),))
    add_CustomerDBServicer_to_server(BuyerDBService(socket=sock, id=id), server)
    server.add_insecure_port("127.0.0.1:50051")
    # server.add_insecure_port("[::]:50051")
    print("Async gRPC Server started on port 50051")
    await server.start()
    await server.wait_for_termination()


async def udp_receive(id: int, queue: asyncio.Queue):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((IP_ADD_MAP[id]['IP'], IP_ADD_MAP[id]['PORT']))
    print("Ready to receive")

    while True:
        data, addr = await sock.recvfrom(1024)
        print(f"received from addr:{addr} data:{data}")
        await queue.put(data)

async def process_message(id: int, queue: asyncio.Queue):
    while True:
        data = await queue.get()
        
        print("Got the data", data)

        received_message = GeneralMessage()
        received_message.ParseFromString(data)

        field_name = received_message.WhichOneof("message_type")

        if field_name == "request_message":
            request_message = received_message.request_message
        else:
            service_message = received_message.service_message

async def start_server(args):
    queue = asyncio.Queue(maxsize=1000)

    print("starting the processes")

    async with asyncio.TaskGroup() as tg:
        grpc_rec = asyncio.create_task(gpdc_serve(args.id))
        udp_rec = asyncio.create_task(udp_receive(args.id, queue))
        message_proc = asyncio.create_task(process_message(args.id, queue))

    print("finished")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog='customer_db_service',
        description='starts the customer_db replica'
    )
    
    parser.add_argument('--id', type=int)

    args = parser.parse_args()
    
    # setup_databases()
    try:
        asyncio.run(start_server(args))
    except KeyboardInterrupt:
        print("Server stopped.")