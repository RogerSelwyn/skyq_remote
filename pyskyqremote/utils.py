"""SKY Q Remote Utilities."""
import json
import logging
import math
import socket
import time
from http import HTTPStatus

import requests
import websocket
import xmltodict

from .const import (
    CONNECT_TIMEOUT,
    HTTP_TIMEOUT,
    REST_BASE_URL,
    SKY_PLAY_URN,
    SKYCONTROL,
    SOAP_ACTION,
    SOAP_CONTROL_BASE_URL,
    SOAP_DESCRIPTION_BASE_URL,
    SOAP_PAYLOAD,
    SOAP_RESPONSE,
    SOAP_TIMEOUT,
    SOAP_USER_AGENT,
    WS_BASE_URL,
)

_LOGGER = logging.getLogger(__name__)


class deviceAccess:
    """Set up the device for access."""

    def __init__(self, host):
        """Initialise the utility setup."""
        self._host = host

    def getSoapControlURL(self, descriptionIndex):
        """Get the sky control url."""
        descriptionUrl = SOAP_DESCRIPTION_BASE_URL.format(self._host, descriptionIndex)
        headers = {"User-Agent": SOAP_USER_AGENT}
        try:
            resp = requests.get(descriptionUrl, headers=headers, timeout=SOAP_TIMEOUT)
            if resp.status_code == HTTPStatus.OK:
                description = xmltodict.parse(resp.text)
                deviceType = description["root"]["device"]["deviceType"]
                if not (SKYCONTROL in deviceType):
                    return {"url": None, "status": "Not Found"}
                services = description["root"]["device"]["serviceList"]["service"]
                if not isinstance(services, list):
                    services = [services]
                playService = None
                for s in services:
                    if s["serviceId"] == SKY_PLAY_URN:
                        playService = s
                if playService is None:
                    return {"url": None, "status": "Not Found"}
                return {
                    "url": SOAP_CONTROL_BASE_URL.format(
                        self._host, playService["controlURL"]
                    ),
                    "status": "OK",
                }
            return {"url": None, "status": "Not Found"}
        except (requests.exceptions.Timeout):
            _LOGGER.warning(
                f"W0020U - Control URL not accessible: {self._host} : {descriptionUrl}"
            )
            return {"url": None, "status": "Error"}
        except (requests.exceptions.ConnectionError) as err:
            _LOGGER.exception(f"X0010U - Connection error: {self._host} : {err}")
            return {"url": None, "status": "Error"}
        except Exception as err:
            _LOGGER.exception(f"X0020U - Other error occurred: {self._host} : {err}")
            return {"url": None, "status": "Error"}

    def callSkyWebSocket(self, method):
        """Make a websocket call to the sky box."""
        try:
            ws = websocket.create_connection(WS_BASE_URL.format(self._host, method))
            response = json.loads(ws.recv())
            ws.close()
            return response
        except (TimeoutError) as err:
            _LOGGER.warning(
                f"W0030U - Websocket call failed: {self._host} : {method} : {err}"
            )
            return {"url": None, "status": "Error"}
        except Exception as err:
            _LOGGER.exception(f"X0030U - Error occurred: {self._host} : {err}")
            return None

    def callSkySOAPService(self, soapControlURL, method):
        """Make a SOAP call to the sky box."""
        try:
            payload = SOAP_PAYLOAD.format(method)
            headers = {
                "Content-Type": 'text/xml; charset="utf-8"',
                "SOAPACTION": SOAP_ACTION.format(method),
            }
            resp = requests.post(
                soapControlURL,
                headers=headers,
                data=payload,
                verify=True,
                timeout=SOAP_TIMEOUT,
            )
            if resp.status_code == HTTPStatus.OK:
                xml = resp.text
                return xmltodict.parse(xml)["s:Envelope"]["s:Body"][
                    SOAP_RESPONSE.format(method)
                ]
            return None
        except requests.exceptions.RequestException:
            return None

    def http_json(self, jsonport, path, headers=None) -> str:
        """Make an HTTP call to the sky box."""
        response = requests.get(
            REST_BASE_URL.format(self._host, jsonport, path),
            timeout=HTTP_TIMEOUT,
            headers=headers,
        )
        return json.loads(response.content)

    def sendCommand(self, port, code):
        """Send a command to the sky box."""
        commandBytes = bytearray(
            [4, 1, 0, 0, 0, 0, int(math.floor(224 + (code / 16))), code % 16]
        )

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as err:
            _LOGGER.exception(
                f"X0040U - Failed to create socket when sending command: {self._host} : {err}"
            )
            return

        try:
            client.connect((self._host, port))
        except Exception as err:
            _LOGGER.exception(
                f"X0050U - Failed to connect to client when sending command: {self._host} : {err}"
            )
            return

        strlen = 12
        timeout = time.time() + CONNECT_TIMEOUT

        while 1:
            data = client.recv(1024)
            data = data

            if len(data) < 24:
                client.sendall(data[0:strlen])
                strlen = 1
            else:
                client.sendall(commandBytes)
                commandBytes[1] = 0
                client.sendall(commandBytes)
                client.close()
                break

            if time.time() > timeout:
                _LOGGER.error(
                    f"E0030U - Timeout error sending command: {self._host} : {str(code)}"
                )
                break
