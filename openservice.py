
# doc https://rivadelgarda.pnrr.comunweb.it/openapi/doc

import requests
import json
import re
import base64
import configparser
import logging
import urllib
import time


log_levels = {'DEBUG': logging.DEBUG, 
              'INFO': logging.INFO,
              'WARNING': logging.WARNING,
              'ERROR': logging.ERROR,
              }


class openService():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('openservice.ini')
        self.auth_token= self.config.get('default','auth_token')
        self.api_url = self.config.get('default','api_url')
        self.debug = self.config.getboolean('default','debug',fallback=True)
        self.log = logging.getLogger(__name__)
        logging.basicConfig()
        self.log.setLevel(log_levels[self.config.get('default','log_level',fallback='DEBUG')])

                
    def prettyPrintRequest(self,req):
        self.log.debug("=================================================")
        
        self.log.debug('{}\n{}\r\n{}\r\n\r\n{}'.format(
            '-----------START-----------',
            req.method + ' ' + req.url,
            '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            req.body,
        ))
        self.log.debug("=================================================")

    def printResponse(self,response):
        self.log.info('Response status code %s' % response.status_code)
        self.log.debug(response.headers)
        self.log.debug(response.encoding)
        self.log.debug(response.text)
        self.log.debug(response.json())                
       
    def doRequest(self,method,url,querystring={},headers={},json={}):

        self.log.info("Waiting 1 sec")
        time.sleep(1)
        
        _querystring = { }
        _querystring = {**_querystring,**querystring}
        _headers = {"Content-Type":"application/json",
                    "Authorization": "Basic %s" % self.auth_token}

        _headers = {**_headers,**headers}

        request = requests.Request(method, url, headers=_headers, params=_querystring,json=json)
        prepared = request.prepare()


        if self.debug:
            self.prettyPrintRequest(prepared)

        s = requests.Session()
        self.log.info('>>> Calling method %s on %s' % (method, url))
        response = s.send(prepared)

        return response


    def read(self,data):
        # data = id
        response = self.doRequest("GET","%s/%s" % (self.apiread,data))

        self.printResponse(response)
        return response        


    def getAllItems(self,api_entry_point,fields_to_extract):

        full_api_url = self.api_url + api_entry_point
        response = os.doRequest("GET",full_api_url)
        json = response.json()

        allitems = []

        lastlap = False

        while(True):
            for item in json['items']:
                newitem = {}
                for field in fields_to_extract:
                    newitem[field]=item[field]
                allitems.append(newitem)

            if lastlap:
                return(allitems)
                break

        
            response = os.doRequest("GET",json['next'])
            json = response.json()

            # when next is none there is no more pagination to follow
            # so there is only a lastlap to do to download last items
            if json['next'] == None:
                lastlap = True
                continue

    

if __name__ == "__main__":
    os = openService()        

    fields = {'id','name','has_service_status','has_online_contact_point','uri'}
    items = os.getAllItems('servizi',fields)
    for item in items:
        string = ""

        string += item['name']
        string += '|' + re.sub('/api/openapi/servizi/.*#','/Servizi/',item['uri'])
        string += '|' + item['has_service_status'][0]
        url_contatto = "https://rivadelgarda.pnrr.comunweb.it/api/openapi/classificazioni/punti-di-contatto/"
        url_contatto += item['has_online_contact_point'][0]['id'].replace(':','\:')
        response = os.doRequest('GET',url_contatto)
        json = response.json()

        string += '|' + json['name']
        print(string)

        
