import requests
import os 
from playwright.sync_api import sync_playwright
import xml.etree.ElementTree as ET
import cairosvg
import html
from PIL import Image
import subprocess
import shutil
import chat

downloaded = set()
# START_URL = "https://visioconference.supmti.ac.ma/playback/presentation/2.3/8ab678ec2baf0cbcf1e315136084dcde33f2ebfd-1762191511958/"
#START_URL = "https://visioconference.supmti.ac.ma/playback/presentation/2.3/0a2f3631b67c280930e9b313a0d716ce597b7018-1762888173315"
START_URL = input("Enter The Full Link of The Presentation: ")
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

if not os.path.exists("downloads/deskshare.webm"):
    tree = ET.parse("downloads/shapes.svg")
    root = tree.getroot()
    images = root.findall(".//{http://www.w3.org/2000/svg}image")
    in_list = []
    out_list = []
    href_list = []
    for e in images:
        in_list.append(float(e.get("in")))
        out_list.append(float(e.get("out")))
        href_list.append(e.get("{http://www.w3.org/1999/xlink}href"))

    for svg in href_list:
        print("https://visioconference.supmti.ac.ma/presentation/" + id + "/" + svg)
        headers = {
            "User-Agent": "Mozilla/5.0",  # mimic a real browser
            }
        # response = requests.get("https://visioconference.supmti.ac.ma/presentation/" + id + "/"  + svg, stream=True, timeout=40)
        # response = requests.get(START_URL + svg, headers=headers)
        download_svgs("https://visioconference.supmti.ac.ma/presentation/" + id + "/"  + svg)
        # svg_data = response.content
        # try:
        # concat_file = os.path.join(temp_dir, "file_list.txt")
        dur = out_list[index] - in_list[index]
        if index > 0:
            # converting svg into png whith high dpi 
            png_data = cairosvg.svg2png(url=f"svgs/{index}.svg", write_to=f"svgs/{index}.png", dpi=300)
            # reading png insuring it's rgba
            img = Image.open(f"svgs/{index}.png").convert("RGBA")
            # creating new white background
            bg = Image.new("RGB", img.size, (255, 255, 255))  
            # put the img on top of the mask 
            bg.paste(img, mask=img.split()[3])  
            bg = bg.resize((1280, 720), Image.LANCZOS)
            img_name = f"{index:04d}.png"
            bg.save(f"frames/{img_name}")
            with open("file.txt", "a") as f:
                f.write(f"file 'frames/{img_name}'\n")
                f.write(f"duration {dur}\n")
        else:
            with open("file.txt", "a") as f:
                f.write(f"file 'frames/0001.png'\n")
                f.write(f"duration {dur}\n")
        index += 1
    img_name = f"{(index - 1):04d}.png"
    with open("file.txt", "a") as f:
        f.write(f"file 'frames/{img_name}'\n")

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
    try :
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", "file.txt",
            "-r", "30",
            "-c:v", "libx264",
            "-preset", "ultrafast",  # ultrafast, superfast, faster, fast, medium, slow, slower
            "-crf", "23",       # controls quality (lower = better)
            "-pix_fmt", "yuv420p",
            "-max_muxing_queue_size", "2048",
            "output.mp4"
        ])

        subprocess.run([
            "ffmpeg",
            "-y",                  
            "-i", "output.mp4",   
            "-i", "downloads/webcams.webm",  
            "-map", "0:v:0",       
            "-map", "1:a:0",       
            "-c:v", "copy",        
            "-c:a", "copy",        
            "-shortest",           
            "pre_chat" + ".mp4"           
        ], check=True)
        chat.generate_all_chats(output_fname=file_name + ".mp4")
    except Exception as e:
        empty_folder("downloads")
        empty_folder("frames") 
        empty_folder("chats") 
        empty_folder("svgs")   
        remove_file("output.mp4")
        remove_file("file.txt")
        print(e)
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
        chat.generate_all_chats(output_fname=file_name + ".mp4")
    except Exception as e:
        empty_folder("downloads")
        empty_folder("frames") 
        empty_folder("chats") 
        empty_folder("svgs")   
        remove_file("output.mp4")
        remove_file("file.txt")
        print(e)


empty_folder("downloads")
empty_folder("frames") 
empty_folder("chats") 
empty_folder("svgs")   
remove_file("output.mp4")
remove_file("file.txt")

print("output.mp4 created")