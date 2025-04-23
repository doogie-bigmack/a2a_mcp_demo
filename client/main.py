import argparse
from agent import A2AClient
import logfire
import json

logfire.configure(service_name="client_main")


def main():
    """
    Main entry point for the A2A Dockerfile Security Client.
    """
    parser = argparse.ArgumentParser(
        description="A2A Dockerfile Security Client"
    )
    parser.add_argument(
        "--dockerfile",
        type=str,
        help="Path to Dockerfile or Compose YAML",
        required=True,
    )
    parser.add_argument(
        "--server-url",
        type=str,
        default="http://server:8080",
        help="Security agent URL",
    )
    args = parser.parse_args()

    try:
        try:
            with open(args.dockerfile, "r") as f:
                dockerfile_text = f.read()
        except Exception as e:
            logfire.error("client_file_read_error", error=str(e))
            logfire.info(
                "client_file_read_error_json", error="Failed to read Dockerfile", details=str(e)
            )
            return

        try:
            client = A2AClient(args.server_url)
            result = client.send_dockerfile(dockerfile_text)
            if isinstance(result, dict) and "error" in result:
                logfire.error("client_send_dockerfile_error", error=result["error"])
                logfire.info(
                    "client_send_dockerfile_error_json",
                    error="Failed to send Dockerfile",
                    details=result["error"],
                )
            else:
                logfire.info("client_send_dockerfile_success", result=result)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logfire.error(
                "client_unhandled_exception", error=str(e), traceback=tb
            )
            logfire.info(
                "client_unhandled_exception_json",
                error="Unhandled client exception",
                details=str(e),
                traceback=tb,
            )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logfire.error(
            "client_fatal_exception", error=str(e), traceback=tb
        )
        logfire.info(
            "client_fatal_exception_json",
            error="Fatal client exception",
            details=str(e),
            traceback=tb,
        )


if __name__ == "__main__":
    main()
