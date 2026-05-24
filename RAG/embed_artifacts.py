import json
import sys
from pathlib import Path

import httpx


def embed_file(file_path: str):
    url = "http://localhost:8101/v1/embed"
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File {file_path} not found.")
        return

    # Read and stringify the JSON content
    with open(path, "r") as f:
        data = json.load(f)
        text_to_embed = json.dumps(data)

    payload = {
        "text": text_to_embed,
        "task_type": "clustering",  # Optional task type
        "provider": "ollama",
        "model": "nomic-embed-text",
    }

    print(f"Sending {file_path} to {url}...")

    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            print("\n--- Embedding Result ---")
            print(f"Provider:  {result['provider']}")
            print(f"Model:     {result['model']}")
            print(f"Dimension: {result['dimension']}")
            print(f"Latency:   {result['latency_ms']}ms")
            print(f"Vector (first 5): {result['embedding'][:5]}...")

    except Exception as e:
        print(f"Failed to get embedding: {e}")


if __name__ == "__main__":
    target = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "sandbox/artifacts/state/durable_state.json"
    )
    embed_file(target)
