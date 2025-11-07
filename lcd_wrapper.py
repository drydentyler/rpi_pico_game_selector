from machine import I2C, Pin
from pico_i2c_lcd import I2cLcd


class LCDWrapper:
    def __init__(self):
        # Set the I2C Address hex value
        I2C_ADDR = 0x27

        # Number of Rows and Columns on LCD display
        I2C_NUM_ROWS = 2
        I2C_NUM_COLS = 16

        # Check Pico pinout, there are groupings of SDA and SCL, first param is the grouping
        self.i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)
        self.lcd = I2cLcd(self.i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

    def clear(self):
        """
        Wrapper function to clear the LCD
        """
        self.lcd.clear()

    def display_duration(self, counter: int = 0):
        """
        Clear LCD and replace with the Duration Display

        Args:
            counter: int, initial value to set with duration display
        """
        # Clear display
        self.clear()

        # Move to top left corner and write duration message
        self.lcd.move_to(0, 0)
        self.lcd.putstr(f'Duration (mins):')
        # self._write_centered(counter, 1)
        self.lcd.move_to((16 - len(str(counter))) // 2, 1)
        self.lcd.putstr(f'{counter}  ')

    def update_duration(self, counter: int):
        """
        Update the duration display with the new duration value

        Args:
            counter: int, new duration value to display
        """
        # TODO: there is no _write_centered function, needs to be created or removed
        counter_str = f'{" " if len(str(counter)) == 2 else ""}{counter}'
        self._write_centered(counter_str, 1)
        self.lcd.move_to((16 - len(counter_str)) // 2, 1)
        self.lcd.putstr(counter_str)

    def display_game(self, game):
        """
        Given a game object, update LCD with the name of the game

        Args:
             game: Game, provided game object that will be displayed on LCD
        """
        self.clear()
        if game:
            name = game.name
            # If the length of the game name is larger than 16, display name wrapped to next line
            if len(name) > 16:
                self.lcd.putstr(name)
            # Else, center the name on the top line
            else:
                self.lcd.move_to((16 - len(name)) // 2, 0)
                self.lcd.putstr(name)
        # If the provided game is None, display no game found message centered on top line
        else:
            message = 'No game found.'
            self.lcd.move_to((16 - len(message)) // 2, 0)
            self.lcd.putstr(message)

    def display_ip(self, ip: str):
        """
        Present the IP address where the webserver is hosted on the LCD

        Args:
            ip: str, the string value of the IP address of the webserver
        """
        self.clear()
        # Center the IP address on the top line
        self.lcd.move_to((16 - len(ip)) // 2, 0)
        self.lcd.putstr(ip)
