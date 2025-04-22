from fastmcp.client import Client
import inspect

print("Client methods and docstrings:\n")
for name, obj in inspect.getmembers(Client):
    if not name.startswith("__"):
        print(f"{name}: {getattr(obj, '__doc__', '')}")
