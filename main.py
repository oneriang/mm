import os
import shutil
import exifread
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging
import traceback

# Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('photo_organizer.log'),
#         logging.StreamHandler()
#     ]
# )
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('photo_organizer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Supported media file extensions
SUPPORTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.heic', '.gif', '.bmp', '.tiff')
SUPPORTED_VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')


def walk_files(directory):
    """Walk through all files in directory, including subdirectories."""
    for root, _, files in os.walk(directory):
        for filename in files:
            yield os.path.join(root, filename)


def get_photo_date_taken(path):
    """Get the date when the photo was taken from EXIF data."""
    try:
        with open(path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            if 'EXIF DateTimeOriginal' in tags:
                date_str = str(tags['EXIF DateTimeOriginal'])
                return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        logger.warning(f"Failed to get EXIF date from {path}: {str(e)}")
    
    # Fallback to file modification time
    return datetime.fromtimestamp(os.path.getmtime(path))


def get_video_date_taken(path):
    """Get the creation date of a video file using ffprobe."""
    try:
        # 指定 ffprobe 的完整路径（根据你的安装位置修改）
        ffprobe_path = 'ffmpeg/bin/ffprobe.exe'  # 示例路径
        
        command = [
            ffprobe_path, '-v', 'error',
            '-show_entries', 'format_tags=creation_time',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, text=True)
        output = result.stdout.strip()
        
        if output:
            # Handle different timestamp formats
            if 'T' in output:  # ISO format (e.g., '2018-12-31T12:34:56.000000Z')
                date_str = output.split('.')[0]  # Remove milliseconds
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
            else:  # Other possible formats
                return datetime.strptime(output, '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.warning(f"Failed to get metadata date from {path}: {str(e)}")
    
    # Fallback to file modification time
    return datetime.fromtimestamp(os.path.getmtime(path))


def generate_unique_filename(directory, base_name, extension):
    """Generate a unique filename to avoid conflicts."""
    counter = 1
    new_filename = f"{base_name}{extension}"
    file_path = os.path.join(directory, new_filename)
    
    while os.path.exists(file_path):
        new_filename = f"{base_name} ({counter}){extension}"
        file_path = os.path.join(directory, new_filename)
        counter += 1
    
    return new_filename


def rename_file1(src_path, dst_directory, date_taken):
    """Rename file using creation date and copy to destination directory."""
    try:
        filename = os.path.basename(src_path)
        extension = os.path.splitext(filename)[1].lower()
        
        # Create YYYY/MM/DD directory structure
        date_folder = date_taken.strftime('%Y/%m/%d')
        dst_folder = os.path.join(dst_directory, date_folder)
        os.makedirs(dst_folder, exist_ok=True)
        
        # Generate filename based on timestamp
        base_name = date_taken.strftime('%Y-%m-%d_%H-%M-%S')
        new_filename = generate_unique_filename(dst_folder, base_name, extension)
        dst_path = os.path.join(dst_folder, new_filename)
        
        # Copy file preserving metadata
        shutil.copy2(src_path, dst_path)
        
        logger.info(f"Processed: {src_path} -> {dst_path}")
        return dst_path
    except Exception as e:
        logger.error(f"Failed to process file {src_path}: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def process_file(file_path, dst_directory):
    """Process a single file based on its type."""
    try:
        extension = os.path.splitext(file_path)[1].lower()
        
        if extension in SUPPORTED_IMAGE_EXTENSIONS:
            date_taken = get_photo_date_taken(file_path)
        elif extension in SUPPORTED_VIDEO_EXTENSIONS:
            date_taken = get_video_date_taken(file_path)
        else:
            logger.debug(f"Skipping unsupported file type: {file_path}")
            return None
            
        # return rename_file(file_path, dst_directory, date_taken)
        return rename_file(file_path, dst_directory, date_taken, skip_duplicates=True)
    except Exception as e:
        logger.error(f"Failed to process file {file_path}: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def sort_files_by_date(src_directory, dst_directory):
    """Sort all files in directory by creation date and rename them."""
    try:
        logger.info(f"Processing directory: {src_directory}")
        logger.info(f"Target directory: {dst_directory}")
        
        os.makedirs(dst_directory, exist_ok=True)
        files = list(walk_files(src_directory))
        logger.info(f"Found {len(files)} files to process")
        
        # Use thread pool for parallel processing
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_file, file_path, dst_directory) 
                      for file_path in files]
            
            # Wait for all tasks to complete
            for future in futures:
                future.result()
        
        logger.info("Processing completed")
    except Exception as e:
        logger.error(f"Failed to process directory: {str(e)}")
        logger.error(traceback.format_exc())


def rename_file(src_path, dst_directory, date_taken, skip_duplicates=True):
    """将文件复制到目标目录（跳过重复文件）"""
    try:
        filename = os.path.basename(src_path)
        extension = os.path.splitext(filename)[1].lower()
        
        # 创建按年月日组织的目录结构
        date_folder = date_taken.strftime('%Y/%m/%d')
        dst_folder = os.path.join(dst_directory, date_folder)
        os.makedirs(dst_folder, exist_ok=True)
        
        # 生成基于时间戳的文件名
        base_name = date_taken.strftime('%Y-%m-%d_%H-%M-%S')
        dst_path = os.path.join(dst_folder, f"{base_name}{extension}")
        
        # 检查是否已存在相同内容的文件
        if skip_duplicates and os.path.exists(dst_path):
            if files_are_identical(src_path, dst_path):
                logger.info(f"跳过重复文件: {src_path} (已存在: {dst_path})")
                return None
        
        # 生成唯一文件名（只有当skip_duplicates=False时才需要）
        if not skip_duplicates:
            dst_path = os.path.join(dst_folder, generate_unique_filename(dst_folder, base_name, extension))
        
        # 复制文件并保留元数据
        shutil.copy2(src_path, dst_path)
        logger.info(f"已处理: {src_path} -> {dst_path}")
        return dst_path
    except Exception as e:
        logger.error(f"处理文件失败 {src_path}: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def files_are_identical(file1, file2):
    """通过哈希比较判断两个文件是否相同"""
    try:
        if os.path.getsize(file1) != os.path.getsize(file2):
            return False
            
        hash1 = filehash(file1)
        hash2 = filehash(file2)
        return hash1 == hash2
    except:
        return False

def filehash(filename):
    """计算文件的MD5哈希值"""
    import hashlib
    h = hashlib.md5()
    with open(filename, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

# if __name__ == '__main__':
#     # Example usage
#     source = r"E:\[备份]“tt”的 iPhone\相册"
#     destination = 'D:/photo'
    
#     # Normalize paths
#     source = os.path.normpath(source)
#     destination = os.path.normpath(destination)
    
#     sort_files_by_date(source, destination)

def setup_logging(source_dir):
    """配置日志，文件名包含源目录名和时间戳"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_dirname = "".join(c if c.isalnum() else "_" for c in os.path.basename(os.path.normpath(source_dir)))
    
    log_filename = f"photo_organizer_{safe_dirname}_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return log_filename

if __name__ == '__main__':

    # source = r"E:\[备份]“tt”的 iPhone\相册"
    # source = r"E:\[备份]iPhone"
    # source = r"E:\[备份]IUNI-U3"
    # source = r"E:\[备份]IUNI-U3(2)"
    # source = r"E:\[备份]IUNI-U3(3)"
    # source = r"E:\[备份]IUNI-U3(4)"
    source = r"E:\unimported"

    destination = 'D:/photo'
    
    # 标准化路径并设置日志
    source = os.path.normpath(source)
    destination = os.path.normpath(destination)
    log_file = setup_logging(source)
    
    print(f"日志文件已创建: {log_file}")
    sort_files_by_date(source, destination)