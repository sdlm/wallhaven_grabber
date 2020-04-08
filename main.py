import os
import time
import json
from typing import Set

from lxml import html

import requests

cookies = "..."
filenames = []
collections = {"title": 123}


def get_page_urls() -> set:
    pages = set()
    for filename in filenames:
        with open(filename, 'r') as f:
            for bookmark in json.load(f):
                pages.add(bookmark['g'])
    return pages


def save_stat(pages_for_second_run: Set[str], complete_images: Set[str]):
    with open(f'data/errors.txt', 'w') as f:
        f.write(','.join(pages_for_second_run))
    with open(f'data/complete.txt', 'w') as f:
        f.write(','.join(complete_images))


def download_image(url: str, path: str = None):
    page_resp = requests.get(url=url, headers={"Cookie": cookies})
    img_url = html.fromstring(page_resp.text).xpath('//img[@id="wallpaper"]/@src')[0]
    img_filename = img_url.split('/')[-1]
    img_resp = requests.get(url=img_url, stream=True, headers={"Cookie": cookies})
    pre_path = path if path else 'data/images/'
    with open(f'{pre_path}{img_filename}', 'wb') as fd:
        for chunk in img_resp.iter_content(chunk_size=256):
            fd.write(chunk)


def download_bookmark_images():
    pages = get_page_urls()
    pages_for_second_run = set()
    complete_images = set()

    if os.path.exists('data/errors.txt'):
        with open('data/errors.txt', 'r') as f:
            pages_for_second_run = set(f.read().split(','))
            pages -= pages_for_second_run
    if os.path.exists('data/complete.txt'):
        with open('data/complete.txt', 'r') as f:
            complete_images = set(f.read().split(','))
            pages -= complete_images

    total_cnt = len(pages) + len(complete_images)
    counter = len(complete_images)
    for page_url in pages:
        counter += 1
        # time.sleep(2)
        if counter % 10 == 0:
            save_stat(pages_for_second_run, complete_images)
        try:
            download_image(page_url, path='data/images/')
            complete_images.add(page_url)
            print(f'Successfully downloaded {page_url} (complete: {counter/total_cnt*100:.1f}%)')
        except:
            pages_for_second_run.add(page_url)
            print(f'Error occurred during load {page_url} (complete: {counter/total_cnt*100:.1f}%)')

    save_stat(pages_for_second_run, complete_images)


def download_all_favourite_img_urls():
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": cookies
    }
    collection_map = {}
    for collection_title, collection_id in collections.items():
        image_pages = set()
        page = 1
        while True:
            time.sleep(2)
            collection_url = f'https://wallhaven.cc/favorites/{collection_id}?page={page}'
            collection_resp = requests.get(url=collection_url, headers=headers)
            dom = html.fromstring(collection_resp.text)
            urls = [str(x) for x in dom.xpath('//a[@class="preview"]/@href')]
            if not urls:
                print(f"No preview on {collection_url}")
                break

            print(f"Add previews {len(urls)}")
            image_pages = image_pages.union(urls)
            page += 1
        collection_map[collection_title] = {
            'id': collection_id,
            'images': list(image_pages)
        }

    with open('data/favourites.json', 'w') as f:
        json.dump(collection_map, f)


def prepare_dirs():
    os.mkdir('data/favourite')
    for title, _ in collections.items():
        os.mkdir(f'data/favourite/{title}')


def get_collections():
    with open('data/favourites.json', 'r') as f:
        return json.load(f)


def download_collection(title: str):
    collections = get_collections()
    collection = collections[title]
    urls = set(collection['images'])
    bad_urls = set(collection.get('bad_urls', []))
    good_urls = set(collection.get('good_urls', []))
    urls -= bad_urls
    urls -= good_urls
    for i, url in enumerate(urls):
        try:
            time.sleep(1)
            download_image(url, path=f'data/favourite/{title}/')
            good_urls.add(url)
            print(f'Successfully downloaded {url} (complete: {i/len(urls)*100:.1f}%)')
        except:
            print(f'Error occurred during load {url} (complete: {i/len(urls)*100:.1f}%)')
            bad_urls.add(url)
        if i % 10 == 0:
            collection['bad_urls'] = list(bad_urls)
            collection['good_urls'] = list(good_urls)
            collections[title] = collection
            with open('data/favourites.json', 'w') as f:
                json.dump(collections, f)


def download_collections():
    for title, _ in get_collections().items():
        download_collection(title)


if __name__ == '__main__':
    # download_all_favourite_img_urls()
    download_collections()
