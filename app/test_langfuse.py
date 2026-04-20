from dotenv import load_dotenv
load_dotenv(".env", override=True)

import os
from langfuse import get_client

print("PK =", os.getenv("LANGFUSE_PUBLIC_KEY"))
print("SK =", os.getenv("LANGFUSE_SECRET_KEY"))
print("BASE =", os.getenv("LANGFUSE_BASE_URL"))

langfuse = get_client()
print("Langfuse auth_check:", langfuse.auth_check())