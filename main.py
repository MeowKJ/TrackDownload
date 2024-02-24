import os
import httpx
import asyncio
from tkinter import *
from tkinter import filedialog
from tkinter.ttk import Progressbar
import threading
from tkinter import messagebox

# 默认值
song_list_url = "https://majdata.net/api2/api/SongList"
maidata_url = "https://majdata.net/api2/api/Maidata/"
img_url = "https://majdata.net/api2/api/ImageFull/"
track_url = "https://majdata.net/api2/api/Track/"
user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"
)
MAX_CONNECTIONS = 10


def sanitize_filename(filename):
    return "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in filename)


async def download_data(i, client, folder, progressbar, total_tasks):
    title = sanitize_filename(i["Title"].strip())
    for attempt in range(3):  # 最多尝试三次
        response = await client.get(
            maidata_url + str(i["Id"]), headers={"User-Agent": user_agent}
        )
        if response.status_code != 200:
            print(
                f"Failed to download maidata for {title}. Status code: {response.status_code}"
            )
            if attempt == 2:
                messagebox.showwarning(
                    "Download Failed",
                    f"Failed to download maidata for {title} after 3 attempts.",
                )
            continue
        if not response.content:
            print(f"Maidata content is empty for {title}")
            if attempt == 2:
                messagebox.showwarning(
                    "Download Failed",
                    f"Maidata content is empty for {title} after 3 attempts.",
                )
            continue
        directory_path = os.path.join(folder, title)
        if not os.path.exists(directory_path):
            os.mkdir(directory_path)
        with open(os.path.join(directory_path, "maidata.txt"), "wb") as f:
            f.write(response.content)
        response = await client.get(
            img_url + str(i["Id"]), headers={"User-Agent": user_agent}
        )
        if not response.content:
            print(f"Image content is empty for {title}")
            if attempt == 2:
                messagebox.showwarning(
                    "Download Failed",
                    f"Image content is empty for {title} after 3 attempts.",
                )
            continue
        with open(os.path.join(directory_path, "bg.jpg"), "wb") as f:
            f.write(response.content)
        response = await client.get(
            track_url + str(i["Id"]), headers={"User-Agent": user_agent}
        )
        if not response.content:
            print(f"Track content is empty for {title}")
            if attempt == 2:
                messagebox.showwarning(
                    "Download Failed",
                    f"Track content is empty for {title} after 3 attempts.",
                )
            continue
        with open(os.path.join(directory_path, "track.mp3"), "wb") as f:
            f.write(response.content)
        print(f"Downloaded {title}")
        progressbar["value"] += 1
        break


def main(folder, progressbar):
    async def main_async():
        async with httpx.AsyncClient(
            limits=httpx.Limits(max_connections=MAX_CONNECTIONS), timeout=30
        ) as client:
            # 下载 JSON 文件
            response = await client.get(
                song_list_url, headers={"User-Agent": user_agent}
            )
            if response.status_code != 200:
                print(
                    f"Failed to download song list. Status code: {response.status_code}"
                )
                return
            data = response.json()
            total_tasks = len(data)
            tasks = [
                download_data(i, client, folder, progressbar, total_tasks) for i in data
            ]
            await asyncio.gather(*tasks)

    asyncio.run(main_async())


def download():
    btn_download["state"] = "disabled"  # 禁用按钮
    progressbar["value"] = 0
    folder = filedialog.askdirectory()
    thread = threading.Thread(target=main, args=(folder, progressbar))
    thread.start()
    root.after(100, check_thread, thread)


def check_thread(thread):
    if thread.is_alive():
        root.after(100, check_thread, thread)
    else:
        btn_download["state"] = "normal"  # 启用按钮
        root.update_idletasks()


root = Tk()
root.title("铺面偷取器")
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

btn_download = Button(root, text="现在偷取", command=download)

btn_download.pack(pady=10)

progressbar = Progressbar(root, orient=HORIZONTAL, length=280, mode="determinate")
progressbar.pack(pady=10)

root.mainloop()
