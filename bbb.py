#TODO: I want to refactor this project into a better version, Soon...

import requests
import os
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import subprocess
from video import generate_all_chats

def get_presentation_base(session_url : str):
    parsed = urlparse(session_url)

    session_id = parsed.path.rstrip("/").split("/")[-1]
    print(f"{parsed.scheme}://{parsed.netloc}"
        f"/presentation/{session_id}/")
    return (
        f"{parsed.scheme}://{parsed.netloc}"
        f"/presentation/{session_id}/"
    )

def download_file(url: str, video_len: int):
    try:
        filename = url.split("/")[-1]
        path = os.path.join("downloads", filename)

        print(f"Downloading: {url}")
        if filename.endswith(".webm"):
            cmd = []
            if video_len > 0:
                cmd = ["ffmpeg", "-ss", "0", "-i", url,"-t", f"{video_len}", "-c", "copy", f"{path}"]
            else:
                cmd = ["ffmpeg", "-ss", "0", "-i", url, "-c", "copy", f"{path}"]
            subprocess.run(cmd, check=True)     
        else:
            r = requests.get(url, stream=True, timeout=20)
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
    except Exception as e:
        print(f"Failed: {url} -> {e}")


def check(url, session):
    request = session.get(
        url,
        headers={"Range": "bytes=0-0"},
        timeout=15,
        stream=True,
    )
    request.close()
    size = request.headers.get("Content-Range") or request.headers.get("Content-Length")
    return request.status_code, size

def probe(base, session):
    base = base.rstrip("/") + "/"
    candidates = [
        "metadata.xml",
        "shapes.svg",
        "slides_new.xml",
        "video/webcams.webm",
        "video/webcams.mp4",
        "deskshare/deskshare.webm",
        "deskshare/deskshare.mp4",
        "presentation/deskshare.png",
    ]
    for rel in candidates:
        code, size = check(urljoin(base, rel), session)
        print(f"{code:>3}  {str(size or ''):>20}  {rel}")

def shapes_refs(base, session):
    base = base.rstrip("/") + "/"
    xml = session.get(urljoin(base, "shapes.svg"), timeout=15).content
    root = ET.fromstring(xml)
    return sorted({
        e.get("{http://www.w3.org/1999/xlink}href")
        for e in root.findall(".//{http://www.w3.org/2000/svg}image")
    })
# Then probe the discovered refs too:
session = requests.Session()
url = "https://visioconference.supmti.ac.ma/playback/presentation/2.3/f33e8d292a1a6a74eebafb39f3f73b5d77acc6a0-1793301368635"
base = get_presentation_base(url)
probe(base, session)

for rel in shapes_refs(base, session):
    code, size = check(urljoin(base.rstrip("/") + "/", rel), session)
    print(f"{code:>3}  {str(size or ''):>20}  {rel}")

deskshare_url = urljoin(base, "deskshare/deskshare.webm")
webcams_url = urljoin(base, "video/webcams.webm")
download_file(urljoin(base, "metadata.xml"),0)
download_file(urljoin(base, "slides_new.xml",), 0)


# subprocess.run([
#     "ffmpeg",
#     "-y",
#     "-i", deskshare_url,
#     "-i", webcams_url,
#     "-map", "0:v:0",
#     "-map", "1:a:0",
#     "-c:v", "copy",
#     "-c:a", "copy",
#     "-shortest",
#     "pre_chat.mp4"
# ], check=True)

generate_all_chats("pre_chat.mp4", "out.mp4");