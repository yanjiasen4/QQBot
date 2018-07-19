# -*- coding:gbk -*-

api_key = "e811b8f51ef167512c930353237c1773adb33d81"
minsim = '50!'

import requests
import json
import time
import sys
import os
import re
from collections import OrderedDict

# enable or disable indexes
index_hmags = '0'
index_hanime = '0'
index_hcg = '0'
index_ddbobjects = '0'
index_ddbsamples = '0'
index_pixiv = '1'
index_pixivhistorical = '1'
index_anime = '0'
index_seigaillust = '1'
index_danbooru = '0'
index_drawr = '1'
index_nijie = '1'
index_yandere = '0'

# generate appropriate bitmask
db_bitmask = int(index_yandere+index_nijie+index_drawr+index_danbooru+index_seigaillust+index_anime +
                 index_pixivhistorical+index_pixiv+index_ddbsamples+index_ddbobjects+index_hcg+index_hanime+index_hmags, 2)


def recognizeImage(filePath):
    url = 'http://saucenao.com/search.php?output_type=2&numres=1&minsim=' + \
        minsim+'&dbmask='+str(db_bitmask)+'&api_key='+api_key
    image = open(filePath, 'rb')
    files = {'file': (filePath, image.read())}
    image.close()

    processResults = True
    msg = ''
    ret = ''
    while True:
        r = requests.post(url, files=files)
        if r.status_code != 200:
            print (r.status_code)
            if r.status_code == 403:
                msg = 'Incorrect or Invalid API Key! Please Edit Script to Configure...'
                return msg
            else:
                time.sleep(10)
        else:
            results = json.JSONDecoder(
                object_pairs_hook=OrderedDict).decode(r.text)
            print results
            if int(results['header']['user_id']) > 0:
                # api responded
                # print 'Remaining Searches 30s|24h: ' + \
                    # str(results['header']['short_remaining']) + \
                    # '|'+str(results['header']['long_remaining'])
                if int(results['header']['status']) == 0:
                    # search succeeded for all indexes, results usable
                    msg = 'search succeeded'
                    break
                else:
                    if int(results['header']['status']) > 0:
                        # One or more indexes are having an issue.
                        # This search is considered partially successful, even if all indexes failed, so is still counted against your limit.
                        # The error may be transient, but because we don't want to waste searches, allow time for recovery.
                        #print 'API Error. Retrying in 600 seconds...'
                        time.sleep(600)
                    else:
                        # Problem with search as submitted, bad image, or impossible request.
                        # Issue is unclear, so don't flood requests.
                        # print(
                        msg = 'Bad image or other request error.'
                        processResults = False
                        time.sleep(10)
                        break

    if processResults:
        # print(results)

        if int(results['header']['results_returned']) > 0:
            similarity = float(results['results'][0]['header']['similarity'])
            # one or more results were returned
            if similarity > float(results['header']['minimum_similarity']):
                print('hit! '+str(results['results']
                      [0]['header']['similarity']))

                # get vars to use
                service_name = ''
                illust_id = 0
                member_id = ''
                index_id = results['results'][0]['header']['index_id']
                page_string = ''
                illust_title = ''
                illust_url = ''
                page_match = re.search(
                    '(_p[\d]+)\.', results['results'][0]['header']['thumbnail'])
                if page_match:
                    page_string = page_match.group(1)

                if index_id == 5 or index_id == 6:
                    # 5->pixiv 6->pixiv historical
                    service_name = 'pixiv'
                    illust_id = results['results'][0]['data']['pixiv_id']
                    illust_url = results['results'][0]['data']['ext_urls'][0]
                    illust_title = results['results'][0]['data']['title']
                    member_id = results['results'][0]['data']['member_id']
                    member_name = results['results'][0]['data']['member_name']
                elif index_id == 8:
                    # 8->nico nico seiga
                    service_name = 'seiga'
                    illust_id = results['results'][0]['data']['pixiv_id']
                    illust_url = results['results'][0]['data']['ext_urls'][0]
                    illust_title = results['results'][0]['data']['title']
                    member_id = results['results'][0]['data']['member_id']
                    member_name = results['results'][0]['data']['member_name']
                elif index_id == 10:
                    # 10->drawr
                    service_name = 'drawr'
                    illust_id = results['results'][0]['data']['pixiv_id']
                    illust_url = results['results'][0]['data']['ext_urls'][0]
                    illust_title = results['results'][0]['data']['title']
                    member_id = results['results'][0]['data']['member_id']
                    member_name = results['results'][0]['data']['member_name']
                elif index_id == 11:
                    # 11->nijie
                    service_name = 'nijie'
                    illust_id = results['results'][0]['data']['pixiv_id']
                    illust_url = results['results'][0]['data']['ext_urls'][0]
                    illust_title = results['results'][0]['data']['title']
                    member_id = results['results'][0]['data']['member_id']
                    member_name = results['results'][0]['data']['member_name']
                elif index_id == 34:
                    # 34->deviantart
                    service_name = 'deviantart'
                    illust_id = results['results'][0]['data']['da_id']
                    illust_url = results['results'][0]['data']['ext_urls'][0]
                    illust_title = results['results'][0]['data']['title']
                    member_name = results['results'][0]['data']['author_name']
                else:
                    # unknown
                    print('Unhandled Index! Exiting...')
                    return
                
                ret = (service_name, illust_title, member_name, illust_id, illust_url, similarity)
    return (msg, ret)


if __name__ == '__main__':
    msg, ret = recognizeImage('test1.jpg')
    retContent = '图源:{0}\n作品标题:{1}\n作者:{2}\n作品编号:{3}\n链接:{4}\n相似度:{5}'.format(ret[0], ret[1], ret[2], ret[3], ret[4], ret[5]) 
    print msg + '\n' + retContent
