#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

import simplejson as json
import urllib.request, urllib.error, urllib.parse
from urllib.parse import urljoin

import urlutil

def getRecordedList(serverUrl, recLen,
                    rule=None, genre=None, keyword=None):
    requestParam = 'isHalfWidth=false&limit=' + str(recLen) + '&offset=0'
    if rule is not None:
        requestParam += '&ruleId=' + str(rule)
    if genre is not None:
        requestParam += '&genre=' + str(genre)
    if keyword is not None:
        requestParam += '&keyword=' + urllib.parse.quote(keyword)

    urlInfo = urlutil.getUrlInfo(serverUrl)

    request = urllib.request.Request(url=urljoin(urlInfo["url"], 'api/recorded?' + requestParam), headers=urlInfo["headers"])
    response = urllib.request.urlopen(request)
    strjson = response.read()
    videos = json.loads(strjson)['records']
    return videos

def getRecordingList(serverUrl, recLen,
                    rule=None, genre=None, keyword=None):
    urlInfo = urlutil.getUrlInfo(serverUrl)

    request = urllib.request.Request(url=urljoin(urlInfo["url"], 'api/recording?isHalfWidth=true&limit=' + str(recLen) + '&offset=0'), headers=urlInfo["headers"])
    response = urllib.request.urlopen(request)
    strjson = response.read()
    videos = json.loads(strjson)['records']
    return videos

def analyzeFileName(progs):
    count = 0
    folders = []
    for p1 in progs:
        count += 1
        exist = False
        for f in folders:
            if f['name'] in p1['name']:
                exist = True
                f['count'] += 1
                break
        if not exist:
            for p2 in progs[count:]:
                name = checkName(p1['name'], p2['name'])
                if name:
                    folders.append({'name':name, 'count':1})
                    break
    return folders

def checkName(pn1, pn2):
    dupName = None
    p1 = delHead(pn1)
    p2 = delHead(pn2)
    dupName = separate(p1, p2, u'#')
    if dupName is None:
        dupName = separate(p1, p2, u'♯')
#    if dupName is None:
#        dupName = separate(p1, p2, u'「')
    if dupName is None:
        dupName = separate2(p1, p2, u'(.+)(第.*話).*')
    if dupName is None:
        dupName = separate2(p1, p2, u'(.+)([①-⑩]).*')
    if dupName is None:
        dupName = separate2(p1, p2, u'(.+)(\s.{1,2}話).*')
    if dupName is None:
        dupName = separate2(p1, p2, u'(.+)(【.*】).*')
    if dupName is None:
        if p1 == p2:
            #print('  ZZ:[{}], [{}]'.format(p1, p2))
            dupName = p1
    if dupName:
        dupName = dupName.rstrip(u' ')
    return dupName

def delHead(name):
    ret = name.replace(u'[新]', '')
    ret = ret.replace(u'[終]', '')
    ret = ret.replace(u'[字]', '')
    ret = ret.replace(u'[再]', '')
    ret = ret.replace(u'[デ]', '')
    return ret

def separate(p1, p2, s):
    if s in p1 and s in p2:
        if p1.split(s)[0] == p2.split(s)[0]:
            if p1.split(s)[0] != '':
                return p1.split(s)[0]
    return None

def separate2(p1, p2, numbers):
    p1e = re.match(numbers, p1)
    p2e = re.match(numbers, p2)
    if p1e and p2e:
        #print('  SS:[{}], [{}]'.format(p1e.group(1), p2e.group(1)))
        if p1e.group(1) == p2e.group(1):
            return p1e.groups()[0]
    return None
