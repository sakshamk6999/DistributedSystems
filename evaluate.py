import argparse
import json
import socket
import threading
import time
from queue import Queue
from statistics import mean, median
import pymysql
from tqdm import trange


def send_data_to_server(client_socket: socket.socket, args):
    json_string = json.dumps(args)
    data_bytes = json_string.encode('utf-8')
    # print("sending", json_string)
    client_socket.sendall(data_bytes)

def record_output(action, response, record_list, initial_time):
    decoded_string = response.decode("utf-8")

    res_object = json.loads(decoded_string)

    t = time.perf_counter()

    elapsed_call_time = t - initial_time

    if res_object['status'] == 'OK':
        record_list.put({
            "action": action,
            "elapsed_call_time": elapsed_call_time,
            "status": "success"
        })
    else:
        record_list.put({
            "action": action,
            "elapsed_call_time": elapsed_call_time,
            "status": "fail"
        })
    
    return res_object
    

def buyer_client(buyer_id, buyer_server_config, barrier, thread_id, num_calls, result_q, run_num):
    server_host = buyer_server_config['host']
    server_port = buyer_server_config['port']

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.connect((server_host, server_port))

    try:
        barrier.wait()
    except threading.BrokenBarrierError:
        pass
    

    t0 = time.perf_counter()

    current_session = {
        "is_logged_in": False,
        "session_id": None,
    }
    
    if run_num == 0:
        register_account_payload = {
            "action": "REGISTER",
            "username": f"test_buyer_{buyer_id}",
            "name": f"buyer_{buyer_id}",
            "password": f"test_buyer_{buyer_id}"
        }

        send_data_to_server(client_socket, register_account_payload)
        server_res = client_socket.recv(1024)
        last_response = record_output("REGISTER", server_res, result_q, t0)

    login_payload = {
        "action": "LOGIN",
        "username": f"test_buyer_{buyer_id}",
        "password": f"test_buyer_{buyer_id}"
    }

    t0 = time.perf_counter()

    send_data_to_server(client_socket, login_payload)
    server_res = client_socket.recv(1024)
    last_response = record_output("LOGIN", server_res, result_q, t0)

    session_id = last_response['session_id']

    j = 0
    for i in range(num_calls):
        total_actions = ['PRODUCT_SEARCH', 'GET_BUYER_PURCHASES', 'SAVE_CART', 'CLEAR_CART', 'DISPLAY_CART']

        selected_action = total_actions[j]
        j = (j + 1) % 5

        if selected_action == "PRODUCT_SEARCH":
            payload = {
                "action": "PRODUCT_SEARCH",
                "session_id": session_id,
                "category": 1,
                "keywords": ["cycle", "kids", "adventure"]
            }
        elif selected_action == "GET_BUYER_PURCHASES":
            payload = {
                "action": "GET_BUYER_PURCHASES",
                "session_id": session_id,
            }
        elif selected_action == "SAVE_CART":
            payload = {
                "action": "SAVE_CART",
                "session_id": session_id,
            }
        elif selected_action == "CLEAR_CART":
            payload = {
                "action": "CLEAR_CART",
                "session_id": session_id,
            }
        else:
            payload = {
                "action": "DISPLAY_CART",
                "session_id": session_id,
            }

        t0 = time.perf_counter()
        send_data_to_server(client_socket, payload)
        server_res = client_socket.recv(1024)
        record_output(selected_action, server_res, result_q, t0)
    
    # Logging out
    payload = {
        "action": "LOGOUT",
        "session_id": session_id,
    }
    
    send_data_to_server(client_socket, payload)

    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()

