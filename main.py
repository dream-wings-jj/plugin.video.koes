#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import xbmcgui
import xbmcplugin
import xbmcaddon
import datetime
import simplejson as json
import urllib.request, urllib.error, urllib.parse
import urlutil
from urllib.parse import parse_qs
from consts import *
from genlist import *

pluginUrl = sys.argv[0]
addon_handle = int(sys.argv[1])
settings = xbmcaddon.Addon('plugin.video.koes')

#file='/tmp/plugin.log'
#fp = open(file, 'a')

def w(s):
    if fp:
        fp.write(s)
        fp.write('\n')

def popup(msg):
    xbmcgui.Dialog().ok('xxx', msg)
    return

def addList(video, server_url):
    li = xbmcgui.ListItem(video['name'])
    if video['thumbnails']:
        thumbnail_url = urljoin(server_url, 'api/thumbnails/' + str(video['thumbnails'][0]))
        li.setArt({
            'poster': thumbnail_url,
            'fanart': thumbnail_url,
            'landscape': thumbnail_url,
            'thumb': thumbnail_url
        })

    startdate = datetime.datetime.fromtimestamp(video['startAt'] / 1000)

    info = {
        'originaltitle': video['name'],
        'title': video['name'],
        'sorttitle': video['name'],
        'tvshowtitle': video['name'],
        'album':  video['name'],
        'year': startdate.strftime('%Y'),
        'date': startdate.strftime('%d.%m.%Y'),
        'aired': startdate.strftime('%Y-%m-%d'),
        'dateadded': startdate.strftime('%Y-%m-%d %H:%M:%S'),
        'duration': (video['endAt'] - video['startAt']) / 1000,
    }

    try:
        # ジャンル
        if 'genre1' in video and video['genre1'] in GENRE1:
            # ジャンル1
            info['genre'] = GENRE1[video['genre1']]

            # サブジャンル
            if 'subGenre1' in video and video['genre1'] in GENRE2 and video['subGenre1'] in GENRE2[video['genre1']]:
                info['genre'] += ' / ' + GENRE2[video['genre1']][video['subGenre1']]

        # 詳細
        if 'description' in video and not 'extended' in video:
            info['plot'] = video['description']
            info['plotoutline'] = video['description']
        elif 'description' in video and 'extended' in video:
            info['plot'] = video['description'] + '\n\n' + video['extended']
            info['plotoutline'] = video['description']
    except:
        print('error')

    li.setInfo('video', info)

    li.addContextMenuItems([
        ('更新', 'Container.Refresh'),
        ('削除', 'RunScript(%s/delete.py, %d, %s)' % (settings.getAddonInfo('path'), video['id'], video['name']))
    ])

    video_url = urljoin(server_url, 'api/videos/' + str(video['videoFiles'][0]['id']))

    xbmcplugin.addDirectoryItem(handle=addon_handle, url=video_url, listitem=li)

def getServerUrl():
    serverUrl = settings.getSetting('server_url')
    if not serverUrl:
        settings.openSettings()
        serverUrl = settings.getSetting('server_url')
    return serverUrl

def listTitle():
    videos = getRecordedList(getServerUrl(), recLen=2000)
    list = analyzeFileName(videos)
    for l in list:
        li = xbmcgui.ListItem(l['name']+'('+str(l['count'])+')')
        url = u'{0}?list=Title&name={1}'.format(pluginUrl, l['name'])
        xbmcplugin.addDirectoryItem(handle=addon_handle,
                                    url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

def listGenre():
    for genre in [0x3, 0x7, 0x6, 0x4, 0x1,
                  0x0, 0x2, 0x5, 0x8, 0x9, 0xA, 0xB, 0xF]:
        li = xbmcgui.ListItem(GENRE1[genre])
        url = '{0}?list=Genre&id={1}'.format(pluginUrl, genre)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

def listItemsInGenre(genreId):
    videos = getRecordedList(getServerUrl(),
                             recLen=settings.getSetting('recorded_length'),
                             genre=genreId)
    if len(videos) > 10:
        list = analyzeFileName(videos)
        for l in list:
            li = xbmcgui.ListItem(l['name']+'('+str(l['count'])+')')
            url = u'{0}?list=Genre&id={1}&name={2}'.format(pluginUrl,
                                                           genreId, l['name'])
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                        listitem=li, isFolder=True)
        newList = []
        for video in videos:
            isFound = False
            for l in list:
                if l['name'] in video['name']:
                    isFound = True
                    break
            if not isFound:
                newList.append(video)
        makeList(newList)
    else:
        makeList(videos)

