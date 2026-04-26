#!/usr/bin/env python
import urllib.request as req
import json
import os, glob
import time
import argparse

import multiprocessing as mp
from multiprocessing import Pool

mp.set_start_method('fork')

_PROCNUM = 256

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
            #print('retry ', url)
    print(path)

def dlassets(assets):
    print('downloading ass')
    args = [
        (
            'https://resources.download.minecraft.net/'+assets['objects'][i]['hash'][:2]+'/'+assets['objects'][i]['hash'],
            'assets/' + i
        ) for i in assets['objects'].keys()
    ]
    with Pool(processes=_PROCNUM) as pool:
        pool.starmap(dlfile,args)

def dllibs(libs):
    print('downloading libs')
    args = [
       (
           i['downloads']['artifact']['url'],
           'libraries/' + i['downloads']['artifact']['path']
       ) for i in libs
    ]
    with Pool(processes=_PROCNUM) as pool:
        pool.starmap(dlfile,args)


def download(vername):
    man_url = 'https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'
    man = rjson(man_url)

    ver = rjson(find_ver_url(man,vername))

    dllibs(ver['libraries'])

    assets = rjson(ver['assetIndex']['url'])

    dlassets(assets)

    # download client

    url = ver['downloads']['client']['url']

    dlfile(url,'client.jar')

    classpath = ''
    for f in glob.glob('**/*.jar',recursive=True):
        classpath += f + ':'

    str_run = '#/bin/bash\n'+'java '+ '-cp ' + classpath + ' ' + ver['mainClass'] + " -accessToken 0 -version 30"
    with open('run.sh', 'w') as f:
        f.write(str_run)
    os.system('chmod +x run.sh')


if __name__ == '__main__':
    prs = argparse.ArgumentParser()
    prs.add_argument('-v', '--version', help='specify the version that you want to download (may be buggy with older versions)')
    prs.add_argument('-p', '--procnum', help='specify the number of processes to download with (default 256)')

    args = prs.parse_args()

    if(args.procnum):
        _PROCNUM = args.procnum

    download(args.version)
