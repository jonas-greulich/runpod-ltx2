import os
import requests
import json
import base64
import time

API_KEY = os.environ.get("RUNPOD_API_KEY", "")
ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "44474we5w627g9")

with open("workflows/ltx2_draft.json") as f:
    workflow = json.load(f)

r = requests.post(
    f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"input": {"workflow": workflow, "quality": "draft"}},
)
r.raise_for_status()
job_id = r.json()["id"]
print(f"Job gestartet: {job_id}")

while True:
    s = requests.get(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}",
        headers={"Authorization": f"Bearer {API_KEY}"},
    ).json()
    print(f"Status: {s['status']}")
    if s["status"] == "COMPLETED":
        output = s.get("output", {})
        if "video_base64" not in output:
            print("Fertig, aber kein Video im Output:", output)
            break
        with open("output.mp4", "wb") as f:
            f.write(base64.b64decode(output["video_base64"]))
        print("Gespeichert: output.mp4")
        break
    elif s["status"] == "FAILED":
        print("Fehler:", json.dumps(s, indent=2))
        break
    time.sleep(5)
