import time
import urllib
import random
import requests
import threading
from urllib import request
from bs4 import BeautifulSoup


image_urls = []  # 表情链接
page_urls = []  # 页面链接
base_url = 'https://www.doutula.com/photo/list/?page={page}'
for page in range(1, 500):  # 2051
    url = base_url.format(page=page)
    page_urls.append(url)
condition = threading.Condition()  # 条件锁


class Producer(threading.Thread):  # 生产者：负责从page_urls提取页面链接，爬取每一页的表情url
    user_agents = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.60 Safari/537.17',
        'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36',
    ]
    header = {'User-Agent': random.choice(user_agents)}

    proxies = [
        '219.234.5.128:3128', '61.135.155.82:443', '122.72.99.103:80',
        '106.46.132.2:80', '112.16.4.99:81', '123.58.166.113:9000'
    ]
    proxy = {'http': random.choice(proxies)}

    def run(self):
        print('Producer is running ......', threading.current_thread())
        while len(page_urls) > 0:
            condition.acquire()  # 访问前加锁
            try:
                p_url = page_urls.pop()
            finally:
                condition.release()  # 使用完后要及时把锁给释放，方便其他线程使用
            response = requests.get(p_url, headers=self.header, proxies=self.proxy)
            try:
                soup = BeautifulSoup(response.content, 'lxml')
                infos = soup.select('.img-responsive.lazy.image_dta')
                condition.acquire()
                try:
                    for info in infos:
                        image_url = info['data-original']
                        image_urls.append(image_url)
                finally:
                    condition.notify()
                    condition.release()
                time.sleep(1)
            except Exception as e:
                print('failed,error:%s, current url:%s' % (e, p_url))


class Consumer(threading.Thread):  # 消费者：负责从image_urls提取表情链接，并下载
    def run(self):
        print('Consumer is running ------', threading.current_thread())
        while True:
            condition.acquire()
            try:
                if not image_urls:  # if len(image_url_list) == 0:
                    print('image_urls is empty,the consumer is waiting!')
                    condition.wait()
                image_url = image_urls.pop()
            finally:
                condition.release()
            filename = image_url.split('/')[-1]
            path = 'D:\\song\\' + filename
            urllib.request.urlretrieve(image_url, filename=path)
            print('表情：%s 下载完成！' % filename)
            if len(page_urls) == 0 and len(image_urls) == 0:
                print('page_urls & image_urls -----> empty!')
                break
        print('consumer over!')


if __name__ == '__main__':
    start = time.perf_counter()  # 建议不用time.time(),  time.clock()方法在3.3中废弃，将在3.8中移除
    for x in range(2):  # 2个生产者线程，去从页面中爬取表情链接
        Producer().start()

    for x in range(4):  # 4个消费者线程，去从FACE_URL_LIST中提取下载链接
        Consumer().start()
    end = time.perf_counter()
    print('main_thread end! use time is: ', start - end)  # 建立线程用时
