# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 01:32:47 2023

@author: Administrator

Requirements:

1. pip install PyExecJS (pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyExecJS)
2. pip install qrcode
"""
import urllib
import urllib.request
import http.cookiejar
import json
import qrcode
import socket
import execjs   
import contextlib
import ssl
import re
import os
import time

from urllib.error import HTTPError



global userAgent 
global context

douyinCookieJsonFile    = 'douyinCookiesJson.txt'
douyinCookieFile        = 'douyinCookies.txt'
work_path               = os.getcwd()
AllinOneFolder          = 'colcake'
userAgent               = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
context                 = ssl._create_unverified_context()


def urlretrieve_evo(url, filename=None, data=None, headers=None):
    url_req = urllib.request.Request(url)
    if headers:
        for key, val in headers:
            url_req.add_header(key, val) #新的header将覆盖同名header,缺少则新增
    with contextlib.closing(urllib.request.urlopen(url_req, data,context=context)) as fp:
    # with contextlib.closing(urllib.request.urlopen(url_req, data)) as fp:   
        fp_info = fp.info()
        if filename:
            tfp = open(filename, 'wb')
        else:
            raise Exception('filename is not given.')
        with tfp:
            '''回调函数
            @blocknum: 已经下载的数据块
            @bs: 数据块的大小
            @size: 远程文件的大小
            '''
            # result = filename, headers
            bs = 1024*8
            size = -1
            read = 0
            blocknum = 0
            if "content-length" in fp_info:
                size = int(fp_info["Content-Length"])
            while True:
                block = fp.read(bs)
                if not block:
                    break
                read += len(block)
                tfp.write(block)
                blocknum += 1
                # 显示下载进度
                # sys.stdout.write('\r>> Downloading %s %.1f%% %.1fKB   ' % (filename, (float(blocknum * bs) / float(size) * 100.0), (float(blocknum * bs) / 1024.0)))
                # sys.stdout.flush()
    return size


def strSafe(name):
    newname = re.sub('[^A-Za-z0-9\u4e00-\u9fa5【】\[\]]+', '', name) # 字符筛选
    return newname


# 把EditThisCookie导出的json文件转换为Mozilla—Netscape格式的文件
def cookieFileGen(cookieJsonFile,cookieMozillaFile):
    with open(cookieJsonFile,'r') as f:
        cookieDict = json.load(f)
    with open(cookieMozillaFile,'w',encoding='utf-8') as f:
        f.writelines('# Netscape HTTP Cookie File\n') # magic sign
        f.writelines('# http://curl.haxx.se/rfc/cookie_spec.html\n') # magic sign
        f.writelines('# This is a generated file!  Do not edit.\n\n') # magic sign
        for eachCookie in cookieDict: # domain, domain_specified, path, secure, expires, name, value
            initial_dot = "TRUE" if eachCookie['domain'].startswith(".") else "FALSE"
            secure = "TRUE" if eachCookie['secure'] else "FALSE"
            if 'expirationDate' in eachCookie:
                expires = str(int(eachCookie['expirationDate']))
            else:
                expires = ""
            if eachCookie['value'] is None:
                # cookies.txt regards 'Set-Cookie: foo' as a cookie
                # with no name, whereas http.cookiejar regards it as a
                # cookie with no value.
                name = ""
                value = eachCookie['name']
            else:
                name = eachCookie['name']
                value = eachCookie['value']
            if(eachCookie['name']):
                f.write('\t'.join([eachCookie['domain'],initial_dot,eachCookie['path'],secure,expires,name,value])+'\n')


# 创建Cookie文件
def cake_init(cookies_filename, UA, proxy = ''):
    socket.setdefaulttimeout(60) # 设置60秒超时
    proxy_support = urllib.request.ProxyHandler({'http':proxy,'https':proxy}) if proxy else urllib.request.ProxyHandler({})
    cookiejar = http.cookiejar.MozillaCookieJar(cookies_filename) # 加载cookies内容 cookiejar.save()能够保存文件
    cookie_support = urllib.request.HTTPCookieProcessor(cookiejar)
    opener = urllib.request.build_opener(proxy_support,cookie_support)# urllib钢铁侠组配
    opener.addheaders = [('User-agent', UA),
                         ('authority', "www.douyin.com"),
                         ('referer', "https://www.douyin.com/")]
    urllib.request.install_opener(opener) #urllib钢铁侠开机初始化
    return cookiejar


def getjson(api_url,postdata={}):
    response  = urllib.request.urlopen(api_url,data=urllib.parse.urlencode(postdata).encode('utf-8'))
    data_json = json.loads(response.read().decode('utf-8'))
    return data_json

def getpage(url,data=None):
    # url_req = urllib.request.Request(url)
    # url_req.add_header('referer','https://www.douyin.com/')
    # url_req.add_header('User-agent',userAgent)
    response = urllib.request.urlopen(url, data=data)
    video_html_rd = response.read()
    return video_html_rd


def qrshow(codeText):
    qrcode.make(codeText).show()


def qrlogin():
    API_login   = "https://sso.douyin.com/get_qrcode/?service=https%3A%2F%2Fwww.douyin.com"
    cake_init()
    loginJson   = getjson(API_login)
    qrcodeUrl   = loginJson['data']['qrcode_index_url']
    qrcodeToken = loginJson['data']['token']
    qrshow(qrcodeUrl) # 显示二维码图片
    return qrcodeToken


def qrcheck(qrcodeToken,is_frontier = 'false'):
    API_QRcheck = "https://sso.douyin.com/check_qrconnect/"
    POST_DICT   = {
        "service": "https://www.douyin.com",
        "token":qrcodeToken,
        "need_logo": "false",
        "is_frontier": is_frontier,
        "need_short_url": "false",
        "device_platform": "web_app",
        "account_sdk_source": "sso",
        "sdk_version": "2.2.5",
        "language": "zh",
        }
    jsonRes = getjson(API_QRcheck,POST_DICT)
    print(jsonRes)
    return jsonRes


def checklogin():
    API_logincheck = "https://sso.douyin.com/check_login/"
    res = getjson(API_logincheck)
    if res['has_login']:
        print("[-] 账号已登录。")
    else:
        print("[-] 账号未登录。")
    return res


def getColCakeUrl(cursor = 0,count=10):
    p = {
         'cursor':cursor,
         'aid':6383,
         'mstoken':'pce37o4ocAySu3sSedZoF-OV89snXqxmvCte-JvWvz1JQSKoUgEmueEof2ToiSVXdBTnB2su1bxiJ2XFKiyQqUGVWJ7Af8lHtveiOabzhfvaifZFNwkTwh3anGxok4A=',
         'webid':7225698522056640003,
         }
    api = 'https://www.douyin.com/aweme/v1/web/aweme/listcollection/?%s'%(urllib.parse.urlencode(p)) # 该接口可以获取视频链接
    xbogus = execjs.compile(open('./X-Bogus.js').read()).call('sign', urllib.parse.urlparse(api).query, userAgent)
    api_xbogus_signed = '%s&X-Bogus=%s'%(api,xbogus)
    cake_json = getjson(api_xbogus_signed,{'cursor':cursor,'count':count})
    return cake_json


# 先转换Cookie格式
cookieFileGen(douyinCookieJsonFile,douyinCookieFile)
cookiejar = cake_init(douyinCookieFile,UA = userAgent)
cookiejar.load(douyinCookieFile)
checklogin()
# getUserCake(user_url)


# def getUserCake(user_url):
cursor  = 0
usercakenum = 0


while(usercakenum < 1000):
    time.sleep(0.2)
    res = getColCakeUrl(cursor)
    if(len(res['aweme_list']) == 0):
        break
    else:
        print("[-] 下载%d个视频中。"%len(res['aweme_list']))
    cursor = res['cursor'] # 下一个指针
    for i in range(len(res['aweme_list'])):
        time.sleep(0.2)
        video_quality_list  = res['aweme_list'][i]['video']['bit_rate']
        if(video_quality_list):
            video_quality_list_sorted = sorted(video_quality_list,key=lambda x:x['bit_rate'],reverse=True)
            video_down_urls     = video_quality_list_sorted[0]['play_addr']['url_list'] # 选码率最高的视频下载源
            video_bit_rate      = video_quality_list_sorted[0]['bit_rate']
            video_quality       = video_quality_list_sorted[0]['gear_name'] # normal_1080_0
        else:
            print("[-] 非视频作品跳过")
            continue
        video_user_name     = res['aweme_list'][i]['author']['nickname']
        video_user_id       = res['aweme_list'][i]['author']['uid']
        # video_user_secid    = res['aweme_list'][i]['author']['sec_uid']
        video_name          = res['aweme_list'][i]['preview_title']
        video_id            = res["aweme_list"][i]["aweme_id"]

        video_url           = video_down_urls[0] # 随便选择一个下载源进行下载
        video_file_name     = '%s_%s_%s_%s.mp4'%(strSafe(video_user_name),strSafe(video_name),video_user_id,video_id)
        video_folder_name   = '%s_%s'%(strSafe(video_user_name),video_user_id)
        video_folder_path   = os.path.join(work_path,AllinOneFolder) if AllinOneFolder else os.path.join(work_path,video_folder_name) 
        video_file_path     = os.path.join(video_folder_path,video_file_name)

        # 如果没有视频文件夹则创建一个
        if not os.path.exists(video_folder_path):
            os.mkdir(video_folder_path)
        else:
            None
        
        video_exist_file = [i for i in os.listdir(video_folder_path) if i.split('_')[-1] == ("%s.mp4"%video_id)]
        if video_exist_file: # 如果文件下已经有该视频文件了，跳过下载
            print("[-] 视频已存在：%s"%video_exist_file[0])
            continue
        urlretrieve_evo_headers = [('referer', 'https://www.douyin.com/user/self'),('User-agent', userAgent)] # 添加上下载头，防止下载失败
        # -------------------------- 下载视频封面 --------------------------
        # cover_url_list      = res['aweme_list'][i]['video']['origin_cover']['url_list']
        # cover_file_name     = '%s_%s_%s_%s.jpeg'%(strSafe(video_user_name),strSafe(video_name),video_user_id,video_id)
        # cover_file_path     = os.path.join(video_folder_path,cover_file_name)
        # for cover_url in cover_url_list:
        #     try:
        #         if not os.path.exists(cover_file_path):
        #             urlretrieve_evo(cover_url,filename=cover_file_path,headers=urlretrieve_evo_headers)
        #             break
        #         else:
        #             None
        #     except HTTPError:
        #         print('[×] 下载失败：%s'%cover_file_name)
        # -----------------------------------------------------------------
        for video_url in video_down_urls:
            try:
                urlretrieve_evo(video_url,filename=video_file_path,headers=urlretrieve_evo_headers)
                break
            except HTTPError:
                print('[×] 下载失败：%s'%video_file_name)
        print('[√] 下载成功：【%s:%d】%s'%(video_quality,video_bit_rate,video_file_name))
        usercakenum += 1
print("[-] 共下载%d个视频"%usercakenum)
    


