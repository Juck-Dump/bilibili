import requests
import qrcode
from time import sleep
import base64
import os
from progressbar import *
import threading


def check_session(key=""):
    if key == "":
        if not os.path.exists(".\BSESSDATA.txt"):
            file = open(".\BSESSDATA.txt", "w", encoding='utf8')
            file.close()
        with open(".\BSESSDATA.txt", "r", encoding='utf8') as BSE:
            b_sekey = BSE.read()
            try:
                b_key = base64.b85decode(bytes(b_sekey, encoding='utf8'))
                key = str(b_key, encoding='utf8')[:-2]
            except:
                print("# BSESSDATA文件错误!")

    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/79.0.3945.130 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://www.bilibili.com',
        'Referer': "https://www.bilibili.com/",
        'Connection': 'keep-alive',
        'Host': 'api.bilibili.com',
        'cookie': 'SESSDATA=' + key + ";",
    }

    cookie_dic = {
        'SESSDATA': key
    }

    ses = requests.session()
    requests.utils.add_dict_to_cookiejar(ses.cookies, cookie_dic)
    res = ses.get("https://api.bilibili.com/x/space/myinfo", headers=header).json()
    if res['code'] == 0:
        return {'status': 0, 'key': key, 'myinfo': res}
    else:
        return {'status': -1, 'myinfo': res}


def login():
    header1 = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': "https://passport.bilibili.com/login",
        'Origin': 'https://passport.bilibili.com',
        'Connection': 'keep-alive',
        'Host': 'passport.bilibili.com',
    }
    while 1:
        ses = requests.session()
        res = ses.get("https://passport.bilibili.com/qrcode/getLoginUrl", headers=header1).json()
        oauthkey = res['data']['oauthKey']
        qr = qrcode.make(res['data']['url'])
        qr.show()
        while 1:
            res = ses.post("https://passport.bilibili.com/qrcode/getLoginInfo", headers=header1,
                           data={
                               'oauthKey': oauthkey,
                               'gourl': 'https://passport.bilibili.com/account/security'
                                 }).json()
            if res['status']:
                key = str(ses.cookies.get_dict()['SESSDATA'])
                ret = check_session(key)
                key = key + "39"
                b_sekey = base64.b85encode(bytes(key, encoding='utf8'))
                with open("BSESSDATA.txt", 'wb') as txt:
                    txt.write(b_sekey)
                return ret
            else:
                if res['data'] == -5:
                    print("# APP未确认!")
                if res['data'] == -2:
                    print("# 二维码已过期!")
                    choice = input("# 是否重试? [y/n]:")
                    if choice == 'y':
                        break
                    elif choice == 'n':
                        ret = check_session(" ")
                        return ret
            sleep(4)


def analyze_flv(aid, key):
    ret = {}
    header1 = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/79.0.3945.130 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://www.bilibili.com',
        'Referer': "https://www.bilibili.com/video/av" + str(aid),
        'Connection': 'keep-alive',
        'Host': 'api.bilibili.com',
        'cookie': 'SESSDATA=' + key + ";",
    }

    res = requests.get("https://api.bilibili.com/x/web-interface/view?aid=" + aid, headers=header1).json()
    ret["av_info"] = res['data']
    title = res['data']['title'].replace('\\', ' ').replace('/', ' ')
    print("# AV标题: %s" % res['data']['title'])

    pages = len(res['data']['pages'])
    pid = 0
    if pages == 1:
        print("# 共1P 已自动选择P1")
    else:
        pid = int(input("# 共%dP 请选择(数字): " % pages)) - 1
    print("# 分P标题: %s" % res['data']['pages'][pid]['part'])
    cid = str(res['data']['pages'][pid]['cid'])

    res = requests.get(
        "https://api.bilibili.com/x/player/playurl?avid=" + aid + "&cid=" + cid + "&qn=0&type=&otype=json",
        headers=header1).json()
    print("# 可下载的清晰度: %s" % res['data']['accept_description'])
    print("# 对应清晰度代码: %s" % res['data']['accept_quality'])
    qn = input("# 选择下载清晰度(输入数字代码): ")
    ret['qn'] = int(qn)
    res = requests.get(
        "https://api.bilibili.com/x/player/playurl?avid=" + aid + "&cid=" + cid + "&qn="
        + str(qn) + "&type=&otype=json", headers=header1).json()
    size = res['data']['durl'][0]['size']
    print("# 获得清晰度: " + str(res['data']['quality']))
    size = int(size)
    print("# 文件大小: %d Byte" % size)
    ret["c_info"] = res['data']
    ret["pid"] = pid

    path = "[av%s]-[%s]-[%s]" % (aid, qn, title)
    folder = os.path.exists(path)
    if not folder:
        os.mkdir(path)
    ret['folder'] = path
    return ret


def download_flv(start, size, aid, url, pid, qn, part, path):
    global process
    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US, en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Range': 'bytes=' + str(start) + '-' + (str(start + size) if size > 0 else ''),  # Range 的值要为 bytes=0- 才能下载完整视频
        'Referer': "https://api.bilibili.com/x/web-interface/view?aid=" + aid + "/?p=" + str(part - 1),
        'Origin': 'https://www.bilibili.com',
        'Connection': 'keep-alive',
    }

    res = requests.get(url, stream=True, headers=header)
    with open("%s\\av%s_p%s_%d_part%s.flv" % (path, aid, pid, qn, part), "ab+") as flv:

        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                re = flv.write(chunk)
                process[part - 1] = process[part - 1] + re


