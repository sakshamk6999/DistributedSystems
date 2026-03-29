from backend.customer_db_service import start_server
import argparse
import asyncio

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