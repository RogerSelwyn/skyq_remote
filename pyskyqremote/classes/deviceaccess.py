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

from ..const import (
    COMMANDS,
    CONNECT_TIMEOUT,
    HTTP_TIMEOUT,
    REST_BASE_URL,
    REST_DELETE,
    REST_GET,
    REST_POST,
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
UNDEFINED = "undefined"


class DeviceAccess:
    """Set up the device for access."""

    def __init__(self, host, jsonPort, port):
        """Initialise the utility setup."""
        self._host = host
        self._jsonPort = jsonPort
        self._port = port
        # _LOGGER.debug(f"Init device access - {self._host}")
        self._soapControlURL = UNDEFINED

    def retrieveInformation(self, rest_path, call_type=REST_GET):
        """Retrieve information from the SkyQ box."""
        try:
            if call_type == REST_GET:
                return self.http_json(rest_path)
            if call_type == REST_POST:
                return self.http_json_post(rest_path)
            if call_type == REST_DELETE:
                return self.http_json_delete(rest_path)
        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
        ):  # as err:
            # _LOGGER.debug(f"D0010U - Connection error: {self._host} : {err}")
            return None
        # except Exception as err:
        #     _LOGGER.exception(f"X0010DA - Error occurred: {self._host} : {err}")
        #     return None

    def callSkyWebSocket(self, method):
        """Make a websocket call to the sky box."""
        _LOGGER.debug(f"WS Call - {self._host} - {method}")
        try:
            ws = websocket.create_connection(WS_BASE_URL.format(self._host, method))
            response = json.loads(ws.recv())
            ws.close()
            return response
        except (TimeoutError) as err:
            _LOGGER.warning(f"W0010DA - Websocket call failed: {self._host} : {method} : {err}")
            return {"url": None, "status": "Error"}
        except Exception as err:
            _LOGGER.exception(f"X0020DA - Error occurred: {self._host} : {err} : {method}")
            return None

    def callSkySOAPService(self, method):
        """Make a SOAP call to the sky box."""
        if self._soapControlURL == UNDEFINED:
            self._soapControlURL = self._getSoapControlURL()
        if not self._soapControlURL:
            _LOGGER.warning(f"W0020DA - SOAP Control URL not found: {self._host} : {method}")
            return None
        _LOGGER.debug(f"SOAP Call - {self._host} - {method}")
        try:
            payload = SOAP_PAYLOAD.format(method)
            headers = {
                "Content-Type": 'text/xml; charset="utf-8"',
                "SOAPACTION": SOAP_ACTION.format(method),
            }
            resp = requests.post(
                self._soapControlURL,
                headers=headers,
                data=payload,
                verify=True,
                timeout=SOAP_TIMEOUT,
            )
            if resp.status_code == HTTPStatus.OK:
                xml = resp.text
                return xmltodict.parse(xml)["s:Envelope"]["s:Body"][SOAP_RESPONSE.format(method)]
            return None
        except requests.exceptions.RequestException:
            return None

    def http_json(self, path, headers=None) -> str:
        """Make an HTTP get call to the sky box."""
        _LOGGER.debug(f"HTTP Get Call - {self._host} - {path}")
        response = requests.get(
            REST_BASE_URL.format(self._host, self._jsonPort, path),
            timeout=HTTP_TIMEOUT,
            headers=headers,
        )
        return response.json()

    def http_json_post(self, path, headers=None) -> str:
        """Make an HTTP post call to the sky box."""
        _LOGGER.debug(f"HTTP Post Call - {self._host} - {path}")
        response = requests.post(
            REST_BASE_URL.format(self._host, self._jsonPort, path),
            timeout=HTTP_TIMEOUT,
            headers=headers,
        )
        return response.status_code

    def http_json_delete(self, path, headers=None) -> str:
        """Make an HTTP delete call to the sky box."""
        _LOGGER.debug(f"HTTP Delete Call - {self._host} - {path}")
        response = requests.delete(
            REST_BASE_URL.format(self._host, self._jsonPort, path),
            timeout=HTTP_TIMEOUT,
            headers=headers,
        )
        return response.status_code

    def sendCommand(self, port, code):
        """Send a command to the sky box."""
        commandBytes = bytearray([4, 1, 0, 0, 0, 0, int(math.floor(224 + (code / 16))), code % 16])

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as err:
            _LOGGER.exception(f"X0030DA - Failed to create socket when sending command: {self._host} : {err}")
            return

        try:
            client.connect((self._host, port))
        except Exception as err:
            _LOGGER.exception(f"X0040DA - Failed to connect to client when sending command: {self._host} : {err}")
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
                _LOGGER.error(f"E0010DA - Timeout error sending command: {self._host} : {code}")
                break

    def press(self, sequence):
        """Issue the specified sequence of commands to SkyQ box."""
        if isinstance(sequence, list):
            for item in sequence:
                if item.casefold() not in COMMANDS:
                    _LOGGER.error(f"E0020DA - Invalid command: {self._host} : {item}")
                    break
                self.sendCommand(self._port, COMMANDS[item.casefold()])
                time.sleep(0.5)
        elif sequence not in COMMANDS:
            _LOGGER.error(f"E0030DA - Invalid command: {self._host} : {sequence}")
        else:
            self.sendCommand(self._port, COMMANDS[sequence.casefold()])

    def _findPlayService(self, description):
        services = description["root"]["device"]["serviceList"]["service"]
        if not isinstance(services, list):
            services = [services]
        playService = None
        for s in services:
            if s["serviceId"] == SKY_PLAY_URN:
                playService = s

        return playService

    def _getSoapControlURL(self):
        """Get the soapcontrourl for the SkyQ box."""
        url_index = 0
        soapControlURL = None
        while soapControlURL is None and url_index < 50:
            soapControlURL = self._getSoapControlURLItem(url_index)["url"]
            url_index += 1

        return soapControlURL

    def _getSoapControlURLItem(self, descriptionIndex):
        """Get the sky control url."""
        _LOGGER.debug(f"SoapControlURL - {self._host} - {descriptionIndex}")
        descriptionUrl = SOAP_DESCRIPTION_BASE_URL.format(self._host, descriptionIndex)
        headers = {"User-Agent": SOAP_USER_AGENT}
        empty_return = {"url": None, "status": "Not Found"}
        try:
            resp = requests.get(descriptionUrl, headers=headers, timeout=SOAP_TIMEOUT)
            if resp.status_code == HTTPStatus.OK:
                description = xmltodict.parse(resp.text)
                deviceType = description["root"]["device"]["deviceType"]
                if SKYCONTROL not in deviceType:
                    return empty_return

                playService = self._findPlayService(description)

                if playService is None:
                    return empty_return

                return {
                    "url": SOAP_CONTROL_BASE_URL.format(self._host, playService["controlURL"]),
                    "status": "OK",
                }
            return empty_return
        except (requests.exceptions.Timeout):
            _LOGGER.warning(f"W0030DA - Control URL not accessible: {self._host} : {descriptionUrl}")
            return {"url": None, "status": "Error"}
        except (requests.exceptions.ConnectionError) as err:
            _LOGGER.exception(f"X0050DA - Connection error: {self._host} : {err}")
            return empty_return
        except Exception as err:
            _LOGGER.exception(f"X0060DA - Other error occurred: {self._host} : {err}")
            return empty_return
