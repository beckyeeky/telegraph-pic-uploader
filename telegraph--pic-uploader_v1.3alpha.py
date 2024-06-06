import requests
import os
import json
import time
from PIL import Image, ImageFile, ImageSequence
from shutil import copyfile
import imageio
from telegraph import Telegraph

# 配置项
USE_PROXY = True  # 设置是否使用代理
PROXY = '127.0.0.1:7890'
TELEGRAPH_TOKEN = "cd388846d981d689bb5ac5fh5sdfg83993bb34567fe9c803c08e30112345"
MAX_IMAGE_SIZE = 5600
COMPRESS_TARGET_SIZE_KB = 5000
COMPRESS_QUALITY = 85
COMPRESS_RATIO = 0.8

# 初始化Telegraph
telegraph = Telegraph(access_token=TELEGRAPH_TOKEN)

if USE_PROXY:
    proxies = {
        "http": f"http://{PROXY}/",
        "https": f"http://{PROXY}/",
        "http_socks": f"socks5://{PROXY}/",
        "https_socks": f"socks5://{PROXY}/"
    }
    telegraph._telegraph.session.proxies = {
        'http': f'socks5h://{PROXY}',
        'https': f'socks5h://{PROXY}'
    }
else:
    proxies = None

#telegraph.create_account(short_name='Kris', author_name='Kris wu', author_url='', replace_token=True)

def get_title(directory):
    """
    获取目录的标题
    """
    return os.path.basename(directory)

def resize_image(image_path, max_wh):
    """
    按比例调整图片尺寸
    """
    img = Image.open(image_path)
    w, h = img.size
    print(f"{image_path}")
    print(f"source size: {w} {h}")
    if max(w, h) <= MAX_IMAGE_SIZE:
        return image_path

    resize_ratio = max_wh / max(w, h)
    new_size = (int(w * resize_ratio), int(h * resize_ratio))
    resized_img = img.resize(new_size, Image.LANCZOS)
    new_path = image_path.replace(".jpg", "_rz.jpg").replace(".png", "_rz.png")
    resized_img.save(new_path)
    return new_path

def compress_gif(image_path):
    """
    压缩GIF图片
    """
    compressed_path = image_path.replace(".gif", "_compressed.gif")
    copyfile(image_path, compressed_path)
    
    im = Image.open(compressed_path)
    rp = 250
    image_list = [frame.convert('RGB').resize((rp, rp), Image.LANCZOS) for frame in ImageSequence.Iterator(im) if max(frame.size) > rp]
    duration = im.info.get('duration', 100) / 1000
    
    imageio.mimsave(compressed_path, image_list, duration=duration)
    return compressed_path

def compress_png(image_path, target_size_kb=COMPRESS_TARGET_SIZE_KB, quality=COMPRESS_QUALITY, k=COMPRESS_RATIO):
    """
    压缩PNG图片
    """
    compressed_path = image_path.replace(".png", "_compressed.png")
    copyfile(image_path, compressed_path)
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    while os.path.getsize(compressed_path) // 1024 > target_size_kb:
        with Image.open(compressed_path) as im:
            im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
            im.save(compressed_path, quality=quality)
    return compressed_path

def compress_image(image_path):
    """
    根据文件类型压缩图片
    """
    ext = image_path.split('.')[-1].lower()
    if ext == 'gif':
        return compress_gif(image_path)
    elif ext in ['png', 'jpg', 'jpeg']:
        return compress_png(image_path)
    return image_path

def telegraph_file_upload(file_path):
    """
    上传文件到telegra.ph
    """
    file_types = {'gif': 'image/gif', 'jpeg': 'image/jpeg', 'jpg': 'image/jpg', 'png': 'image/png', 'mp4': 'video/mp4'}
    file_ext = file_path.split('.')[-1].lower()
    
    if file_ext not in file_types:
        return f'error, {file_ext}-file can not be processed'

    if os.path.getsize(file_path) >= 5120 * 1024:
        file_path = compress_image(file_path)

    with open(file_path, 'rb') as f:
        response = requests.post('https://telegra.ph/upload', files={'file': ('file', f, file_types[file_ext])}, timeout=30, proxies=proxies)
    
    telegraph_url = json.loads(response.content)
    if isinstance(telegraph_url, list):
        print(f"pic size: {os.path.getsize(file_path) // 1024} kb")
        return f"https://telegra.ph{telegraph_url[0]['src']}"
    return ""

def process_images(directory):
    """
    处理目录中的所有图片并上传
    """
    img_list = [os.path.join(directory, nm) for nm in os.listdir(directory) if nm.lower().endswith(('jpg', 'png', 'gif'))]
    pics_html = ""

    for img_path in img_list:
        resized_path = resize_image(img_path, MAX_IMAGE_SIZE)
        telegraph_url = telegraph_file_upload(resized_path)
        print(telegraph_url)
        if telegraph_url:
            pics_html += f"<img src='{telegraph_url}'/> "
        time.sleep(2)

    with open(f"{directory}.txt", "w", encoding="utf-8") as file:
        file.write(pics_html)

    return pics_html

def main():
    print("Welcome!")
    links = []

    while True:
        root_folder = input("input folder:")
        html_text = input("html content:")

        for root, dirs, files in os.walk(root_folder):
            folder_title = get_title(root)
            try:
                print(f"\n{root}")
                print(f"Uploading folder: {root}")
                html_imgs = process_images(root)
                response = telegraph.create_page(
                    title=folder_title,
                    html_content=html_text + html_imgs,
                    author_name='Kris wu',
                    author_url=''
                )
                print(response['url'])
                links.append(response['url'])
            except Exception as e:
                print(f"Error: {e}")
                break

        print("\nHere are all page links:")
        for link in links:
            print(link)

if __name__ == "__main__":
    main()