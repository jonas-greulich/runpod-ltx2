import runpod
import subprocess
import time
import json
import urllib.request
import base64
import os
import sys

COMFY_PORT = 8188
COMFY_URL = f"http://127.0.0.1:{COMFY_PORT}"
comfy_process = None


def start_comfyui():
    global comfy_process
    os.makedirs("/tmp/comfy_output", exist_ok=True)
    comfy_process = subprocess.Popen(
        [
            sys.executable,
            "/app/ComfyUI/main.py",
            "--listen", "0.0.0.0",
            "--port", str(COMFY_PORT),
            "--output-directory", "/runpod-volume/output",
            "--extra-model-paths-config", "/app/extra_model_paths.yaml",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print("Waiting for ComfyUI to start...")
    for _ in range(90):
        try:
            urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=2)
            print("ComfyUI is ready.")
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("ComfyUI did not start within 180 seconds.")


def queue_workflow(workflow: dict) -> str:
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["prompt_id"]


def wait_for_output(prompt_id: str, timeout: int = 900) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(
                f"{COMFY_URL}/history/{prompt_id}", timeout=5
            ) as resp:
                history = json.loads(resp.read())
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                for node_output in outputs.values():
                    for key in ("gifs", "videos", "images"):
                        if key in node_output and node_output[key]:
                            return node_output[key][0]["filename"]
        except Exception:
            pass
        time.sleep(3)
    raise TimeoutError(f"Job {prompt_id} did not complete within {timeout}s.")


def handler(job):
    job_input = job.get("input", {})
    workflow = job_input.get("workflow")
    quality = job_input.get("quality", "draft")

    if not workflow:
        return {"error": "No workflow provided."}

    # Draft-Modus: niedrige Auflösung + wenige Steps für schnelle Iteration
    if quality == "draft":
        for node in workflow.values():
            ctype = node.get("class_type", "")
            inputs = node.get("inputs", {})
            if ctype == "EmptyLTXVLatentVideo":
                inputs["width"] = 512
                inputs["height"] = 288
            if ctype in ("KSampler", "LTXVSampler"):
                inputs["steps"] = min(inputs.get("steps", 20), 8)

    prompt_id = queue_workflow(workflow)
    print(f"Queued prompt_id: {prompt_id}")

    filename = wait_for_output(prompt_id)
    output_path = f"/tmp/comfy_output/{filename}"

    with open(output_path, "rb") as f:
        video_b64 = base64.b64encode(f.read()).decode("utf-8")

    return {
        "video_base64": video_b64,
        "filename": filename,
        "prompt_id": prompt_id,
        "quality": quality,
    }


start_comfyui()
runpod.serverless.start({"handler": handler})
