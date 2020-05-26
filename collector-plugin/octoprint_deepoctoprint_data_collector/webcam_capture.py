# coding=utf-8
from __future__ import absolute_import

import logging
import os
import re
import time
from contextlib import closing
from datetime import datetime, timedelta

import requests

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

def webcam_full_url(url):
    if not url or not url.strip():
        return None

    full_url = url.strip()
    if not urlparse(full_url).scheme:
        full_url = "http://localhost/" + re.sub(r"^\/", "", full_url)

    return full_url

def capture_jpeg(webcam_settings):
    snapshot_url = webcam_full_url(webcam_settings.get("snapshot", ''))
    if snapshot_url:
        snapshot_timeout = int(webcam_settings.get("snapshotTimeout", '5'))
        snapshot_validate_ssl = bool(webcam_settings.get("snapshotSslValidation", 'False'))

        r = requests.get(snapshot_url, stream=True, timeout=snapshot_timeout, verify=snapshot_validate_ssl )
        r.raise_for_status()
        jpg = r.content
        return jpg

    else:
        stream_url = webcam_full_url(webcam_settings.get("stream", "/webcam/?action=stream"))

        with closing(urlopen(stream_url)) as res:
            chunker = MjpegStreamChunker()

            while True:
                data = res.readline()
                mjpg = chunker.findMjpegChunk(data)
                if mjpg:
                    res.close()
                    mjpeg_headers_index = mjpg.find('\r\n'*2)
                    if mjpeg_headers_index > 0:
                        return mjpg[mjpeg_headers_index+4:]
                    else:
                        raise Exception('Wrong mjpeg data format')


class MjpegStreamChunker:

    def __init__(self):
        self.boundary = None
        self.current_chunk = StringIO()

    # Return: mjpeg chunk if found
    #         None: in the middle of the chunk
    def findMjpegChunk(self, line):
        if not self.boundary:   # The first time endOfChunk should be called with 'boundary' text as input
            self.boundary = line
            self.current_chunk.write(line)
            return None

        if len(line) == len(self.boundary) and line == self.boundary:  # start of next chunk
            return self.current_chunk.getvalue()

        self.current_chunk.write(line)
        return None
