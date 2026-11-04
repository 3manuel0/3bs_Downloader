#TODO: I want to refactor this project into a better version, Soon...

import requests
from video import generate_all_chats, add_svgs
import os
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import subprocess


session = requests.Session()
url = "https://visioconference.supmti.ac.ma/playback/presentation/2.3/f33e8d292a1a6a74eebafb39f3f73b5d77acc6a0-1793301368635"





def get_presentation_base(session_url : str):
    parsed = urlparse(session_url)

    session_id = parsed.path.rstrip("/").split("/")[-1]
    # print(f"{parsed.scheme}://{parsed.netloc}"
    #     f"/presentation/{session_id}/")
    return (
        f"{parsed.scheme}://{parsed.netloc}"
        f"/presentation/{session_id}/"
    )

base = get_presentation_base(url)

def download_file(url: str):
    try:
        filename = url.split("/")[-1]
        path = os.path.join("downloads", filename)

        print(f"Downloading: {url}")
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

probe(base, session)

for rel in shapes_refs(base, session):
    code, size = check(urljoin(base.rstrip("/") + "/", rel), session)
    print(f"{code:>3}  {str(size or ''):>20}  {rel}")

deskshare_url = urljoin(base, "deskshare/deskshare.webm")
webcams_url = urljoin(base, "video/webcams.webm")
# download_file(urljoin(base, "metadata.xml"))
# download_file(urljoin(base, "slides_new.xml",))


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
# test = check(urljoin(base, "deskshare/deskshare.webm"), session)
if(check(urljoin(base, "deskshare/deskshare.webm"), session)[0] == 206):
    print("deskshare found", check(urljoin(base, "deskshare/deskshare.webm"), session)[0]);
# if not os.path.exists("downloads/deskshare.webm"):
#     svgs = get_svgs()
#     images = []
#     for i, svg in enumerate(svgs):
#         print("https://visioconference.supmti.ac.ma/presentation/" + id + "/" + svg.href)

#         if svg.href.endswith(".svg"):
#             svg_url = "https://visioconference.supmti.ac.ma/presentation/" + id + "/"  + svg.href
#             print(svg_url)
#             # converting svg into png whith high dpi 
#             png_data = cairosvg.svg2png(url=svg_url, dpi=300)
            
#             # reading png insuring it's rgba
#             img = Image.open(BytesIO(png_data)).convert("RGBA")
#             # creating new white background
#             bg = Image.new("RGB", img.size, (255, 255, 255))  
#             # put the img on top of the mask 
#             bg.paste(img, mask=img.split()[3])  
#             bg = bg.resize((1280, 720), Image.LANCZOS)
#             img_name = f"{i:04d}.png"
#             images.append((os.path.join("frames", img_name), svg.start, svg.end))
#             bg.save(f"frames/{img_name}")
#     try:
#         subprocess.run([
#             "ffmpeg",
#             "-y",
#             "-i", "downloads/webcams.webm",
#             "-vf", "scale=1280:720",
#             "-preset", "ultrafast",
#             "-c:v", "libx264",
#             "-c:a", "copy",
#             "output.mp4"
#         ])

#         video.add_svgs(images, "output.mp4", "pre_chat.mp4")



# generate_all_chats("pre_chat.mp4", "out.mp4");