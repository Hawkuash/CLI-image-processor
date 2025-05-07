from fnmatch import fnmatch
from PIL import Image, ImageFile
from PIL.Image import Resampling
import glob, os, time, argparse

ImageFile.LOAD_TRUNCATED_IMAGES = True

def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--depth", action="count", default=0, help="Defines depth of picture search")
    parser.add_argument("-r", "--resize", action="store_true", help="Defines if image should be resized by dividing its dimensions' pixel count by two")
    parser.add_argument("-c", "--convert", action="store_true", help="Defines if image should be converted to JPEG")
    parser.add_argument("-co", "--compress", action="store_true", help="Defines if JPEG image should be compressed. Does not work with resize")
    parser.add_argument("-u", "--update", action="store_true", help="Defines if folder name should be added to a filename")
    parser.add_argument("-s", "--side", type=int, default=2160, help="Minimal size of dimension of an image to be resized")
    parser.add_argument("-e", "--erase", action="store_true", help="Defines if PNG should be deleted after conversion")
    parser.add_argument("-q", "--quality", type=int, choices=[95, 100], default=100, help="Defines quality of JPEG images. 95 equals 10 photoshop and 100 equals 12")
    parser.add_argument("paths", type=str, help="There goes the path or list of paths separated by *")
    return parser.parse_args()


def resize_condition(infile, image):
    
    return os.path.getsize(infile) > 1000000 and (min(image.height, image.width) > args.side)


def resize(infile, format):

    file, ext = os.path.splitext(infile)
    with Image.open(infile) as im:
        if resize_condition(infile, im):
            width, height = im.size
            new_width = width//2
            new_height = height//2
            im_L = im.resize((new_width, new_height), resample=Resampling.LANCZOS)
            if format == "JPEG":
                im_L.save(file + ext, format, quality=args.quality)
            else:
                im_L.save(file + ext, format)


def delete_png(file):

    if os.path.exists(file + ".png"):
        os.remove(file + ".png")


def convert(infile):

    file, ext = os.path.splitext(infile)
    with Image.open(infile) as im:
        rgb_im = im.convert('RGB')
        rgb_im.save(file + ".jpg", "JPEG", quality=args.quality)
    if args.erase and os.path.exists(file + ".jpg"):
        delete_png(file)


def compress(infile):

    file, ext = os.path.splitext(infile)
    with Image.open(infile) as im:
        im.save(file + ".jpg", "JPEG", quality=args.quality)


def update_filename(path, file):
        
        add_path, fold = os.path.split(path)
        new_ent = fold + '_' + file
        os.rename(file, new_ent)

def process_image(path, infile):

    subt = time.time()
    old_size = os.stat(infile).st_size
    if fnmatch(infile, "*.jpg"):
        if args.resize:
            resize(infile, "JPEG")
        if not args.resize and args.compress:
            compress(infile)
    if fnmatch(infile, "*.png"):
        if args.resize:
            resize(infile, "PNG")
        if args.convert:
            convert(infile)
    if args.convert:
        file, ext = os.path.splitext(infile)
        new_size = os.stat(file + ".jpg").st_size
    else:
        new_size = os.stat(infile).st_size
    if args.update:
        update_filename(path, infile)
    print(path, infile,': ', time.strftime("%H:%M:%S", time.gmtime(time.time() - subt)), old_size, new_size)


def add_inner_directories(parent):

    list = []

    for string in parent:
        for f in os.listdir(string):
            f = os.path.join(string, f)
            if os.path.isdir(f):
                list.append(f)
    return list
    
   
def generate_pathlists(args) -> tuple[list, list]:

    path_dict = {}
    initial_list = []
    secondary_list = []

    if '*' in args.paths:
        initial_list.extend(args.paths.split('*'))
    else:
        initial_list.append(args.paths)
    
    for entry in initial_list:
        if fnmatch(entry, '*.png') or fnmatch(entry, '*.jpg'):
            secondary_list.append(entry)
    for entry in secondary_list:
        initial_list.remove(entry)
    
    path_dict['lvl0'] = initial_list

    for i in range(args.depth):
        current_level = 'lvl'+ str(i+1)
        path_dict[current_level] = add_inner_directories(path_dict.get('lvl'+str(i)))
        initial_list.extend(path_dict[current_level])
    initial_list = list(set(initial_list))

    return initial_list, secondary_list


if __name__ == '__main__':
    args = init_args()

    all_time = time.time()
    
    path_list, image_list = generate_pathlists(args)
    print(path_list, image_list, sep="\n")
    
    for path in path_list:
        os.chdir(path)
        for infile in glob.glob("*.[a-z][a-z]g"):
            process_image(path, infile)
    
    for image in image_list:
        path, file = os.path.split(image)
        os.chdir(path)
        process_image(path, file)

    print('Program finished in', time.strftime("%H:%M:%S", time.gmtime(time.time() - all_time)), "at", time.strftime("%Y.%m.%d %H:%M:%S", time.gmtime(time.time())))