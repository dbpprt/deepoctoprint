# coding=utf-8
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import base64
import logging
import os
import random
import string
import sys
import threading
import time
import urllib
import uuid
from builtins import int

import requests

import octoprint.plugin
from octoprint.events import Events

from .webcam_capture import capture_jpeg

try:
    from future_builtins import ascii, filter, hex, map, oct, zip
except:
    pass

if sys.version_info.major > 2:
    import urllib.request

    urlrequest = urllib.request.urlretrieve
    xrange = range
else:
    urlrequest = urllib.urlretrieve


class DeepOctoPrintDataCollector(octoprint.plugin.SettingsPlugin,
                                 octoprint.plugin.StartupPlugin,
                                 octoprint.plugin.AssetPlugin,
                                 octoprint.plugin.EventHandlerPlugin,
                                 octoprint.plugin.TemplatePlugin,
                                 octoprint.plugin.WizardPlugin):

    def __init__(self):
        self.last_status_update_ts = 0
        self._mutex = threading.RLock()
        self.current_print_ts = -1    # timestamp as print_ts coming from octoprint
        self.print_id = None

    def is_wizard_required(self):
        return True

    def get_wizard_version(self):
        return 1

    def get_settings_defaults(self):
        return dict(
            enabled=True,
            endpoint_prefix='http://localhost:8776',
            installation_key=None,
            interval=60
        )

    def get_template_configs(self):
        return [
            dict(type='settings', custom_bindings=True,
                 template='settings.jinja2'),
            dict(type='wizard', custom_bindings=True, template='settings.jinja2')
        ]

    # def get_update_information(self):
    #     TODO: implement updater!
    #     )

    def get_assets(self):
        return dict(
            js=["js/settings.js"]
        )

    @property
    def enabled(self):
        return self._settings.get_boolean(['enabled'])

    def on_event(self, event, payload):

        if event == 'PrintFailed' or event == 'PrintDone':
            self.capture(event=event)

        with self._mutex:
            if event == 'PrintStarted':
                self.current_print_ts = int(time.time())
                self.print_id = uuid.uuid4().hex

        with self._mutex:
            if event == 'PrintFailed' or event == 'PrintDone':
                self.current_print_ts = -1
                self.print_id = None

    def on_after_startup(self):
        main_thread = threading.Thread(target=self.main_loop)
        main_thread.daemon = True
        main_thread.start()

        if self._settings.get(['installation_key']) is None:
            self._settings.set(["installation_key"],
                               uuid.uuid4().hex, force=True)
            self._settings.save(force=True)

    def get_print_info(self):
        with self._mutex:
            return self.print_id, self.current_print_ts

    def capture(self, event='Printing'):
        #try:
        if not self.enabled:
            return

        endpoint = self._settings.get(['endpoint_prefix']) + '/v1/upload'

        print_id, current_print_ts = self.get_print_info()
        installation_key = self._settings.get(['installation_key'])

        # TODO: might be required to rotate the image correctly
        # webcam = dict((k, self._settings.effective['webcam'][k]) for k in (
        #     'flipV', 'flipH', 'rotate90', 'streamRatio')),

        frame = capture_jpeg(self._settings.global_get(["webcam"]))

        headers = {'user-agent': f'collector/{self._plugin_version}', 'x-installation-key': installation_key,
                    'x-print-id': print_id, 'x-start-time': f'{current_print_ts}', 'x-time': f'{int(time.time())}', 'x-current-event': event}

        files = {'pic': frame}
        resp = requests.post(endpoint, files=files, headers=headers)
        resp.raise_for_status()

        #except:
        #    return

    def main_loop(self):
        while True:
            if not self._printer.get_state_id() in ['PRINTING', ]:
                time.sleep(5)
                continue

            self.capture()
            time.sleep(self._settings.get(['interval']))


__plugin_name__ = "DeepOctoPrint - Data Collector"
__plugin_pythoncompat__ = ">=2.7,<4"

__plugin_implementation__ = DeepOctoPrintDataCollector()

# __plugin_hooks__ = {
#     "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
# }
