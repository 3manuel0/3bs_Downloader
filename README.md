# About

3bs_Downloader creates a video using public links from BigBlueButton presentations. This tool helps you download and save school presentations and classes, making them accessible for later viewing.

# Project Setup & Usage

⚠️ **WARNING:**  
This project is **still under development**. Some features may not be fully functional yet.

You will need the following installed on your system:

- [Python 3](https://www.python.org/downloads/)
- [ffmpeg](https://ffmpeg.org/download.html)

---

<!-- TODO: FIX THIS USELESS README LATER -->

## Prepare your environment

Open a terminal in the script folder (or change your path to it) and create a **virtual environment**.

### Windows

⚠️ **WARNING:** : windows has some problems with libraries only linux is working currently

```powershell
python -m venv .venv
```

then run:

```shell
.venv\Scripts\activate.bat
```

### Linux (bash/zsh):

```bash
python3 -m venv .venv
```

then run:

```bash
source .venv/bin/activate
```

## now to install requirments:

```bash
pip install -r req.txt
```

## Runing:

make sure you're always using venv or maybe you can use other methodes like `Conda` then:

```bash
python main.py
```

you will be prompted to enter the link:

```bash
Enter The Full Link of The Presentation:
```

then the duration:

```bash
Enter The duration of the video (exactly as this format hh:mm example 00:55 or 01:45):
```

and enjoy.

## Notes

- Always run the project inside the virtual environment to avoid conflicts.
- Some features may not work yet as the project is still in development.