def main():
    global process
    ret = check_session()
    if ret['status'] == 0:
        print("# 登录成功!")
    else:
        print("# %s" % ret['myinfo']['message'])
        while 1:
            choice1 = input("# 是否使用二维码登录? [y/n]:")
            if choice1 == 'y':
                print("# 请用APP扫描二维码!")
                ret = login()
                if ret['status'] == 0:
                    print("# 登录成功!")
                    break
                else:
                    print("# %s" % ret['myinfo']['message'])
            elif choice1 == 'n':
                while 1:
                    choice2 = input("# 是否手动设置SESSDATA? [y/n]:")
                    if choice2 == 'y':
                        while 1:
                            manual_sessdata = input("# 输入SESSDATA(32位):")
                            if len(manual_sessdata) == 32:
                                print("# Get it! Try again!")
                                ret = check_session(manual_sessdata)
                                if ret['status'] == 0:
                                    key = ret['key'] + "39"
                                    b_sekey = base64.b85encode(bytes(key, encoding='utf8'))
                                    with open("BSESSDATA.txt", 'wb') as txt:
                                        txt.write(b_sekey)
                                    break
                                else:
                                    print("# %s" % ret['myinfo']['message'])
                            else:
                                print("# 输入错误!请重试!")
                        break
                    elif choice2 == 'n':
                        print("# Quit...")
                        sleep(3)
                        exit(0)
                    else:
                        print("# 输入错误!请重试!")
                break
            else:
                print("# 输入错误!请重试!")
    avid = input("# 输入AV号(只输入\"av\"后的数字):")
    av_info = analyze_flv(avid, ret['key'])
    # print(av_info['c_info']['durl'][0])
    urls = [av_info['c_info']['durl'][0]['url'],
            av_info['c_info']['durl'][0]['backup_url'][0]]

    size = int(av_info['c_info']['durl'][0]['size'])
    part_size = size // 4
    # print("# part-size: %d" % part_size)
    part1 = threading.Thread(target=download_flv, args=(0, part_size,
                                                        avid, urls[0],
                                                        av_info['pid'], av_info['qn'], 1, av_info['folder']))
    part2 = threading.Thread(target=download_flv, args=(part_size + 1, part_size,
                                                        avid, urls[1],
                                                        av_info['pid'], av_info['qn'], 2, av_info['folder']))
    part3 = threading.Thread(target=download_flv, args=(part_size * 2 + 2, part_size,
                                                        avid, urls[0],
                                                        av_info['pid'], av_info['qn'], 3, av_info['folder']))
    part4 = threading.Thread(target=download_flv, args=(part_size * 3 + 3, -1,
                                                        avid, urls[1],
                                                        av_info['pid'], av_info['qn'], 4, av_info['folder']))

    print("# 下载中...请稍后...")

    part1.start()
    part2.start()
    part3.start()
    part4.start()

    bar = ProgressBar().start()
    while 1:
        size_all = process[0] + process[1] + process[2] + process[3]
        if size_all >= size:
            bar.update(100)
            sleep(1)
            print("\n# 下载完成!")
            break
        bar.update((size_all / size) * 100)
        sleep(1)

    print("# 合并文件中...")
    file1 = open("%s\\av%s_p%d_%d_part1.flv" % (av_info['folder'], avid, av_info['pid'], av_info['qn']), "rb")
    file2 = open("%s\\av%s_p%d_%d_part2.flv" % (av_info['folder'], avid, av_info['pid'], av_info['qn']), "rb")
    file3 = open("%s\\av%s_p%d_%d_part3.flv" % (av_info['folder'], avid, av_info['pid'], av_info['qn']), "rb")
    file4 = open("%s\\av%s_p%d_%d_part4.flv" % (av_info['folder'], avid, av_info['pid'], av_info['qn']), "rb")

    file_all = open("%s\\av%s_p%d_%d.flv" % (av_info['folder'], avid, av_info['pid'], av_info['qn']), "wb")

    while 1:
        file_bytes = file1.read(4096)
        if not file_bytes:
            break
        file_all.write(file_bytes)
    file1.close()
    os.remove("%s\\av%s_p%d_%d_part1.flv" % (av_info['folder'], avid, av_info['pid'], av_info['qn']))

    while 1:
        file_bytes = file2.read(4096)
        if not file_bytes:
            break
        file_all.write(file_bytes)
    file2.close()
    os.remove("%s\\av%s_p%d_%d_part2.flv" % (av_info['folder'], avid, av_info['pid'], av_info['qn']))

    while 1:
        file_bytes = file3.read(4096)
        if not file_bytes:
            break
        file_all.write(file_bytes)
    file3.close()
    os.remove("%s\\av%s_p%d_%d_part3.flv" % (av_info['folder'], avid, av_info['pid'], av_info['qn']))

    while 1:
        file_bytes = file4.read(4096)
        if not file_bytes:
            break
        file_all.write(file_bytes)
    file4.close()
    os.remove("%s\\av%s_p%d_%d_part4.flv" % (av_info['folder'], avid, av_info['pid'], av_info['qn']))
    file_all.close()

    print("# 合并完成")


process = [0, 0, 0, 0]
print("# Welcome! Designed by love_the_lover...")
main()


