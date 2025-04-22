import uvicorn
import logfire

logfire.configure(service_name="server_agent")

if __name__ == "__main__":
    logfire.configure(service_name="server_agent")
    logfire.info("server_start", msg="Starting server with uvicorn")
    uvicorn.run("agent:app", host="0.0.0.0", port=8080, reload=False)
