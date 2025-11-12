#!/usr/bin/python3
# Copyright (c) 2017-2019 David Steele <dsteele@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
# License-Filename: LICENSE

#
# Copyright 2016-2017 David Steele <steele@debian.org>
# This file is part of comitup
# Available under the terms of the GNU General Public License version 2
# or later
#

import logging
import sys
import time
import urllib
from logging.handlers import TimedRotatingFileHandler
from multiprocessing import Process

from flask import (Flask, abort, jsonify, redirect, render_template, request,
                   send_from_directory)
from cachetools import cached, TTLCache

sys.path.append(".")
sys.path.append("..")

from comitup import client as ciu  # noqa

ciu_client = None
LOG_PATH = "/var/log/comitup-web.log"
TEMPLATE_PATH = "/usr/share/comitup/web/templates"

ttl_cache = TTLCache(maxsize=10, ttl=5)


def deflog():
    log = logging.getLogger("comitup_web")
    log.setLevel(logging.INFO)
    handler = TimedRotatingFileHandler(
        LOG_PATH,
        encoding="utf=8",
        when="D",
        interval=7,
        backupCount=8,
    )
    fmtr = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(fmtr)
    log.addHandler(handler)

    return log


def do_connect(ssid, password, log):
    time.sleep(1)
    log.debug("Calling client connect")
    ciu_client.service = None
    ciu_client.ciu_connect(ssid, password)


@cached(cache=ttl_cache)
def cached_points():
    return ciu_client.ciu_points()


def create_app(log):
    app = Flask(__name__, template_folder=TEMPLATE_PATH)

    @app.after_request
    def add_header(response):
        response.cache_control.max_age = 0
        return response

    @app.route("/")
    def index():
        points = cached_points()
        for point in points:
            point["ssid_encoded"] = urllib.parse.quote(point["ssid"])
        log.info("index.html - {} points".format(len(points)))
        return render_template(
            "index.html", points=points, can_blink=ciu.can_blink()
        )

    @app.route("/confirm")
    def confirm():
        ssid = request.args.get("ssid", "")
        ssid_encoded = urllib.parse.quote(ssid.encode())
        encrypted = request.args.get("encrypted", "unencrypted")

        mode = ciu_client.ciu_info()["imode"]

        log.info("confirm.html - ssid {0}, mode {1}".format(ssid, mode))

        return render_template(
            "confirm.html",
            ssid=ssid,
            encrypted=encrypted,
            ssid_encoded=ssid_encoded,
            mode=mode,
            can_blink=ciu.can_blink(),
        )

    @app.route("/connect", methods=["POST"])
    def connect():
        ssid = urllib.parse.unquote(request.form["ssid"])
        password = request.form["password"].encode()

        cached_points()

        p = Process(target=do_connect, args=(ssid, password, log))
        p.start()

        log.info("connect.html - ssid {0}".format(ssid))
        return render_template(
            "connect.html",
            ssid=ssid,
            password=password,
        )

    @app.route("/blink")
    def blink():
        ciu.blink()

        resp = jsonify(success=True)
        return resp

    @app.route("/img/favicon.ico")
    def favicon():
        log.info("Returning 404 for favicon request")
        abort(404)

    @app.route("/img/<path:path>")
    def send_image(path):
        return send_from_directory(TEMPLATE_PATH + "/images", path)

    @app.route("/js/<path:path>")
    def send_js(path):
        return send_from_directory(TEMPLATE_PATH + "/js", path)

    @app.route("/css/<path:path>")
    def send_css(path):
        return send_from_directory(TEMPLATE_PATH + "/css", path)

    # Connectivity check endpoints for fake internet mode
    # Android connectivity checks - return HTTP 204
    @app.route("/generate_204")
    def generate_204():
        log.info("Android connectivity check: /generate_204")
        return "", 204

    @app.route("/gen_204")
    def gen_204():
        log.info("Android connectivity check: /gen_204")
        return "", 204

    # iOS connectivity checks - return HTTP 200 with specific content
    @app.route("/library/test/success.html")
    def ios_success_html():
        log.info("iOS connectivity check: /library/test/success.html")
        html = "<HTML><HEAD><TITLE>Success</TITLE></HEAD>"
        html += "<BODY>Success</BODY></HTML>"
        return html, 200

    @app.route("/hotspot-detect.html")
    def ios_hotspot_detect():
        log.info("iOS connectivity check: /hotspot-detect.html")
        html = "<HTML><HEAD><TITLE>Success</TITLE></HEAD>"
        html += "<BODY>Success</BODY></HTML>"
        return html, 200

    @app.route("/success.txt")
    def apple_success_txt():
        log.info("Apple connectivity check: /success.txt")
        return "Success", 200

    # Windows connectivity checks
    @app.route("/ncsi.txt")
    def windows_ncsi():
        log.info("Windows connectivity check: /ncsi.txt")
        return "Microsoft NCSI", 200

    @app.route("/connecttest.txt")
    def windows_connecttest():
        log.info("Windows connectivity check: /connecttest.txt")
        return "Microsoft Connect Test", 200

    # Firefox connectivity check
    @app.route("/canonical.html")
    def firefox_canonical():
        log.info("Firefox connectivity check: /canonical.html")
        meta = '<meta http-equiv="refresh" content="0;url=success.txt"/>'
        return meta, 200

    # Samsung/Android manufacturer-specific checks
    @app.route("/generate204")
    def generate204_no_underscore():
        log.info("Samsung connectivity check: /generate204")
        return "", 204

    # Xiaomi connectivity checks
    @app.route("/generate_204_xiaomi")
    def xiaomi_generate_204():
        log.info("Xiaomi connectivity check: /generate_204_xiaomi")
        return "", 204

    # Generic catch-all for other connectivity checks
    @app.route("/check_network_status.txt")
    def check_network_status():
        log.info("Generic connectivity check: /check_network_status.txt")
        return "OK", 200

    @app.route("/<path:path>")
    def catch_all(path):
        return redirect("http://10.41.0.1/", code=302)

    @app.errorhandler(500)
    def internal_error(error):
        sys.exit(1)

    return app


def main():
    log = deflog()
    log.info("Starting comitup-web")

    global ciu_client
    ciu_client = ciu.CiuClient()

    ciu_client.ciu_state()
    ciu_client.ciu_points()

    app = create_app(log)
    app.run(host="0.0.0.0", port=80, debug=False, threaded=True)


if __name__ == "__main__":
    main()
