#!/usr/bin/env python
import urllib.request as req
import json
import os, glob, stat
import time
import argparse
from zipfile import ZipFile
import shutil

import multiprocessing as mp
from multiprocessing import Pool

#mp.set_start_method('fork')

_PROCNUM = 60

def rjson(url):
    return json.loads(req.urlopen(url).read().decode())

def find_ver_url(man,vername):
    for i in man['versions']:
        if(i['id']==vername):
            return i['url']

def dlfile(url,path):
    if(os.path.exists(path)):
        #print('skip ', path)
        return
    os.makedirs(os.path.dirname(path) or '.',exist_ok=True)
    while True:
        try:
            req.urlretrieve(url,path)
            break
        except Exception as e:
            time.sleep(0.2)
            #print('retry ', url)
    print(path)

def dlassets(assets, vername):
    print('downloading ass')
    dls = []
    for i in assets['objects'].keys():
        dls.append((
            'https://resources.download.minecraft.net/'+assets['objects'][i]['hash'][:2]+'/'+assets['objects'][i]['hash'],
            'assets/' + assets['objects'][i]['hash']
        ))

    with Pool(processes=_PROCNUM) as pool:
        pool.starmap(dlfile,dls)

    for i in assets['objects'].keys():
        pth = 'versions/' + vername + '/assets/' + i;
        os.makedirs(os.path.dirname(pth), exist_ok=True)
        shutil.copy('assets/' + assets['objects'][i]['hash'], pth)

def dllibs(libs, vername):
    print('downloading libs')

    try:
        args = []
        for i in libs:

            if 'artifact' in i['downloads']:
                args.append(
                    (
                        i['downloads']['artifact']['url'],
                        'libraries/' + i['downloads']['artifact']['path']
                    )
                )

            if 'classifiers' in i['downloads']:
                for clsk in i['downloads']['classifiers'].keys():
                    cls = i['downloads']['classifiers'][clsk]
                    args.append(
                        (
                            cls['url'],
                            'libraries/' + cls['path']
                        )
                    )
    except Exception as e:
        print(json.dumps(libs,indent=4))
        raise e

    with Pool(processes=_PROCNUM) as pool:
        pool.starmap(dlfile,args)


    for i in args:
        pth = 'versions/' + vername + '/' + i[1];
        os.makedirs(os.path.dirname(pth), exist_ok=True)
        shutil.copy(i[1], pth)



    for i in libs:
        if 'classifiers' in i['downloads']:
            for clsk in i['downloads']['classifiers'].keys():
                cls = i['downloads']['classifiers'][clsk]
                with ZipFile('versions/' + vername + '/libraries/' + cls['path'], 'r') as zf:
                    zf.extractall(path='versions/' + vername + '/natives/')


def download(vername):
    os.makedirs('versions/' + vername, exist_ok=True)
    #os.chdir('versions/' + vername)
    man_url = 'https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'
    man = rjson(man_url)

    ver = rjson(find_ver_url(man,vername))

    dllibs(ver['libraries'], vername)

    assets = rjson(ver['assetIndex']['url'])

    dlassets(assets, vername)

    # download client

    url = ver['downloads']['client']['url']

    dlfile(url,'versions/' + vername + '/client.jar')

    # make run script
    os.chdir('versions/' + vername)
    classpath = ''
    classpath_win = ''
    for f in glob.glob('**/*.jar',recursive=True):
        classpath += f + ':'
        classpath_win += f + ';'

    str_run = '#/bin/bash\n'\
    +'java '+ '-cp ' + classpath\
    + ' -Djava.library.path=natives/ '\
    + ver['mainClass']\
    + " -accessToken 0 -version 30 -userProperties {}"

    str_run_win = 'java '+ '-cp ' + classpath_win\
    + ' -Djava.library.path=natives/ '\
    + ver['mainClass']\
    + " -accessToken 0 -version 30 -userProperties {}"


    with open('run.sh', 'w') as f:
        f.write(str_run)

    os.chmod('run.sh', os.stat('run.sh').st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    with open('run.bat', 'w') as f:
        f.write(str_run_win)


if __name__ == '__main__':
    prs = argparse.ArgumentParser()
    prs.add_argument('-v', '--version', help='specify the version that you want to download')
    prs.add_argument('-p', '--procnum', help='specify the number of processes to download with (default 256)')

    args = prs.parse_args()

    if(args.procnum):
        _PROCNUM = int(args.procnum)

    if(args.version):
        download(args.version)
    else:
        print("THOU HAVEN'T GIVEN THE VERSION")
