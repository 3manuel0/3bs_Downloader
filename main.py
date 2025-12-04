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

downloaded = set()
# START_URL = "https://visioconference.supmti.ac.ma/playback/presentation/2.3/8ab678ec2baf0cbcf1e315136084dcde33f2ebfd-1762191511958/"
#START_URL = "https://visioconference.supmti.ac.ma/playback/presentation/2.3/0a2f3631b67c280930e9b313a0d716ce597b7018-1762888173315"
START_URL = input("Enter The Full Link of The Presentation: ")
time = input("Enter The length of the video (example 1h30 or 80m): ")

def parse_time(time :str)->int:
    seconds = 0.0
    try:
        index_h = list(time).index("h")
        seconds += int(time[0:index_h]) * 3600.0
        if len(time) > index_h + 1:
            time = time[index_h + 1:]
            if "m" in time and len(time) <= 3:
                seconds += int(time[0:-1]) * 60
            elif len(time) < 3:
                seconds += int(time) * 60
    except Exception as e:
        print(e)
        try:
            index_m = list(time).index("m")
            seconds += int(time[0:index_m]) * 60.0
            print(list(time)[0:index_m], time[index_m])
        except:
            seconds = 0
            print("wrong time, the full duration will be used")
    return seconds

VIDEO_LEN = parse_time(time)


print(VIDEO_LEN)

@dataclass
class SVG:
    href:str
    start : float
    end: float


# MEDIA_EXTENSIONS = (".webm", ".xml", ".json")
MEDIA_EXTENSIONS = (".webm",".xml", ".json", "shapes.svg")

index = 0
os.makedirs("downloads", exist_ok=True)
os.makedirs("svgs", exist_ok=True)
os.makedirs("frames", exist_ok=True)
os.makedirs("chats", exist_ok=True)

def empty_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # delete file or symlink
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # delete folder
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")

def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print("File deleted.")


def download_file(url):
    try:
        filename = url.split("/")[-1]
        path = os.path.join("downloads", filename)
        if filename in downloaded:
            return
        downloaded.add(filename)
        print(f"Downloading: {url}")
        if filename.endswith(".webm"):
            cmd = []
            if VIDEO_LEN > 0:
                cmd = ["ffmpeg", "-ss", "0", "-i", url,"-t", f"{VIDEO_LEN}", "-c", "copy", f"{path}"]
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


def get_dynamic_soup(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)

        def handle_response(response):
            url = response.url
            if url.lower().endswith(MEDIA_EXTENSIONS):
                download_file(url)

        page.on("response", handle_response)
        page.wait_for_timeout(5000)
        browser.close()

def download_svgs(url):
    global index
    try:
        ext = "".join(list(url)[-4:])
        print(ext)
        filename = str(index) + ext
        path = os.path.join("svgs", filename)
        if filename in downloaded:
            return
        downloaded.add(filename)
        print(f"Downloading: {url}")
        r = requests.get(url, stream=True, timeout=20)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    except Exception as e:
        print(f"Failed: {url} -> {e}")

get_dynamic_soup(START_URL)

if not os.path.exists("downloads/metadata.xml"):
    print("no metadata.xml, could be a wrong website")
    exit(1)

tree = ET.parse("downloads/metadata.xml")
root = tree.getroot()
id = root.find("id").text
file_name = html.unescape(root.find(".//bbb-context").text)
for i in [":", "/", "?"]:
    file_name = file_name.replace(i, "_")

def get_svgs()->list[SVG]:
    tree = ET.parse("downloads/shapes.svg")
    root = tree.getroot()
    images = root.findall(".//{http://www.w3.org/2000/svg}image")
    svgs = []
    for e in images:
        svg = SVG(e.get("{http://www.w3.org/1999/xlink}href"), float(e.get("in")), float(e.get("out")))
        svgs.append(svg)
    return svgs



if not os.path.exists("downloads/deskshare.webm"):
    svgs = get_svgs()
    images = []
    for i, svg in enumerate(svgs):
        print("https://visioconference.supmti.ac.ma/presentation/" + id + "/" + svg.href)
        # headers = {
        #     "User-Agent": "Mozilla/5.0",  # mimic a real browser
        #     }
        # response = requests.get("https://visioconference.supmti.ac.ma/presentation/" + id + "/"  + svg, stream=True, timeout=40)
        # response = requests.get(START_URL + svg, headers=headers)
        # download_svgs("https://visioconference.supmti.ac.ma/presentation/" + id + "/"  + svg.href)
        # svg_data = response.content
        # try:
        # concat_file = os.path.join(temp_dir, "file_list.txt")
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

    # subprocess.run([
    #     "ffmpeg",
    #     "-y",
    #     "-f", "concat",
    #     "-safe", "0",
    #     "-i", "file.txt",
    #     "-vsync", "vfr",
    #     "-c:v", "libvpx-vp9",
    #     "-pix_fmt", "yuv420p",
    #     "-crf", "30",         
    #     "-b:v", "0",           
    #     "output.webm"
    # ])
    # subprocess.run([
    #     "ffmpeg", "-y",
    #     "-f", "concat", "-safe", "0",
    #     "-i", "file.txt",
    #     "-vf", "fps=30",
    #     "-c:v", "libvpx-vp9",
    #     "-pix_fmt", "yuv420p",
    #     "-crf", "30",
    #     "-b:v", "0",
    #     "output.webm"
    # ])
# try:
    # subprocess.run([
    #     "ffmpeg", "-y",
    #     "-f", "concat", "-safe", "0",
    #     "-i", "file.txt",
    #     "-r", "30",
    #     "-c:v", "libx264",
    #     "-preset", "ultrafast",  # ultrafast, superfast, faster, fast, medium, slow, slower
    #     "-crf", "23",       # controls quality (lower = better)
    #     "-pix_fmt", "yuv420p",
    #     "-max_muxing_queue_size", "2048",
    #     "output.mp4"
    # ])

    # subprocess.run([
    #     "ffmpeg",
    #     "-y",                  
    #     "-i", "output.mp4",   
    #     "-i", "downloads/webcams.webm",  
    #     "-map", "0:v:0",       
    #     "-map", "1:a:0",       
    #     "-c:v", "copy",        
    #     "-c:a", "copy",        
    #     "-shortest",           
    #     "pre_chat" + ".mp4"           
    # ], check=True)
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
        empty_folder("downloads")
        empty_folder("frames") 
        empty_folder("chats") 
        empty_folder("svgs")   
        remove_file("output.mp4")
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
        video.add_svgs(images, "pre_chat.mp4")
        video.generate_all_chats(output_fname=file_name + ".mp4")
    except Exception as e:
        empty_folder("downloads")
        empty_folder("frames") 
        empty_folder("chats") 
        empty_folder("svgs")   
        remove_file("output.mp4")
        print(f"error occured {e}")


empty_folder("downloads")
empty_folder("frames") 
empty_folder("chats") 
empty_folder("svgs")   
remove_file("output.mp4")
remove_file("pre_chat.mp4")


print("All done File Created")
import subprocess, os


