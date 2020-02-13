# aid->cid api
# https://api.bilibili.com/x/web-interface/view?aid=18109462

# play url flv
# https://api.bilibili.com/x/player/playurl?avid=69542806&cid=120570181&qn=0&type=&otype=json

# play url html5 mp4
# https://api.bilibili.com/x/player/playurl?avid=69542806&cid=120570181&qn=0&type=&otype=json&fnver=0&fnval=16

import requests

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Cookie': 'SESSDATA=970fa54d%2C1581764515%2C718f5c11', # 登录B站后复制一下cookie中的SESSDATA字段,有效期1个月
        'Host': 'api.bilibili.com'
    }
start = input('请输入您要下载的B站av号(纯数字):')
avid = str(start)

res = requests.get("https://api.bilibili.com/x/web-interface/view?aid=" + avid).json()
cid = str(res['data']['pages'][0]['cid'])

print('######  FLV')
res = requests.get("https://api.bilibili.com/x/player/playurl?avid=" + avid + "&cid=" + cid+"&qn=16&type=&otype=json",
                   headers=headers).json()
url = res['data']['durl'][0]['url']
size = res['data']['durl'][0]['size']
part = str(size//2)
print(part)
print(res['data']['accept_description'])
print(res['data']['accept_quality'])


print("quality:" + str(res['data']['quality']))
size = int(size)/1024/1024
print("%.2f MB" % size)

# print('\n######  MP4')
# res = requests.get("https://api.bilibili.com/x/player/playurl?avid=" + avid + "&cid=" + cid
#                    + "&qn=116&type=&otype=json&fnver=0&fnval=16",
#                    headers=headers).json()
#
# print(res['data']['accept_description'])
# print(res['data']['accept_quality'])
#
# print(res['data']['quality'])

headers ={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US, en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Range': 'bytes=0-7154214',  # Range 的值要为 bytes=0- 才能下载完整视频
        'Referer': "https://api.bilibili.com/x/web-interface/view?aid=" + avid + "/?p=0",  # 注意修改referer,必须要加的!
        'Origin': 'https://www.bilibili.com',
        'Connection': 'keep-alive',
}

print("Downloading...Just a moment...")
r = requests.get(url, stream=True, headers=headers)
with open("av" + str(start) + ".flv", "wb") as flv:
    total = 0
    for chunk in r.iter_content(chunk_size=2048):
        if chunk:
            total = total + 2
            per = total / (size * 1024) * 100

            flv.write(chunk)
            if per > 100:
                print("Process 100.00%")
            else:
                print("Process %.2f %%" % per)