def seller_client(seller_id, seller_server_config, barrier, thread_id, num_calls, result_q, run_num):
    server_host = seller_server_config['host']
    server_port = seller_server_config['port']

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.connect((server_host, server_port))

    try:
        barrier.wait()
    except threading.BrokenBarrierError:
        pass
    

    t0 = time.perf_counter()

    current_session = {
        "is_logged_in": False,
        "session_id": None,
    }
    
    if run_num == 0:
        register_account_payload = {
            "action": "REGISTER",
            "username": f"test_seller_{seller_id}",
            "name": f"buyer_{seller_id}",
            "password": f"test_seller_{seller_id}"
        }

        send_data_to_server(client_socket, register_account_payload)
        server_res = client_socket.recv(1024)
        last_response = record_output("REGISTER", server_res, result_q, t0)

    login_payload = {
        "action": "LOGIN",
        "username": f"test_seller_{seller_id}",
        "password": f"test_seller_{seller_id}"
    }

    t0 = time.perf_counter()

    send_data_to_server(client_socket, login_payload)
    server_res = client_socket.recv(1024)
    last_response = record_output("LOGIN", server_res, result_q, t0)

    session_id = last_response['session_id']

    j = 0
    for i in range(num_calls):
        total_actions = ['GET_RATING', 'REGISTER_PRODUCT', 'CHANGE_ITEM_PRICE', 'GET_RATING']

        selected_action = total_actions[j]
        j = (j + 1) % 4

        if selected_action == "GET_RATING":
            payload = {
                "action": "GET_RATING",
                "session_id": session_id,
            }
        elif selected_action == "REGISTER_PRODUCT":
            payload = {
                "action": "REGISTER_PRODUCT",
                "session_id": session_id,
                "name": "my_cycle",
                "category": 2,
                "keywords": ['cycle', 'child'],
                "condition": 0,
                "sale_price": 150.0,
                "quantity": 3
            }
        else:
            payload = {
                "action": "GET_RATING",
                "session_id": session_id,
            }

        t0 = time.perf_counter()
        send_data_to_server(client_socket, payload)
        server_res = client_socket.recv(1024)
        record_output(selected_action, server_res, result_q, t0)
    
    # Logging out
    payload = {
        "action": "LOGOUT",
        "session_id": session_id,
    }
    
    send_data_to_server(client_socket, payload)

    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()


def run_benchmark(num_buyer, num_seller, buyer_server_config, seller_server_config, num_runs, num_calls_per_req):
    barrier = threading.Barrier(num_buyer + num_seller)
    result_q = Queue()
    run_times = []
    init_time = time.perf_counter()
    for r in trange(num_runs):
        buyer_threads = [
            threading.Thread(
                target=buyer_client,
                args=(i, buyer_server_config, barrier, i, num_calls_per_req, result_q, r),
                daemon=True
            )
            for i in range(num_buyer)
        ]

        seller_threads = [
            threading.Thread(
                target=seller_client,
                args=(i, seller_server_config, barrier, i, num_calls_per_req, result_q, r),
                daemon=True
            )
            for i in range(num_seller)
        ]

        total_threads = buyer_threads + seller_threads

        for t in total_threads:
            t.start()
        
        t_start = time.perf_counter()

        for t in total_threads:
            t.join()

        t_end = time.perf_counter()
        elapsed_s = t_end - t_start
        run_times.append(elapsed_s)


    final_time = time.perf_counter()

    final_elapsed_time = final_time - init_time

    total_calls = (num_buyer + num_seller) * num_calls_per_req * num_runs

    total_call_times = []
    while not result_q.empty():
        temp = result_q.get()
        total_call_times.append(temp['elapsed_call_time'])
        # print(temp)

    print("TOTAL CALLS:", total_calls)
    print("ELAPSED TIME:", final_elapsed_time)
    print("RUN TIMES", run_times)
    print("Throughput:", total_calls / final_elapsed_time)
    print("Avg resp. time:", mean(total_call_times))
    print("Result")

def main():
    ap = argparse.ArgumentParser(description="TCP server throughput + latency benchmark")
    ap.add_argument("--buyer_host", default="0.0.0.0")
    ap.add_argument("--buyer_port", type=int, default=50000)
    ap.add_argument("--seller_host", default="0.0.0.0")
    ap.add_argument("--seller_port", type=int, default=50001)
    ap.add_argument("--num_buyer", type=int, default=100)
    ap.add_argument("--num_seller", type=int, default=100)
    ap.add_argument("--num_runs", type=int, default=10)
    ap.add_argument("--num_calls_per_run", type=int, default=1000)
    args = ap.parse_args()


    buyer_server_config = {
        "port": args.buyer_port,
        "host": args.buyer_host
    }

    seller_server_config = {
        "port": args.seller_port,
        "host": args.seller_host
    }

    run_benchmark(args.num_buyer, args.num_seller, buyer_server_config, seller_server_config, args.num_runs, args.num_calls_per_run)

if __name__ == "__main__":
    main()