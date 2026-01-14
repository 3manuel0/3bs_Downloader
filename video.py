from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import xml.etree.ElementTree as ET
import os
import subprocess

@dataclass
class Chat:
    name:str
    message:list[str] 
    start : float
    end: float
    is_mod : bool

def add_svgs(images, video_file, out_vid=None):

    temp_out = video_file + ".tmp.mp4"

    cmd = ["ffmpeg", "-y", "-i", video_file]

    for img, _, _ in images:
        cmd += ["-i", img]

    filter_complex = ""
    last = "[0:v]"

    for i, (img, start, end) in enumerate(images):
        tag_out = f"[tmp{i+1}]" if i < len(images)-1 else ""
        filter_complex += (
            f"{last}[{i+1}:v]overlay=0:0:enable='between(t,{start},{end})'{tag_out};"
        )
        if tag_out:
            last = tag_out
    if out_vid:
        cmd += ["-filter_complex", filter_complex.rstrip(";"), "-c:a", "copy", out_vid]
        subprocess.run(cmd, check=True)
    else:
        cmd += ["-filter_complex", filter_complex.rstrip(";"), "-c:a", "copy", temp_out]
        subprocess.run(cmd, check=True)
        os.replace(temp_out, video_file)

    print("Done! Edited original file:", video_file)




def add_chat(images, video_file, output_file, pad_left = 300):

    cmd = ["ffmpeg", "-y", "-i", video_file]

    for img, _, _ in images:
        cmd += ["-i", img]

    filter_complex = f"[0:v]pad=iw+{pad_left}:ih:{pad_left}:0[base];"
    last = "[base]"

    for i, (img, start, duration) in enumerate(images):
        end = start + duration
        if i == len(images)-1:
            filter_complex += f"{last}[{i+1}:v]overlay=0:0:enable='between(t,{start},{end})'"
        else:
            out = f"[tmp{i+1}]"
            filter_complex += f"{last}[{i+1}:v]overlay=0:0:enable='between(t,{start},{end})'{out};"
            last = out

    cmd += ["-filter_complex", filter_complex, "-c:a", "copy", output_file]

    subprocess.run(cmd)
    print("Done! Output saved to", output_file)


def wrap_text(text, font, max_width):
    """
    Splits text into lines that fit within max_width using the given font
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()

        # create a temporary dummy image to calculate text width
        dummy_img = Image.new("RGB", (1,1))
        draw = ImageDraw.Draw(dummy_img)
        w = draw.textlength(test_line, font=font)

        if w <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines

def toatl_chat_height(chats : list[Chat] , font: any, line_height: int)-> int:
    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    toatal_lines = 0
    if len(chats) == 0:
        return 0
    for chat in chats:
        toatal_lines += 1 + len(chat.message)
    y = toatal_lines * line_height + 10
    bbox = draw.textbbox((10, y ), chats[-1].message[-1], font=font)
    return bbox[3]

def render_chat_panel(chats : list[Chat], input_fname, output_fname, width=300, line_height=20, font_path="test.ttf"):

    font = ImageFont.truetype(font_path, 16)
    for chat in chats:
        chat.message = wrap_text(chat.message, font, width - 20)  # 10px padding each side


    print(toatl_chat_height(chats, font, line_height))
    index = 0
    temp_chats = []
    images = []
    for chat in chats:
        img = Image.new("RGB", (width, 720), (255, 255, 255))  # semi-transparent bg
        draw = ImageDraw.Draw(img)
        img_name = f"{(index):04d}.png"
        i = 0
        temp_chats.append(chat)
        while toatl_chat_height(temp_chats, font, line_height) > 720:
            temp_chats.pop(0)
        for temp in temp_chats:
            y = i * line_height + 10
            draw.text((10, y), temp.name, font=font, fill=(0, 127, 0))
            i+=1
            for line in temp.message:
                y = i * line_height + 10
                draw.text((10, y), line, font=font, fill=(0, 0, 0))
                i+=1
        images.append((f"chats/{img_name}", chat.start, chat.end))
        img.save(f"chats/{img_name}")
        index += 1
    add_chat(images, input_fname, output_fname, width)

def generate_all_chats(inpute_fname = "pre_chat.mp4" , output_fname = "output.mp4"):
    tree = ET.parse("downloads/metadata.xml")
    root = tree.getroot()

    duration_tag = root.find(".//duration")
    duration = float(duration_tag.text) / 1000.0
    tree = ET.parse("downloads/slides_new.xml")
    root = tree.getroot()
    i = 0
    chats = []
    out = 0.0
    for chat in root.findall(".//chattimeline"):
        timestamp = float(chat.get("in"))
        name = chat.get("name")
        message = chat.get("message")
        sender = chat.get("senderRole")
        chat = Chat(name, message,timestamp, out, False)
        if i > 0:
            chats[i-1].end = round(timestamp - chats[i-1].start, 2)
        if(sender == "MODERATOR"):
            chat.is_mod = True
        chats.append(chat)
        i +=1
    chats[-1].end = round(duration - chats[-1].start ,2)
    print("Rendering the Chat")
    render_chat_panel(chats, input_fname=inpute_fname, output_fname=output_fname)

# this was for testing purposes only 
# generate_all_chats()