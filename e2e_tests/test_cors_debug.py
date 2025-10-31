"""
Quick test to debug CORS issues
"""



def test_cors_debug(page):
    """Debug test for CORS issues"""
    page.goto("https://localhost:5173/store")

    # Wait a bit for page to load
    page.wait_for_timeout(2000)

    # Capture console logs
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

    # Capture network errors
    network_errors = []

    def handle_response(response):
        if not response.ok:
            network_errors.append(f"Failed: {response.url}")

    page.on("response", handle_response)

    # Wait for catalog to load
    page.wait_for_timeout(5000)

    # Print all console logs
    print("\n=== CONSOLE LOGS ===")
    for log in console_logs:
        print(log)

    # Print network errors
    print("\n=== NETWORK ERRORS ===")
    for error in network_errors:
        print(error)

    # Check if API was called
    print("\n=== CHECKING API CALLS ===")

    # Execute JavaScript to check what API URL is being used
    api_url = page.evaluate("window.__env ? window.__env.PUBLIC_API_URL : 'not found'")
    print(f"Browser sees PUBLIC_API_URL as: {api_url}")