def listRule():
    server_url = settings.getSetting('server_url')
    if not server_url:
        settings.openSettings()
        server_url = settings.getSetting('server_url')
    urlInfo = urlutil.getUrlInfo(server_url)

    request = urllib.request.Request(url=urljoin(urlInfo["url"], 'api/rules?limit=50'), headers=urlInfo["headers"])
    response = urllib.request.urlopen(request)
    strjson = response.read()
    rules = json.loads(strjson)['rules']

    for rule in rules:
        keyword = rule['searchOption'].get('keyword', None)
        if keyword:
            li = xbmcgui.ListItem(keyword)
        else:
            li = xbmcgui.ListItem('(None)')
        url = '{0}?list=Rule&id={1}'.format(pluginUrl, rule['id'])
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

def listItems(rule=None, genre=None, keyword=None):
    videos = getRecordedList(getServerUrl(),
                             recLen=settings.getSetting('recorded_length'),
                             rule=rule, genre=genre, keyword=keyword)
    if keyword is not None:
        newList = []
        for video in videos:
            if keyword in str(video['name']):
                newList.append(video)
        makeList(newList)
    else:
        makeList(videos)

def makeList(videos):
    server_url = settings.getSetting('server_url')
    for video in videos:
        addList(video, server_url)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.setContent(addon_handle, 'movies')
    xbmcplugin.endOfDirectory(addon_handle)

def recordedAll():
    videos = getRecordedList(getServerUrl(),
                             recLen=settings.getSetting('recorded_length'))
    videos += getRecordingList(getServerUrl(), recLen=2000)
    makeList(videos)

def listMain():
    li = xbmcgui.ListItem('すべて')
    #li.setIsFolder(True)
    url = '{0}?list=Recorded'.format(pluginUrl)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    li = xbmcgui.ListItem('ジャンル')
    #li.setIsFolder(True)
    url = '{0}?list=Genre'.format(pluginUrl)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    li = xbmcgui.ListItem('ルール')
    #li.setIsFolder(True)
    url = '{0}?list=Rule'.format(pluginUrl)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    li = xbmcgui.ListItem('タイトル')
    #li.setIsFolder(True)
    url = '{0}?list=Title'.format(pluginUrl)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

def menulist(paramstring):
    params = parse_qs(paramstring[1:])
    if params:
        if params['list'][0] == 'Recorded':
            recordedAll()
        elif params['list'][0] == 'Rule':
            id = params.get('id', None)
            if id:
                listItems(rule=int(id[0]))
            else:
                listRule()
        elif params['list'][0] == 'Genre':
            id = params.get('id', None)
            if id is not None:
                id = int(id[0])
            name = params.get('name', None)
            if name:
                name = name[0]
            if id is not None:
                if name:
                    listItems(genre=id, keyword=name)
                else:
                    listItemsInGenre(id)
            else:
                listGenre()
        elif params['list'][0] == 'Title':
            name = params.get('name', None)
            if name:
                listItems(keyword=name[0])
            else:
                listTitle()
        else:
            listMain()
    else:
        listMain()
    return

if __name__ == '__main__':
    server_url = settings.getSetting('server_url')
    recorded_length = settings.getSetting('recorded_length')

    if not server_url:
        settings.openSettings()
        server_url = settings.getSetting('server_url')

    menulist(sys.argv[2])
