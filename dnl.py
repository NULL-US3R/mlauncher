import urllib.request as req
import json
import os
import time

from multiprocessing import Process
def rjson(url):
    return json.loads(req.urlopen(url).read().decode())

def find_ver_url(man,vername):
    for i in man['versions']:
        if(i['id']==vername):
            return i['url']

def dlfile(url,path):
    if(os.path.exists(path) and os.path.getsize(path)!=0):
        #print('skip ', path)
        return
    os.makedirs(os.path.dirname(path) or '.',exist_ok=True)
    while True:
        try:
            req.urlretrieve(url,path)
            break
        except Exception as e:
            time.sleep(0.1)
            print('retry ', url)
    print(path)

def dlassets(assets):
    print('downloading ass')
    pr = []
    for i in assets['objects'].keys():
        hsh = assets['objects'][i]['hash']
        b = hsh[:2]
        url = 'https://resources.download.minecraft.net/'+b+'/'+hsh
        p = Process(target=dlfile,args=(url,'assets/' + i))
        pr.append(p)
        p.start()
    for p in pr:
        p.join()

def dllibs(libs):
    print('downloading libs')
    pr =[]
    for i in libs:
        path = 'libraries/' + i['downloads']['artifact']['path']
        url = i['downloads']['artifact']['url']
        p = Process(target=dlfile,args=(url,path))
        pr.append(p)
        p.start()
    for p in pr:
        p.join()

man_url = 'https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'
man = rjson(man_url)

vername = man['latest']['release']

ver = rjson(find_ver_url(man,vername))

assets = rjson(ver['assetIndex']['url'])

dlassets(assets)

dllibs(ver['libraries'])

# download client

url = ver['downloads']['client']['url']

dlfile(url,'client.jar')

#print(json.dumps(ver,indent=4))
