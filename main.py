import os
import asyncio
import threading

from tkinter import *
from tkinter import filedialog
from tkinter.ttk import Progressbar, Entry
from tkinter import messagebox

import httpx

# Default URLs
song_list_url = "https://majdata.net/api3/api/SongList"
maidata_url = "https://majdata.net/api3/api/Maidata/"
img_url = "https://majdata.net/api3/api/ImageFull/"
track_url = "https://majdata.net/api3/api/Track/"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"
MAX_CONNECTIONS = 3


def sanitize_filename(filename):
    """Sanitize the filename by replacing invalid characters."""
    return "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in filename)


async def download_data(i, client, folder, progressbar):
    """Asynchronous function to download data for a single item."""
    title = sanitize_filename(i["Title"].strip())
    for attempt in range(3):  # Retry up to 3 times
        try:
            # Downloading maidata
            response = await client.get(
                maidata_url + str(i["Id"]), headers={"User-Agent": user_agent}
            )
            if response.status_code == 200 and response.content:
                # Create directory and save files
                directory_path = os.path.join(folder, title)
                os.makedirs(directory_path, exist_ok=True)
                with open(os.path.join(directory_path, "maidata.txt"), "wb") as f:
                    f.write(response.content)

                # Download and save image
                response = await client.get(
                    img_url + str(i["Id"]), headers={"User-Agent": user_agent}
                )
                if response.content:
                    with open(os.path.join(directory_path, "bg.jpg"), "wb") as f:
                        f.write(response.content)

                # Download and save track
                response = await client.get(
                    track_url + str(i["Id"]), headers={"User-Agent": user_agent}
                )
                if response.content:
                    with open(os.path.join(directory_path, "track.mp3"), "wb") as f:
                        f.write(response.content)

                print(f"Downloaded {title}")
                progressbar["value"] += 1
                break
            else:
                raise Exception(f"Bad response: {response.status_code}")
        except Exception as e:
            print(f"Attempt {attempt + 1}: Error downloading data for {title} - {e}")
            if attempt == 2:
                messagebox.showerror(
                    "Download Failed",
                    f"Could not download data for {title} after 3 attempts.",
                )


async def main_async(folder, progressbar, proxy):
    """Main asynchronous function to manage downloads."""
    proxies = {"http://": proxy, "https://": proxy} if proxy else None
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_connections=MAX_CONNECTIONS),
        timeout=30,
        proxies=proxies,
    ) as client:
        response = await client.get(song_list_url, headers={"User-Agent": user_agent})
        if response.status_code == 200:
            data = response.json()
            tasks = [download_data(item, client, folder, progressbar) for item in data]
            await asyncio.gather(*tasks)
        else:
            messagebox.showerror(
                "Download Failed",
                f"Could not fetch song list. Status code: {response.status_code}",
            )


def main(folder, progressbar, proxy):
    """Wrapper function to run the asynchronous main function."""
    asyncio.run(main_async(folder, progressbar, proxy))


def download():
    """Function to handle the download button click."""
    btn_download["state"] = "disabled"
    progressbar["value"] = 0
    folder = filedialog.askdirectory()
    if folder:
        proxy = entry_proxy.get().strip()
        thread = threading.Thread(target=main, args=(folder, progressbar, proxy))
        thread.start()
        root.after(100, check_thread, thread)


def check_thread(thread):
    """Function to check the thread's state and update the UI accordingly."""
    if thread.is_alive():
        root.after(100, check_thread, thread)
    else:
        btn_download["state"] = "normal"
        root.update_idletasks()


root = Tk()
root.title("铺面下载器")
root.geometry("300x350")

lbl_song_list_url = Label(root, text="Song List URL:")
lbl_song_list_url.pack(pady=5)
entry_song_list_url = Entry(root, width=40)  # 将输入框长度调整为更长的值
entry_song_list_url.pack(pady=5)
entry_song_list_url.insert(0, song_list_url)

lbl_maidata_url = Label(root, text="Maidata URL:")
lbl_maidata_url.pack(pady=5)
entry_maidata_url = Entry(root, width=40)  # 将输入框长度调整为更长的值
entry_maidata_url.pack(pady=5)
entry_maidata_url.insert(0, maidata_url)

lbl_img_url = Label(root, text="Image URL:")
lbl_img_url.pack(pady=5)
entry_img_url = Entry(root, width=40)  # 将输入框长度调整为更长的值
entry_img_url.pack(pady=5)
entry_img_url.insert(0, img_url)

lbl_track_url = Label(root, text="Track URL:")
lbl_track_url.pack(pady=5)
entry_track_url = Entry(root, width=40)  # 将输入框长度调整为更长的值
entry_track_url.pack(pady=5)
entry_track_url.insert(0, track_url)

# GUI elements for proxy configuration
lbl_proxy = Label(root, text="Proxy (optional):")
lbl_proxy.pack(pady=5)
entry_proxy = Entry(root, width=40)
entry_proxy.pack(pady=5)

btn_download = Button(root, text="下载", command=download)

btn_download.pack(pady=10)

progressbar = Progressbar(root, orient=HORIZONTAL, length=280, mode="determinate")
progressbar.pack(pady=10)

root.mainloop()
