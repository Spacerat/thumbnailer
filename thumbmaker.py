from __future__ import print_function, division

from bs4 import BeautifulSoup
import requests
import requests_cache
import shutil
import os

try:
    from urllib.parse import urlparse, urljoin
except ImportError:
    from urlparse import urlparse, urljoin

from os.path import join
from PIL import Image
import tempfile
import argparse



requests_cache.install_cache('.cache')

def save_image(response, path):
    if response.status_code == 200:
        with open(path, 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
    else:
        raise ValueError("Cannot save %s, invalid response code %s" % (path, response.status_code))

def try_int(v):
    try:
        return int(v)
    except ValueError:
        if v.endswith('px'):
            return try_int(v[:-2])
    except TypeError:
        return None

def get_thumb_size(real_size, render_size):
    thumb_size = list(render_size)
    for i in (0, 1):
        if render_size[i] is None: continue
        if render_size[i] > real_size[i]:
            return None
        thumb_size[1-i] = int((render_size[i] / real_size[i]) * real_size[1-i])
        return tuple(thumb_size)

def process_img(root, img, base_path):
    requests.get(join(root, img['src']), stream=True)
    r = requests.get(join(root, img['src']), stream=True)
    localpath = make_path_for_file(base_path, img['src'])
    save_image(r, localpath)
    image  = Image.open(localpath)

    real_size = image.size
    render_size = (try_int(img.get('width', None)), try_int(img.get('height', None)))
    thumb_size = get_thumb_size(real_size, render_size)
    if thumb_size is not None:
        image.thumbnail(thumb_size, Image.ANTIALIAS)
        thumbpath = make_path_for_file(base_path, 'thumbnails', img['src'])
        image.save(thumbpath)
        return join('thumbnails', img['src'])
    else:
        return None

def make_path_for_file(*components):
    path = os.path.realpath(join(*components))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def process_page(root_url, base_path, page):

    url = urljoin(root_url, page)
    site = requests.get(url)
    soup = BeautifulSoup(site.text, "html.parser")

    for img in soup.find_all('img'):
        new_path = process_img(root_url, img, base_path)
        if new_path:
            img['src'] = new_path

    root, ext = os.path.splitext(page)
    if not ext:
        ext = '.html'
    page_path = make_path_for_file(base_path, "%s%s"%(root,ext))

    with open(page_path, 'w') as f:
        f.write(soup.prettify())

def process_site(root_url, pages):
    site_name = urlparse(root_url).netloc
    with tempfile.TemporaryDirectory() as temp_dir:
        for page in pages:
            process_page(root_url, temp_dir, page)
        zipfile = shutil.make_archive(temp_dir, 'zip', temp_dir)
        with open(zipfile, 'rb') as f:
            return site_name+'.zip', f.read()

def main():
    parser = argparse.ArgumentParser(description='Thumbnailify all images on a static website')
    parser.add_argument('root_url', help='Root webpage to process')
    parser.add_argument('pages', nargs='+', help='list of pages to access')
    args = parser.parse_args()
    print(process_site(args.root_url, args.pages))


if __name__ == '__main__':
    main()



