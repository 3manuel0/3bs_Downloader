import requests
import os 
from dataclasses import dataclass
from playwright.sync_api import sync_playwright
import xml.etree.ElementTree as ET
import cairosvg
import html
from io import BytesIO
from PIL import Image
import subprocess
import shutil
import video

# TODO : BETTER TO CREAT A CLASS THAT DOES EVERYTHING LATER OR MAYBE 2 CLASSES 

@dataclass
class SVG:
    href:str
    start : float
    end: float
    
downloaded = set()
# MEDIA_EXTENSIONS = (".webm", ".xml", ".json")
MEDIA_EXTENSIONS = (".webm",".xml", ".json", "shapes.svg")

os.makedirs("downloads", exist_ok=True)
os.makedirs("frames", exist_ok=True)
os.makedirs("chats", exist_ok=True)

def parse_time(time :str)->int:
    split = time.split(":")
    if(len(split) != 2): 
        return 0
    seconds = 0
    try:
        hours = int(split[0])
        minutes = int(split[1])
        if minutes > 59:
            raise ValueError("minutes > 59")
        seconds += (hours * 3600) + (minutes * 60)
    except Exception as e:
        print(e)
        print("Error in format")
        return 0
    return seconds

def empty_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # delete file
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # delete folder
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")

def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print("File deleted.")

def clean_all():
    empty_folder("downloads")
    empty_folder("frames") 
    empty_folder("chats")   
    remove_file("output.mp4")

def download_file(url: str, video_len: int):
    try:
        filename = url.split("/")[-1]
        path = os.path.join("downloads", filename)
        if filename in downloaded:
            return
        downloaded.add(filename)
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

def get_svgs()->list[SVG]:
    tree = ET.parse("downloads/shapes.svg")
    root = tree.getroot()
    images = root.findall(".//{http://www.w3.org/2000/svg}image")
    svgs = []
    for e in images:
        svg = SVG(e.get("{http://www.w3.org/1999/xlink}href"), float(e.get("in")), float(e.get("out")))
        svgs.append(svg)
    return svgs

def get_dynamic_soup(url: str, video_len: int):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)

        def handle_response(response):
            url = response.url
            if url.lower().endswith(MEDIA_EXTENSIONS):
                # pass
                download_file(url, video_len)

        page.on("response", handle_response)
        page.wait_for_timeout(5000)
        browser.close()


# main start of the script
if __name__ == "__main__":

    START_URL = input("Enter The Full Link of The Presentation: ")
    TIME = input("Enter The duration of the video (exactly as this format hh:mm example 00:55 or 01:45): ")
    VIDEO_LEN = parse_time(TIME)

    print(VIDEO_LEN)
    get_dynamic_soup(START_URL, VIDEO_LEN)

    if not os.path.exists("downloads/metadata.xml"):
        print("no metadata.xml, could be a wrong website")
        exit(1)

    tree = ET.parse("downloads/metadata.xml")
    root = tree.getroot()
    id = root.find("id").text
    file_name = html.unescape(root.find(".//bbb-context").text)

    for i in [":", "/", "?"]:
        file_name = file_name.replace(i, "_")

    if not os.path.exists("downloads/deskshare.webm"):
        svgs = get_svgs()
        images = []
        for i, svg in enumerate(svgs):
            print("https://visioconference.supmti.ac.ma/presentation/" + id + "/" + svg.href)

            if svg.href.endswith(".svg"):
                svg_url = "https://visioconference.supmti.ac.ma/presentation/" + id + "/"  + svg.href
                print(svg_url)
                # converting svg into png whith high dpi 
                png_data = cairosvg.svg2png(url=svg_url, dpi=300)
                
                # reading png insuring it's rgba
                img = Image.open(BytesIO(png_data)).convert("RGBA")
                # creating new white background
                bg = Image.new("RGB", img.size, (255, 255, 255))  
                # put the img on top of the mask 
                bg.paste(img, mask=img.split()[3])  
                bg = bg.resize((1280, 720), Image.LANCZOS)
                img_name = f"{i:04d}.png"
                images.append((os.path.join("frames", img_name), svg.start, svg.end))
                bg.save(f"frames/{img_name}")
        try:
            subprocess.run([
                "ffmpeg",
                "-y",
                "-i", "downloads/webcams.webm",
                "-vf", "scale=1280:720",
                "-preset", "ultrafast",
                "-c:v", "libx264",
                "-c:a", "copy",
                "output.mp4"
            ])

            video.add_svgs(images, "output.mp4", "pre_chat.mp4")
            video.generate_all_chats(output_fname=file_name + ".mp4")
        except Exception as e:
            clean_all()
            print(f"error occured {e}")
    else:
        
        try: 
            subprocess.run([
                "ffmpeg",
                "-y",                  
                "-i", "downloads/deskshare.webm",   
                "-i", "downloads/webcams.webm",  
                "-map", "0:v:0",       
                "-map", "1:a:0",       
                "-c:v", "copy",        
                "-c:a", "copy",        
                "-shortest",           
                "pre_chat" + ".mp4"           
            ], check=True)
            svgs = get_svgs()
            images = []
            print(get_svgs())
            for i, svg in enumerate(svgs):
                print(svg)
                if svg.href.endswith(".svg"):
                    svg_url = "https://visioconference.supmti.ac.ma/presentation/" + id + "/"  + svg.href
                    print(svg_url)
                    # converting svg into png whith high dpi 
                    png_data = cairosvg.svg2png(url=svg_url, dpi=300)
                    # reading png insuring it's rgba
                    img = Image.open(BytesIO(png_data)).convert("RGBA")
                    bg = Image.new("RGB", img.size, (255, 255, 255))  
                    bg.paste(img, mask=img.split()[3]) 
                    # resize to 1280 x 720
                    bg = bg.resize((1280, 720), Image.LANCZOS)
                    img_name = f"{i:04d}.png"
                    images.append((os.path.join("frames", img_name), svg.start, svg.end))
                    bg.save(f"frames/{img_name}")
                elif svg.href.endswith(".png") and not svg.href.endswith("deskshare.png"):
                    png_url = "https://visioconference.supmti.ac.ma/presentation/" + id + "/"  + svg.href
                    print(png_url)
                    png_data = requests.get(png_url).content
                    # reading png insuring it's rgba
                    img = Image.open(BytesIO(png_data)).convert("RGBA")
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3]) 
                    # resize to 1280 x 720
                    bg = bg.resize((1280, 720), Image.LANCZOS)
                    img_name = f"{i:04d}.png"
                    images.append((os.path.join("frames", img_name), svg.start, svg.end))
                    bg.save(f"frames/{img_name}")
            video.add_svgs(images, "pre_chat.mp4")
            video.generate_all_chats(output_fname=file_name + ".mp4")
        except Exception as e:
            clean_all()
            print(f"error occured {e}")

    clean_all()
    print("All done File Created")


