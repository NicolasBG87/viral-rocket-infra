import os
import requests


def shutdown_pod():
    pod_id = os.getenv("RUNPOD_POD_ID")
    api_key = os.getenv("RUNPOD_API_KEY")

    if not pod_id or not api_key:
        print("🔒 No RUNPOD_POD_ID or RUNPOD_API_KEY provided — cannot auto-shutdown.")
        return

    url = "https://api.runpod.io/graphql"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "query": """
            mutation TerminatePod($input: PodTerminateInput!) {
                podTerminate(input: $input)
            }
        """,
        "variables": {
            "input": {
                "podId": pod_id
            }
        }
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        print("🛑 Pod successfully requested termination!")
    else:
        print(f"❌ Failed to shutdown pod: {response.text}")
