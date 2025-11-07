import network
import rp2
import sys
import socket

from network_settings import NetworkSettings
from picozero import pico_led
from time import sleep


class Webserver:
    status_codes: {int: str} = {
        201: "Successfully Created",
        400: "Error: Bad Request",
        404: "Error: Not Found",
        409: "Error: Conflict"
    }

    def __init__(self):
        # The __init__ will run before the __enter__ so set ip and connection to None, they will be updated in __enter__
        self.ip: str = None
        self.connection = None

        # Get the html store in the text file as a variable to easily be served on request
        self.html = open('index_html.txt').read()

        # TODO: There is no such thing as 'status_alert_html.txt' this will need to be created
        self.status_alert = open('status_alert_html.txt').read()

    def connect(self) -> str:
        """
        Connect to the Wi-Fi network and return the IP address of the Pico on the network
        """
        # STA_IF stands for station interface and is what will allow the Pico to become part of the Wi-Fi network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)

        # Connect to the Wi-Fi using the class variables assigned in the Network Settings file
        wlan.connect(NetworkSettings.ssid, NetworkSettings.password)

        # While attempting to connect,
        while not wlan.isconnected():
            # The bootsel button is used to enter a bootloader mode to flash new firmware, if pressed => exit
            if rp2.bootsel_button() == 1:
                sys.exit()

            # Print waiting for connection and flash led while attempting to connect
            print('Waiting for connection . . .')
            pico_led.on()
            sleep(0.5)
            pico_led.off()
            sleep(0.5)

        # Get IP address and return
        ip = wlan.ifconfig()[0]
        print(f'Connected on {ip}')
        pico_led.on()

        return ip

    def open_socket(self, ip: str):
        """
        Open a socket for communication between devices on the network as clients and the Pico as server

        Args:
            ip: str, the IP address of the Pico taken from the connect function
        """
        address = (ip, 80)

        # If connection is None from the init function, begin creating the socket
        if self.connection is None:
            self.connection = socket.socket()

        # Try to bind the address and begin listening, but if an error occurs, close the connection
        try:
            self.connection.bind(address)
            self.connection.listen(1)
        except OSError as e:
            self.connection.close()
            print('Had to close connection')

    def create_status_alert(self, status_code: int) -> str:
        """
        Given a status code, create the correct alert to be displayed to the user

        Args:
            status_code: int, integer value of the status code will be compared with class dictionary

        Returns:
            str, the div HTML for the alert that will be displayed
        """
        if status_code:
            # Ensure status code is in 200s or 400s
            if 200 <= status_code <= 299 or 400 <= status_code <= 499:
                # Assign 'success' if in 200s or 'danger' if in 400s
                html = self.status_alert.replace('%STATUS%', 'success' if status_code <= 299 else 'danger')
                # Replace message with the appropriate code meaning from dictionary
                html.replace('%MESSAGE%', Webserver.status_codes[status_code])
            else:
                # If status code is outside 200s or 400s, it hasn't been implemented yet, don't display an alert
                html = ""
        else:
            html = ""
        return html

    def serve(self, connection, prev_status: int | None = None):
        """
        Serve the relevant HTML upon request from a client

        Args:
             connection: the connection created to the network and opened socket that is listening for requests
             prev_status: int | None, integer value of a success/failure/error/etc message to be displayed
        """
        try:
            print(f'status received: {prev_status}')

            # Get 1024 bytes of request from client
            client = connection.accept()[0]
            request = str(client.recv(1024))

            try:
                # Split the request if possible to the relevant information
                request = request.split()[1]
            except IndexError:
                pass

            # TODO: this will be need to be removed eventually
            print(request)

            page = self.html.replace('%STATUS_MESSAGE%', self.create_status_alert(prev_status))

            # Send the client the html and close request
            client.send(page)
            client.close()

            # If game is in request, get the params from the request body
            if request.find('/game/') != -1:
                # %20 is the coding for a space so replace any with ' '
                game_inputs = request[request.index('/game/') + len('/game/'):].replace('%20', ' ')
                # Split the remaining request string by '/' and cast into a tuple
                params = tuple(game_inputs.split('/'))

                # TODO: This is where the DB will need to be called to insert the given game params
                return params
        except Exception as e:
            print(f'An exception occurred while serving client: {e}')

    def __enter__(self):
        # Context manager override, set up the connection and IP attributes of the class
        self.ip = self.connect()
        self.open_socket(self.ip)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Context manager override, always close connection on exiting context manager and print any exceptions
        self.connection.close()
        if exc_type:
            print(f'A {exc_type} exception forced the webserver to close: {exc_val}')


