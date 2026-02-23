import argparse
import json
import threading
import time
import requests
from queue import Queue
from statistics import mean
from tqdm import trange

# --- Helper for REST Calls ---
def record_rest_output(action, response, record_list, initial_time):
    """Parses HTTP response and records latency."""
    t = time.perf_counter()
    elapsed_call_time = t - initial_time
    
    status = "fail"
    try:
        res_object = response.json()
        # Check for 'status' in body OR check HTTP status code
        if response.status_code < 400 and res_object.get('status') != 'ERROR':
            status = "success"
    except Exception:
        res_object = {"error": "Invalid JSON"}

    record_list.put({
        "action": action,
        "elapsed_call_time": elapsed_call_time,
        "status": status
    })
    return res_object

# --- Client Logic ---

def buyer_client(buyer_id, base_url, barrier, num_calls, result_q, run_num):
    session = requests.Session()
    try:
        barrier.wait()
    except threading.BrokenBarrierError:
        pass

    # 1. Register (Only on first run)
    if run_num == 0:
        t0 = time.perf_counter()
        resp = session.post(f"{base_url}/register", json={
            "username": f"test_buyer_{buyer_id}",
            "name": f"buyer_{buyer_id}",
            "password": f"test_buyer_{buyer_id}",
            "customer_type": 0 # Assuming 0 is BUYER in your proto
        })
        record_rest_output("REGISTER", resp, result_q, t0)

    # 2. Login
    t0 = time.perf_counter()
    resp = session.post(f"{base_url}/login", json={
        "username": f"test_buyer_{buyer_id}",
        "password": f"test_buyer_{buyer_id}",
        "customer_type": 0
    })
    login_res = record_rest_output("LOGIN", resp, result_q, t0)
    session_id = login_res.get('session_id')

    if not session_id: return

    # 3. Looping Actions
    actions = ['/products/search', '/cart/display', '/cart/save', '/cart/clear']
    for i in range(num_calls):
        selected_path = actions[i % len(actions)]
        t0 = time.perf_counter()
        
        if selected_path == '/products/search':
            # GET request with params
            resp = session.post(f"{base_url}{selected_path}", json={
                "category": 1,
                "keywords": ["cycle", "kids"],
                "session_id": session_id
            })
        else:
            # POST requests
            resp = session.post(f"{base_url}{selected_path}", json={"session_id": session_id})
        
        record_rest_output(selected_path, resp, result_q, t0)

def seller_client(seller_id, base_url, barrier, num_calls, result_q, run_num):
    session = requests.Session()
    try:
        barrier.wait()
    except threading.BrokenBarrierError:
        pass

    if run_num == 0:
        t0 = time.perf_counter()
        resp = session.post(f"{base_url}/register", json={
            "username": f"test_seller_{seller_id}",
            "name": f"seller_{seller_id}",
            "password": f"test_seller_{seller_id}",
            "customer_type": 1 # Assuming 1 is SELLER
        })
        record_rest_output("REGISTER", resp, result_q, t0)

    t0 = time.perf_counter()
    resp = session.post(f"{base_url}/login", json={
        "username": f"test_seller_{seller_id}",
        "password": f"test_seller_{seller_id}",
        "customer_type": 1
    })
    login_res = record_rest_output("LOGIN", resp, result_q, t0)
    session_id = login_res.get('session_id')

    if not session_id: return

    actions = ['/seller/rating', '/item/register', '/item/change_price']
    for i in range(num_calls):
        path = actions[i % len(actions)]
        t0 = time.perf_counter()
        
        if path == '/seller/rating':
            resp = session.post(f"{base_url}{path}", json={"session_id": session_id})
        elif path == '/item/register':
            resp = session.post(f"{base_url}{path}", json={
                "session_id": session_id,
                "name": "benchmark_item",
                "category": 2,
                "keywords": ["test"],
                "condition": 0,
                "sale_price": 99.9,
                "quantity": 10
            })
        else:
            resp = session.post(f"{base_url}{path}", json={
                "session_id": session_id,
                "item_id": 1,
                "sale_price": 1530.3
            })
        record_rest_output(path, resp, result_q, t0)

# --- Benchmark Runner ---

def run_benchmark(args):
    buyer_url = f"http://{args.buyer_host}:{args.buyer_port}"
    seller_url = f"http://{args.seller_host}:{args.seller_port}"
    
    result_q = Queue()
    total_run_times = []
    global_init = time.perf_counter()

    for r in trange(args.num_runs, desc="Runs"):
        barrier = threading.Barrier(args.num_buyer + args.num_seller)
        threads = []

        for i in range(args.num_buyer):
            threads.append(threading.Thread(target=buyer_client, args=(i, buyer_url, barrier, args.num_calls_per_run, result_q, r)))
        
        for i in range(args.num_seller):
            threads.append(threading.Thread(target=seller_client, args=(i, seller_url, barrier, args.num_calls_per_run, result_q, r)))

        t_start = time.perf_counter()
        for t in threads: t.start()
        for t in threads: t.join()
        total_run_times.append(time.perf_counter() - t_start)

    # Statistics
    final_time = time.perf_counter() - global_init
    all_latencies = []
    while not result_q.empty():
        all_latencies.append(result_q.get()['elapsed_call_time'])

    print(f"\n--- Results ---")
    print(f"Total Time: {final_time:.2f}s")
    print(f"Throughput: {len(all_latencies)/final_time:.2f} req/s")
    print(f"Average Latency: {mean(all_latencies)*1000:.2f} ms")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--buyer_host", default="localhost")
    ap.add_argument("--buyer_port", type=int, default=50000)
    ap.add_argument("--seller_host", default="localhost")
    ap.add_argument("--seller_port", type=int, default=50000)
    ap.add_argument("--num_buyer", type=int, default=10)
    ap.add_argument("--num_seller", type=int, default=10)
    ap.add_argument("--num_runs", type=int, default=10)
    ap.add_argument("--num_calls_per_run", type=int, default=5)
    run_benchmark(ap.parse_args())

if __name__ == "__main__":
    main()