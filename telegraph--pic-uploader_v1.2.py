from telegraph import Telegraph
import requests
import os
import json
import time
from PIL import Image
from PIL import ImageFile
from shutil import copyfile
import imageio
from PIL import Image, ImageSequence

def get_title(dir):
    tmp = dir[::-1]
    index = 0
    for i in range(len(tmp)):
        if tmp[i] == '\\':
            index = i
            break
    return dir[-index:]

def change_size(path, max_wh):
    """
    按比例变化
    Args:
        :param path: 图片路径
        :param max_wh: 最大高/宽
    Returns:
        :return: new image
    """
    img = Image.open(path)
    w, h = img.size
    old_max = max(w, h)
    print("source size:", w, h)
    if old_max <= 5600:
        return path
    # 按比例调整获得新尺寸
    pert = int(max_wh * 100 / old_max)
    prop_s = lambda size, p: int(size * p / 100)
    new_w = int(prop_s(w, pert))
    new_h = int(prop_s(h, pert))
    new_img = img.resize((new_w, new_h), Image.LANCZOS)
    new_path = str(path)[0:-4] + '_rz.jpg'
    new_img.save(new_path)
    return new_path

def gif_press(outfile):
    copy_one = str(outfile)[0:-4] + '_compressed.gif'
    copyfile(outfile, copy_one)
    outfile = copy_one
    # 自定义压缩尺寸 rp*rp
    rp = 250
    
    # 图片缓存空间
    image_list = []
    
    # 读取gif图片
    im = Image.open(outfile)
    
    # 提取每一帧，并对其进行压缩，存入image_list
    for frame in ImageSequence.Iterator(im):
        frame = frame.convert('RGB')
        if max(frame.size[0], frame.size[1]) > rp:
            frame.thumbnail((rp, rp), Image.LANCZOS)
        image_list.append(frame)
    
    # 计算帧之间的频率，间隔毫秒
    duration = (im.info)['duration'] / 1000
    
    # 读取image_list合并成gif
    imageio.mimsave(outfile, image_list, duration=duration)
    
    return outfile

def png_press(outfile, mb=5000, quality=75, k=0.77):
    copy_one = str(outfile)[0:-4] + '_compressed.png'
    copyfile(outfile, copy_one)
    outfile = copy_one
    o_size = os.path.getsize(outfile) // 1024  # 函数返回为字节，除1024转为kb（1kb = 1024 bit）
    print('before_size:{} target_size:{}'.format(o_size, mb))
    if o_size <= mb:
        return outfile
    
    ImageFile.LOAD_TRUNCATED_IMAGES = True  # 防止图像被截断而报错
    
    while o_size > mb:
        im = Image.open(outfile)
        x, y = im.size
        out = im.resize((int(x * k), int(y * k)), Image.LANCZOS)  # 最后一个参数设置可以提高图片转换后的质量
        try:
            out.save(outfile, quality=quality)  # quality为保存的质量，从1（最差）到95（最好），此时为85
        except Exception as e:
            print(e)
            break
        o_size = os.path.getsize(outfile) // 1024
        print(o_size)
    return outfile
    
def compress_image(outfile): # 通常你只需要修改mb大小
    """不改变图片尺寸压缩到指定大小
    :param outfile: 压缩文件保存地址
    :param mb: 压缩目标，KB
    :param k: 每次调整的压缩比率
    :param quality: 初始压缩比率
    :return: 压缩文件地址，压缩文件大小
    """
    if str(outfile)[-4:].lower() == ".gif":
        outfile = gif_press(outfile)
    else:
        outfile = png_press(outfile, mb=5000, quality=85, k=0.8)
    return outfile

def telegraph_file_upload(path_to_file):
    '''
    Sends a file to telegra.ph storage and returns its url
    Works ONLY with 'gif', 'jpeg', 'jpg', 'png', 'mp4' 
    
    Parameters
    ---------------
    path_to_file -> str, path to a local file
    
    Return
    ---------------
    telegraph_url -> str, url of the file uploaded

    >>>telegraph_file_upload('test_image.jpg')
    https://telegra.ph/file/16016bafcf4eca0ce3e2b.jpg    
    >>>telegraph_file_upload('untitled.txt')
    error, txt-file can not be processed
    '''
    file_types = {'gif': 'image/gif', 'jpeg': 'image/jpeg', 'jpg': 'image/jpg', 'png': 'image/png', 'mp4': 'video/mp4'}
    file_ext = path_to_file.split('.')[-1]
    
    if file_ext in file_types:
        file_type = file_types[file_ext]
    else:
        return f'error, {file_ext}-file can not be processed' 
    o_size = os.path.getsize(path_to_file)
    print("pic size:", int(o_size / 1024), "kb")
    if o_size >= 5120 * 1024:
        path_to_file = compress_image(path_to_file)
        
    with open(path_to_file, 'rb') as f:
        url = 'https://telegra.ph/upload'
        response = requests.post(url, files={'file': ('file', f, file_type)}, timeout=30, proxies=myproxies)
    
    telegraph_url = json.loads(response.content)
    print(telegraph_url)
    if not isinstance(telegraph_url, list):
        return ""
    telegraph_url = telegraph_url[0]['src']
    telegraph_url = f'https://telegra.ph{telegraph_url}'
    
    return telegraph_url

def bianli_pics(path):
    img_folder = path
    img_list = [os.path.join(nm) for nm in os.listdir(img_folder) if nm[-3:] in ['jpg', 'png', 'gif']]
    pics_html = ""

    for i in img_list:
        one_path = os.path.join(path, i)
        print(one_path)
        one_path = change_size(one_path, 5500)
        link = telegraph_file_upload(one_path)
        img_html = "<img src='{}'/>".format(link)
        print(link)
        pics_html = pics_html + " " + img_html
        time.sleep(2)
        with open(path + '.txt', "w", encoding="utf-8") as file:
            file.write(pics_html)
    return pics_html

proxy = '127.0.0.1:7890'
myproxies = {
    "http": "http://%(proxy)s/" % {'proxy': proxy},
    "https": "http://%(proxy)s/" % {'proxy': proxy}
}

#set your own if you need to manage and edit your article after publishing it 
token = "cd388846d981d689bb5ac5fh5sdfg83993bb34567fe9c803c08e30112345"      

telegraph = Telegraph(access_token=token)
telegraph._telegraph.session.proxies = {'https': 'socks5h://localhost:7890'}
telegraph.create_account(short_name='Kris', author_name='Kris wu', author_url='', replace_token=True)

tmp_img = ""

print("Welcome!")

links = []

while True:
    print("input folder:")
    Rootfolder = input()
    print("html content:")
    html_text = input()
    for root, dirs, files in os.walk(Rootfolder):
        print("\n", root)
        folder = root 
        biaoti = get_title(folder)
        try:
            print("Uploading folder: ", folder)
            html_imgs = bianli_pics(folder)
            response = telegraph.create_page(
                title=biaoti,
                html_content=html_text + tmp_img + html_imgs,
                author_name='Kris wu',
                author_url='',
            )
            print(response['url'])
            links.append(response['url'])
        except Exception as e:
            print(e)
            break
    print("")
    print("Here are all page links: ")
    for link in links:
        print(link)

#max size 5600
