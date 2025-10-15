# Copyright (c) 2018-2019 David Steele <dsteele@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
# License-Filename: LICENSE

import pathlib
import urllib

import pytest
from mock import Mock

from web import comitupweb

ssid_list = [
    "simple",
    "simple+",
    "simplé",
    "simple 2",
    "simplE",
]


@pytest.fixture(params=ssid_list)
def ssid(request):
    return request.param


@pytest.fixture
def app(monkeypatch):
    templatedir = pathlib.Path(__file__).parent.parent / "web/templates"
    monkeypatch.setattr("web.comitupweb.TEMPLATE_PATH", str(templatedir))

    app = comitupweb.create_app(Mock())
    app.debug = True
    app.testing = True
    return app


def test_webapp_null(app, ssid):
    assert "simpl" in ssid


def test_webapp_index(app, ssid, monkeypatch):
    comitupweb.ttl_cache.clear()

    point = {
        "ssid": ssid,
    }
    client_mock = Mock()
    client_mock.ciu_points.return_value = [point]
    monkeypatch.setattr("web.comitupweb.ciu_client", client_mock)
    # comitupweb.ciu_client = client_mock

    response = app.test_client().get("/")
    index_text = response.get_data().decode()

    assert ssid + "</button>" in index_text
    assert "ssid=" + urllib.parse.quote(ssid) in index_text


def test_webapp_connect(app, ssid, monkeypatch):
    monkeypatch.setattr("web.comitupweb.Process", Mock())

    data = {
        "ssid": urllib.parse.quote(ssid),
        "password": urllib.parse.quote("password"),
    }
    response = app.test_client().post("connect", data=data)
    index_text = response.get_data().decode()

    assert "to " + ssid in index_text


@pytest.mark.parametrize("canblink", [True, False])
@pytest.mark.parametrize("path", ["/confirm"])
def test_webapp_blink_confirm(app, canblink, monkeypatch, path):
    monkeypatch.setattr("web.comitupweb.ciu.can_blink", lambda: canblink)
    monkeypatch.setattr("web.comitupweb.ciu.blink", Mock())
    monkeypatch.setattr("comitup.blink.set_trigger", Mock())
    monkeypatch.setattr("web.comitupweb.ciu_client", Mock())
    monkeypatch.setattr(
        "web.comitupweb.ciu_client.ciu_info",
        Mock(return_value={"imode": "single"})
    )
    monkeypatch.setattr(
        "web.comitupweb.ciu_client.ciu_points", Mock(return_value=[])
    )

    response = app.test_client().get(path)
    blinktext = response.get_data().decode()

    assert canblink == ("Locate" in blinktext)


def test_webapp_blink(app, monkeypatch):
    monkeypatch.setattr("comitup.blink.set_trigger", Mock())
    monkeypatch.setattr("web.comitupweb.ciu.blink", Mock())
    response = app.test_client().get("/blink")

    assert response.status_code == 200


def test_connectivity_android_generate_204(app):
    """Test Android connectivity check endpoint /generate_204"""
    response = app.test_client().get("/generate_204")
    assert response.status_code == 204
    assert response.get_data() == b""


def test_connectivity_android_gen_204(app):
    """Test Android connectivity check endpoint /gen_204"""
    response = app.test_client().get("/gen_204")
    assert response.status_code == 204
    assert response.get_data() == b""


def test_connectivity_ios(app):
    """Test iOS/macOS connectivity check endpoint /hotspot-detect.html"""
    response = app.test_client().get("/hotspot-detect.html")
    assert response.status_code == 200
    assert b"Success" in response.get_data()


def test_connectivity_windows(app):
    """Test Windows connectivity check endpoint /connecttest.txt"""
    response = app.test_client().get("/connecttest.txt")
    assert response.status_code == 200
    assert response.get_data() == b"Microsoft Connect Test"


def test_connectivity_windows_ncsi(app):
    """Test Windows NCSI connectivity check endpoint /ncsi.txt"""
    response = app.test_client().get("/ncsi.txt")
    assert response.status_code == 200
    assert response.get_data() == b"Microsoft NCSI"


def test_connectivity_firefox(app):
    """Test Firefox connectivity check endpoint /success.txt"""
    response = app.test_client().get("/success.txt")
    assert response.status_code == 200
    assert response.get_data() == b"success\n"


def test_connectivity_ubuntu(app):
    """Test Ubuntu/GNOME connectivity check endpoint /connectivity-check"""
    response = app.test_client().get("/connectivity-check")
    assert response.status_code == 204
    assert response.get_data() == b""


def test_connectivity_ubuntu_html(app):
    """Test Ubuntu/GNOME connectivity check /connectivity-check.html"""
    response = app.test_client().get("/connectivity-check.html")
    assert response.status_code == 204
    assert response.get_data() == b""
