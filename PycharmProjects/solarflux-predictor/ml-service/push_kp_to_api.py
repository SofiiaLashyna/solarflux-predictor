import requests
from data_loader import load_kp_gfz

API_URL = "http://localhost:8080/api/observations/batch"


def push_kp(start, end, chunk_size=1000):
    kp = load_kp_gfz(start, end)
    records = [
        {
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": "KP_INDEX",
            "value": float(value),
            "source": "GFZ",
        }
        for ts, value in kp.items()
    ]
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        response = requests.post(API_URL, json=chunk, timeout=60)
        response.raise_for_status()
        print(f"Відправлено {i + len(chunk)}/{len(records)}")


if __name__ == "__main__":
    push_kp("2021-01-01T00:00:00Z", "2025-12-31T23:59:59Z")