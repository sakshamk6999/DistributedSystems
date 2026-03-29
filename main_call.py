from backend.test.customer_db_test import run
import argparse
import asyncio

if __name__ == "__main__":

    print("making a request")
    asyncio.run(run())