import sys
import os
import urllib
import requests
import http.cookiejar
import re
import time
import http.client
import getpass
import random
import argparse


class PixivHandler:

    def __init__(self, username, password):
        self.base_url = "https://accounts.pixiv.net/login"
        self.login_url = "https://accounts.pixiv.net/api/login"
        self.first_page_url = "https://www.pixiv.net"
        self.username = username
        self.password = password
        self.s = None
        self.cookies = None

    def login(self):
        s = requests.Session()
        self.s = s
        login_html = s.get(self.base_url)
        pattern = re.compile(r'name="post_key" value="(.*?)">')
        result = re.search(pattern, login_html.text)
        post_key = result.group(1)
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'
        }

        params = {
            'lang': 'en',
            'source': 'pc',
            'view_type': 'page',
            'ref': 'wwwtop_accounts_index'
        }

        data = {
            'pixiv_id': self.username,
            'password': self.password,
            'captcha': '',
            'g_reaptcha_response': '',
            'post_key': post_key,
            'source': 'pc',
            'ref': 'wwwtop_accounts_indes',
            'return_to': 'https://www.pixiv.net/'
        }
        r = s.post(self.login_url,
                   data=data,
                   headers=headers,
                   params=params)
        target_html = s.get(self.first_page_url, cookies=r.cookies)
        self.cookies = r.cookies
        return target_html

    def download_img(self, page_url, img_url, illu_id):
        header = {
            'Referer': page_url,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.75 Safari/537.36'
        }
        img = self.s.get(img_url, headers=header, cookies=self.cookies)
        img_type = (img_url.split('.'))[-1]
        f = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pixiv', illu_id + '.' + img_type), 'wb')
        f.write(img.content)

    def get_original_img(self, page_url, illu_id):
        r = self.s.get(page_url)
        text = r.text.replace('\n', ' ').replace('\r', '')
        pattern = re.compile(r'.*"original":\s*"(?P<url>.*?)".*')
        m = re.match(pattern, text)
        if m:
            img_url = m.group('url').replace('\\', '')
            print(img_url)
            self.download_img(page_url, img_url, illu_id)
            return True
        else:
            print('failed')
            return False

    def search(self, key_word, image_count):
        count = 0
        page_n = 1
        while count < image_count:
            url = self.get_search_path_url(key_word, 'popular_d', page_n)
            r = self.s.get(url)
            text = r.text.replace('\n', ' ').replace('\r', '')
            pattern = re.compile(r'illustId&quot;:&quot;([0-9]+)&quot')
            illust_id_list = re.findall(pattern, text)
            for illu_id in illust_id_list:
                page_url = self.generate_url_by_id(illu_id)
                downloaded = self.get_original_img(page_url, illu_id)
                if downloaded:
                    count += 1
                if count >= image_count:
                    print('ending')
                    break
            page_n += 1


    def get_search_path_url(self, key_word, order, page_n):
        return 'https://www.pixiv.net/search.php?word={}&order={}&p={}'.format(key_word,
                                                                               order,
                                                                               page_n)

    def generate_url_by_id(self, id):
        return 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + id

if __name__ == '__main__':
    args_parser = argparse.ArgumentParser(description='pixiv crawler')
    args_parser.add_argument('--pixiv_id', type=str, help='pixiv-id')
    args_parser.add_argument('--password', type=str, help='pasword')
    args_parser.add_argument('--keyword', type=str, help='key word to search')
    args_parser.add_argument('--count', type=int, help='count of imgs to dump')
    args = args_parser.parse_args()
    pixiv_handler = PixivHandler(args.pixiv_id, args.password)
    first_page = pixiv_handler.login()
    pixiv_handler.search(args.keyword, args.count)
