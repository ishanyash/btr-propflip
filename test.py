# test_env.py
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Print environment variables
print(f"EPC_API_EMAIL: {os.getenv('EPC_API_EMAIL')}")
print(f"EPC_API_KEY: {os.getenv('EPC_API_KEY')}")