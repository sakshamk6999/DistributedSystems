import socket
import socket
import sys
import os
import argparse
import json

current_session = {
    "is_logged_in": False,
    "session_id": None,
}

CMDS_MAP = ["REGISTER", "LOGIN", "LOGOUT", "PRODUCT_SEARCH", "ADD_ITEM", "REMOVE_ITEM", "SAVE_CART", "CLEAR_CART", "DISPLAY_CART", "PROVIDE_FEEDBACK", ]

def send_data_to_server(client_socket: socket.socket, args):
    json_string = json.dumps(args)
    data_bytes = json_string.encode('utf-8')
    # print("sending", json_string)
    client_socket.sendall(data_bytes)

def handle_register(client_socket: socket.socket, args):
    if 'username' not in args:
        print("username missing. Please try again.")
        return
    
    if 'password' not in args:
        print("password missing. Please try again.")
        return
    
    if 'name' not in args:
        print("name missing. Please try again.")
        return
    
    send_data_to_server(client_socket, args)

    server_res = client_socket.recv(1024)
    # print(f"Received {server_res}")
    decoded_string = server_res.decode("utf-8")
    res_object = json.loads(decoded_string)

    if res_object['status'] == "OK":
        print(res_object['message'])
        print("User ID:", res_object['id'])
    else:
        print("ERROR in response")
        print(res_object['message'])

def handle_login(client_socket: socket.socket, args):
    if 'username' not in args:
        print("username missing. Please try again.")
        return
    
    if 'password' not in args:
        print("password missing. Please try again.")
        return

    send_data_to_server(client_socket, args)

    server_res = client_socket.recv(1024)
    # print(f"Received {server_res}")
    decoded_string = server_res.decode("utf-8")
    res_object = json.loads(decoded_string)

    if res_object['status'] == "OK":
        print(res_object['message'])
        current_session['is_logged_in'] = True
        current_session['session_id'] = res_object['session_id']
        print("Session ID:", res_object['session_id'])
    else:
        print("ERROR in response")
        print(res_object['message'])

def handle_logout(client_socket: socket.socket, args):
    if not current_session['is_logged_in'] or current_session['session_id'] == None:
        print("Invalid action. You should be logged in first.")
        return
    req_obj = {
        "action": "LOGOUT",
        'session_id': current_session['session_id']
    }

    send_data_to_server(client_socket, req_obj)

    server_res = client_socket.recv(1024)
    # print(f"Received {server_res}")
    decoded_string = server_res.decode("utf-8")
    res_object = json.loads(decoded_string)

    if res_object['status'] == "OK":
        print(res_object['message'])
        current_session['is_logged_in'] = False
        current_session['session_id'] = None
    else:
        print("ERROR in response")
        print(res_object['message'])

def handle_common_request(client_socket: socket.socket, args):
    if not current_session['is_logged_in'] or current_session['session_id'] == None:
        print("Invalid action. You should be logged in first.")
        return

    req_obj = {
        **args,
        'session_id': current_session['session_id']
    }
    
    send_data_to_server(client_socket, req_obj)

    server_res = client_socket.recv(1024)
    # print(f"Received {server_res}")
    decoded_string = server_res.decode("utf-8")
    res_object = json.loads(decoded_string)

    if res_object['status'] == "OK":
        print(res_object)
    else:
        print("ERROR in response")
        print(res_object['message'])

# def handle_register_product(client_socket: socket.socket, args):
#     if not current_session['is_logged_in'] or current_session['session_id'] == None:
#         print("Invalid action. You should be logged in first.")
#         return
    
#     req_obj = {
#         **args,
#         'session_id': current_session['session_id']
#     }

#     send_data_to_server(client_socket, req_obj)

#     server_res = client_socket.recv(1024)
#     print(f"Received {server_res}")
#     decoded_string = server_res.decode("utf-8")
#     res_object = json.loads(decoded_string)

#     if res_object['status'] == "OK":
#         print(f"{res_object['message']}")
#     else:
#         print("ERROR in response")
#         print(res_object['message'])

def handle_client_cmd(client_socket: socket.socket, received_cmd):
    received_cmd = received_cmd.split("--")

    command = received_cmd[0].strip()

    args = {}
    args['action'] = command
    for option in received_cmd[1:]:
        temp = option.strip().split()
        
        if len(temp) == 2:
            args[temp[0]] = temp[1]
        if len(temp) > 2:
            args[temp[0]] = temp[1:]
    
    if command == 'REGISTER':
        handle_register(client_socket, args)
    elif command == "LOGIN":
        handle_login(client_socket, args)
    elif command == "LOGOUT":
        handle_logout(client_socket, args)
    elif command == "GET_RATING":
        handle_common_request(client_socket, args)
    elif command == "REGISTER_PRODUCT":
        handle_common_request(client_socket, args)
    elif command == "CHANGE_ITEM_PRICE":
        handle_common_request(client_socket, args)
    elif command == "UPDATE_UNITS_FOR_SALE":
        handle_common_request(client_socket, args)
    elif command == "DISPLAY_ITEMS_FOR_SALE":
        handle_common_request(client_socket, args)
    elif command == "DISCONNECT":
        print("Disconnecting with the server")
        client_socket.shutdown(socket.SHUT_RDWR)
        sys.exit(0)

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("Trying to connect to the Buyer Server")

    try:
        server_host = os.getenv("SELLER_SERVER_HOST", "0.0.0.0")
        server_port = int(os.getenv("SELLER_SERVER_PORT", 50001))
        client_socket.connect((server_host, server_port))
        
        print("Connected to the SERVER !")

        while True:
            print("Type the next command")
            cmd_input = input("seller> ").strip()

            print("Received command", cmd_input.split("--"))

            handle_client_cmd(client_socket, cmd_input)
    except ConnectionRefusedError:
        print("Connection refused. Make sure the container is running.")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()