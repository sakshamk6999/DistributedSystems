import asyncio
import httpx
import sys
import os
import json

BASE_URL = os.getenv("MIDDLEWARE_URL", "http://localhost:50000")

current_session = {
    "is_logged_in": False,
    "session_id": None,
}

async def handle_register(client: httpx.AsyncClient, args):
    if 'username' not in args:
        print("username missing. Please try again.")
        return
    
    if 'password' not in args:
        print("password missing. Please try again.")
        return
    
    if 'name' not in args:
        print("name missing. Please try again.")
        return
    
    try:
        response = await client.post(f"{BASE_URL}/register", json=args)
        res_object = response.json()
        # Mapping REST response to your existing print logic
        if response.status_code == 200:
            print(f"Success: {res_object}")
            # print("User ID:", res_object.get('id') or res_object.get('user_id'))
        else:
            print(f"ERROR: {res_object.get('message', 'Unknown error')}")


    except Exception as e:
        print(f"Connection Error: {e}")


async def handle_login(client: httpx.AsyncClient, args):
    if 'username' not in args:
        print("username missing. Please try again.")
        return
    
    if 'password' not in args:
        print("password missing. Please try again.")
        return
    
    try:
        response = await client.post(f"{BASE_URL}/login", json=args)
        res_object = response.json()

        if response.status_code == 200:
            print("Login Successful!")
            current_session['is_logged_in'] = True
            current_session['session_id'] = res_object.get('session_id')
            print(f"Success: {res_object}")
        else:
            print(f"ERROR: {res_object.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"Connection Error: {e}")

async def handle_logout(client: httpx.AsyncClient):
    if not current_session['is_logged_in']:
        print("Invalid action. You should be logged in first.")
        return

    try:
        # Standard REST: session usually goes in headers or body
        headers = {"Authorization": current_session['session_id']}
        response = await client.post(f"{BASE_URL}/logout", headers=headers)
        
        if response.status_code == 200:
            print("Logged out successfully.")
            current_session['is_logged_in'] = False
            current_session['session_id'] = None
        else:
            print("Logout failed.")
    except Exception as e:
        print(f"Error: {e}")


ACTION_MAP = {
    'GET_RATING': '/seller/rating',
    'REGISTER_ITEM': '/item/register',
    'CHANGE_PRICE': '/item/change_price',
}

async def handle_common_request(client: httpx.AsyncClient, args, command):
    if not current_session['is_logged_in']:
        print("Please login first.")
        return
    
    params = {
        **args,
        'session_id': current_session['session_id']
    }

    print
    response = await client.post(f"{BASE_URL}{ACTION_MAP[command]}", json=params)
    res_object = response.json()

    if response.status_code == 200:
        print(f"Output: {res_object}")
    else:
        print(f"Search Error: {res_object.get('message')}")



async def process_command(client: httpx.AsyncClient, cmd_input: str):
    """Parses the seller> input and routes to the correct async handler."""
    parts = cmd_input.split("--")
    command = parts[0].strip().upper()

    # Parse flags: --username dev --password 123 -> {'username': 'dev', 'password': '123'}
    args = {}
    for option in parts[1:]:
        temp = option.strip().split()
        if len(temp) == 2:
            args[temp[0]] = temp[1]
        elif len(temp) > 2:
            args[temp[0]] = temp[1:]
    print("Args are:", args)
    if command == 'REGISTER':
        await handle_register(client, args)
    elif command == 'LOGIN':
        await handle_login(client, args)
    elif command == 'LOGOUT':
        await handle_logout(client)
    elif command == 'DISCONNECT' or command == 'EXIT':
        print("Closing client...")
        return False
    else:
        await handle_common_request(client, args, command)
    return True

async def main():
    print(f"--- REST Seller Client Started (Connecting to {BASE_URL}) ---")
    
    # Use a single AsyncClient for connection pooling
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Use run_in_executor to prevent input() from blocking the event loop
                # loop = asyncio.get_event_loop()
                # cmd_input = await loop.run_in_executor(None, lambda: input("buyer> ").strip())
                
                # if not cmd_input:
                #     continue
                print("Type the next command")
                cmd_input = input("seller> ").strip()
                
                should_continue = await process_command(client, cmd_input)
                if not should_continue:
                    break
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())