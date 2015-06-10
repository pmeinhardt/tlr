#!/usr/bin/env python

# Requires requests (https://github.com/kennethreitz/requests):
# pip install requests

# Don't forget to set the name of the directory with the RDF files to push,
# endpoint URL and API token below. TODO: Parse these as command-line arguments

import os
import requests

def push(directory, endpoint, token):
    s = requests.Session()
    s.headers = {
        'Content-Type': 'application/n-triples',
        'Authorization': 'token %s' % token,
    }

    plen = len(directory) + 1 # prefix: base directory + "/"

    for root, subdirs, files in os.walk(directory):
        for fname in files:
            path = os.path.join(root, fname)
            name = os.path.splitext(path[plen:].replace('/', '', 1))[0]
            url = endpoint + '?key=http://dbpedia.org/resource/' + name

            res = s.request('PUT', url, data=open(path))

            if res.status_code != 200:
                print str(res.status_code) + ' ' + name

            # print name

    s.close()

if __name__ == '__main__':
    directory = './3.8'
    endpoint = 'http://localhost:8080/api/pmeinhardt/test'
    token = '...'
    push(directory, endpoint, token)
