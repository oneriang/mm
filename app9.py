import os
import shutil
import exifread
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 遍历目录下的所有文件，包括子目录中的文件
def walk_files(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            yield os.path.join(root, filename)

# 获取照片的拍摄时间
def get_photo_date_taken(path):
    with open(path, 'rb') as f:
        tags = exifread.process_file(f)
        try:
            date_taken = datetime.strptime(str(tags['EXIF DateTimeOriginal']), '%Y:%m:%d %H:%M:%S')
        except KeyError:
            date_taken = datetime.fromtimestamp(os.path.getmtime(path))
    return date_taken

# 获取视频的拍摄时间
def get_video_date_taken(path):
    command = ['ffprobe', '-v', 'error', '-show_entries', 'format_tags=creation_time', '-of', 'default=noprint_wrappers=1:nokey=1', path]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode().strip()
    if output:
        date_taken = datetime.strptime(output, '%Y-%m-%dT%H:%M:%S.%fZ')
    else:
        date_taken = datetime.fromtimestamp(os.path.getmtime(path))
    return date_taken

# # 将文件重命名为拍摄时间
# def rename_file(src_path, dst_directory, date_taken, log_file):
#     filename = os.path.basename(src_path)
#     extension = os.path.splitext(filename)[1]
#     new_filename = date_taken.strftime('%Y-%m-%d_%H-%M-%S') + extension
#     dst_path = os.path.join(dst_directory, date_taken.strftime('%Y/%m/%d'), new_filename)
#     os.makedirs(os.path.dirname(dst_path), exist_ok=True)
#     i = 1
#     while os.path.exists(dst_path):
#         new_filename = date_taken.strftime('%Y-%m-%d_%H-%M-%S') + f" ({i})" + extension
#         dst_path = os.path.join(dst_directory, new_filename)
#         i += 1
#     shutil.copy2(src_path, dst_path)
#     processed_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     log_entry = f"{src_path}\t{dst_path}\t{processed_time}\n"
#     with open(log_file, 'a') as f:
#         f.write(log_entry)
#     return dst_path

# 处理单个文件
def process_file(file, dst_directory):
    if file.lower().endswith('.jpg') or file.lower().endswith('.jpeg') or file.lower().endswith('.png'):
        date_taken = get_photo_date_taken(file)
    elif file.lower().endswith('.mp4') or file.lower().endswith('.avi') or file.lower().endswith('.mov'):
        date_taken = get_video_date_taken(file)
    else:
        return
    rename_file(file, dst_directory, date_taken)


# # 将目录下的所有文件按照拍摄时间排序并重命名到新的目录中
# def sort_files_by_date(src_directory, dst_directory, log_file):
#     os.makedirs(dst_directory, exist_ok=True)
#     files = list(walk_files(src_directory))
#     with ThreadPoolExecutor() as executor:
#         for file in files:
#             executor.submit(process_file, file, dst_directory, log_file)

# 将文件重命名为拍摄时间
def rename_file(src_path, dst_directory, date_taken):
    src_dirname = os.path.dirname(src_path)
    filename = os.path.basename(src_path)
    extension = os.path.splitext(filename)[1]
    new_filename = date_taken.strftime('%Y-%m-%d_%H-%M-%S') + extension
    # 修改：将log文件名设置为处理的文件夹路径名
    # log_filename = os.path.basename(dst_directory) + '.log'
    log_filename = src_dirname + '.log'
    # log_path = os.path.join(dst_directory, log_filename)
    log_path = os.path.join('', log_filename)
    log_path = log_path.replace('\\', '#')
    log_path = log_path.replace(':', '@')
    dst_path = os.path.join(dst_directory, date_taken.strftime('%Y/%m/%d'), new_filename)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    i = 1
    while os.path.exists(dst_path):
        new_filename = date_taken.strftime('%Y-%m-%d_%H-%M-%S') + f" ({i})" + extension
        dst_path = os.path.join(dst_directory, new_filename)
        i += 1
    shutil.copy2(src_path, dst_path)
    processed_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"""{src_path}\t{dst_path}\t{processed_time}\n"""
    print(log_path)
   
    with open(log_path, 'a', encoding='utf-8') as f:
        print(log_entry)
        f.write(log_entry)
    return dst_path

# 将目录下的所有文件按照拍摄时间排序并重命名到新的目录中
def sort_files_by_date(src_directory, dst_directory):
    # 修改：将log文件名设置为处理的文件夹路径名
    log_filename = os.path.basename(dst_directory) + '.log'
    os.makedirs(dst_directory, exist_ok=True)
    files = list(walk_files(src_directory))
    print(files)
    with ThreadPoolExecutor() as executor:
        for file in files:
            executor.submit(process_file, file, dst_directory)

if __name__ == '__main__':
    # source = 'source'
    # destination = 'destination'

    # source = 'E:\OneDrive\Pictures\[备份]IUNI-U3(2)'
    # source = 'E:\OneDrive\Pictures\[备份]IUNI-U3(4)'
    # source = 'E:\OneDrive\Pictures\[备份]Meizu-m3 note'
    # source = 'E:\OneDrive\Pictures\iphone4'
    # source = 'E:\OneDrive\Pictures\来自：iPhone'
    # source = 'E:\OneDrive\Pictures\来自：iPad'
    # source = 'E:\OneDrive\Pictures\[备份]“tt”的 iPhone'
    # source = 'E:\OneDrive\Pictures\[备份]IUNI-U3'
    # source = 'E:\OneDrive\Pictures\[备份]Lenovo-Lenovo L78011'
    # source = 'E:\OneDrive\Pictures\Lenovo Z5'
    # source = 'E:\OneDrive\Pictures\来自：U3'
    # source = 'E:\OneDrive\Pictures\[备份]西山里恵のiPhone'
    # source = 'E:\OneDrive\Pictures\FujiFilm'
    source = 'E:\OneDrive\Pictures\Camera Roll'
    destination = 'D:\photo'
    sort_files_by_date(source, destination)