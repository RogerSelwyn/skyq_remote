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

    def __init__(self, host, json_port, port):
        """Initialise the utility setup."""
        self._host = host
        self._json_port = json_port
        self._port = port
        # _LOGGER.debug(f"Init device access - {self._host}")
        self._soap_control_url = UNDEFINED

    def retrieve_information(self, rest_path, call_type=REST_GET):
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

    def call_sky_web_socket(self, method):
        """Make a websocket call to the sky box."""
        _LOGGER.debug("WS Call - %s - %s", self._host, method)
        try:
            websock = websocket.create_connection(
                WS_BASE_URL.format(self._host, method)
            )
            response = json.loads(websock.recv())
            websock.close()
            return response
        except (TimeoutError) as err:
            _LOGGER.warning(
                "W0010DA - Websocket call failed: %s : %s : %s", self._host, method, err
            )
            return {"url": None, "status": "Error"}
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception(
                "X0020DA - Error occurred: %s : %s : %s", self._host, method, err
            )
            return None

    def call_sky_soap_service(self, method):
        """Make a SOAP call to the sky box."""
        if self._soap_control_url == UNDEFINED:
            self._soap_control_url = self._get_soap_control_url()
        if not self._soap_control_url:
            _LOGGER.warning(
                "W0020DA - No Control URL, SOAP call not made: %s : %s ",
                self._host,
                method,
            )
            return None
        _LOGGER.debug("SOAP Call - %s : %s", self._host, method)
        try:
            payload = SOAP_PAYLOAD.format(method)
            headers = {
                "Content-Type": 'text/xml; charset="utf-8"',
                "SOAPACTION": SOAP_ACTION.format(method),
            }
            resp = requests.post(
                self._soap_control_url,
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

    def http_json(self, path, headers=None) -> str:
        """Make an HTTP get call to the sky box."""
        _LOGGER.debug("HTTP Get Call - %s - %s", self._host, path)
        response = requests.get(
            REST_BASE_URL.format(self._host, self._json_port, path),
            timeout=HTTP_TIMEOUT,
            headers=headers,
        )
        return response.json()

    def http_json_post(self, path, headers=None) -> str:
        """Make an HTTP post call to the sky box."""
        _LOGGER.debug("HTTP Post Call - %s - %s", self._host, path)
        response = requests.post(
            REST_BASE_URL.format(self._host, self._json_port, path),
            timeout=HTTP_TIMEOUT,
            headers=headers,
        )
        return response.status_code

    def http_json_delete(self, path, headers=None) -> str:
        """Make an HTTP delete call to the sky box."""
        _LOGGER.debug("HTTP Delete Call - %s - %s", self._host, path)
        response = requests.delete(
            REST_BASE_URL.format(self._host, self._json_port, path),
            timeout=HTTP_TIMEOUT,
            headers=headers,
        )
        return response.status_code

    def send_command(self, port, code):
        """Send a command to the sky box."""
        _LOGGER.debug("Socket Call - %s - %s", self._host, code)
        command_bytes = bytearray(
            [4, 1, 0, 0, 0, 0, int(math.floor(224 + (code / 16))), code % 16]
        )

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as err:
            _LOGGER.exception(
                "X0030DA - Failed to create socket when sending command: %s : %s ",
                self._host,
                err,
            )
            return

        try:
            client.connect((self._host, port))
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception(
                "X0040DA - Failed to connect to client when sending command: %s : %s",
                self._host,
                err,
            )
            return

        strlen = 12
        timeout = time.time() + CONNECT_TIMEOUT

        while 1:
            data = client.recv(1024)

            if len(data) < 24:
                client.sendall(data[:strlen])
                strlen = 1
            else:
                client.sendall(command_bytes)
                command_bytes[1] = 0
                client.sendall(command_bytes)
                client.close()
                break

            if time.time() > timeout:
                _LOGGER.error(
                    "E0010DA - Timeout error sending command: %s : %s", self._host, code
                )
                break

    def press(self, sequence):
        """Issue the specified sequence of commands to SkyQ box."""
        if isinstance(sequence, list):
            for item in sequence:
                if item.casefold() not in COMMANDS:
                    _LOGGER.error(
                        "E0020DA - Invalid command: %s : %s", self._host, item
                    )
                    break
                self.send_command(self._port, COMMANDS[item.casefold()])
                time.sleep(0.5)
        elif sequence not in COMMANDS:
            _LOGGER.error("E0030DA - Invalid command: %s : %s", self._host, sequence)
        else:
            self.send_command(self._port, COMMANDS[sequence.casefold()])

    def _find_play_service(self, description):
        services = description["root"]["device"]["serviceList"]["service"]
        if not isinstance(services, list):
            services = [services]
        play_service = None
        for service in services:
            if service["serviceId"] == SKY_PLAY_URN:
                play_service = service

        return play_service

    def _get_soap_control_url(self):
        """Get the soapcontrourl for the SkyQ box."""
        url_index = 0
        soap_control_url = None
        while soap_control_url is None and url_index < 50:
            soap_control_url = self._get_soap_control_url_item(url_index)["url"]
            url_index += 1

        if not soap_control_url:
            _LOGGER.warning("W0030DA - Soap Control URL not available - %s", self._host)

        return soap_control_url

    def _get_soap_control_url_item(self, description_index):
        """Get the sky control url."""
        # _LOGGER.debug("SoapControlURL - %s - %s", self._host, description_index)
        description_url = SOAP_DESCRIPTION_BASE_URL.format(
            self._host, description_index
        )
        headers = {"User-Agent": SOAP_USER_AGENT}
        empty_return = {"url": None, "status": "Not Found"}
        try:
            resp = requests.get(description_url, headers=headers, timeout=SOAP_TIMEOUT)
            if resp.status_code == HTTPStatus.OK:
                description = xmltodict.parse(resp.text)
                device_type = description["root"]["device"]["deviceType"]
                if SKYCONTROL not in device_type:
                    return empty_return

                play_service = self._find_play_service(description)

                if play_service is None:
                    return empty_return

                return {
                    "url": SOAP_CONTROL_BASE_URL.format(
                        self._host,
                        play_service[  # pylint: disable=unsubscriptable-object
                            "controlURL"
                        ],
                    ),
                    "status": "OK",
                }
            return empty_return
        except requests.exceptions.Timeout:
            _LOGGER.debug(
                "D0020DA - Control URL not accessible: %s : %s",
                self._host,
                description_url,
            )
            return {"url": None, "status": "Error"}
        except (requests.exceptions.ConnectionError) as err:
            _LOGGER.exception("X0050DA - Connection error: %s : %s", self._host, err)
            return empty_return
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception(
                "X0060DA - Other error occurred: %s : %s", self._host, err
            )
            return empty_return
