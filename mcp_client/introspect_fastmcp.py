import fastmcp
import fastmcp.client
import fastmcp.client.sampling
import inspect

print("=== fastmcp ===")
for name, obj in inspect.getmembers(fastmcp):
    print(name, obj)

print("\n=== fastmcp.client ===")
for name, obj in inspect.getmembers(fastmcp.client):
    print(name, obj)

print("\n=== fastmcp.client.sampling ===")
for name, obj in inspect.getmembers(fastmcp.client.sampling):
    print(name, obj)
