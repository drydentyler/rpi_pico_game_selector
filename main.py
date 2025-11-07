from game import Game
from lcd_wrapper import LCDWrapper
from machine import Pin
# TODO: rename rotary encoder file
# TODO: rotary_encoder_new_class doesn't even match any of the rotary encoder files
from rotary_encoder_new_class import RotaryEncoder
# TODO: rename webserver class
# TODO: webserver_new_class also doesn't match any available files
from webserver_new_class import Webserver
from games_db_wrapper import DBWrapper


def encoder_handler(pin):
    """
    Handler function for Rising and Falling changes in Rotary Encoder

    Args:
        Pin, unused but required
    """
    # Will need to access the LCD, Rotary Encoder and displaying_ip bool
    global lcd, re, displaying_ip

    # Read the current states of the CLK and DT pins
    clk_state = re.clk_pin.value()
    dt_state = re.dt_pin.value()

    # TODO: the button handler func sets the interrupts handlers to None to prevent overlapping interrupts but this func
    # TODO: doesn't have it, should it? is it necessary?

    # TODO: I don't love the variable name displaying_ip because it could display anything other than duration
    # The IP and Game result are not being displayed, check the encoder values and update LCD
    if not displaying_ip and not re.button_pressed:
        if clk_state == re.prev_clk_state and dt_state == re.prev_dt_state:
            # This is an error, if this handler was called but the states didn't change
            pass
        elif (clk_state == 1 and re.prev_dt_state == 0) or (clk_state == 0 and re.prev_dt_state == 1):
            # If the CLK and DT values are offset, the dial is moving Clockwise, increment values
            # The counter value is going to be 4x the quadrature counter, set to the max (180*4)-1
            if re.counter < 719:
                # Increment counter by 1
                re.counter += 1
                # Recalculate the quadrature counter by dividing counter by 4
                re.qtr_counter = round(re.counter / 4)
        elif (clk_state == 1 and re.prev_dt_state == 1) or (clk_state == 0 and re.prev_dt_state == 0):
            # If CLK and DT are the same value, moving Counter-clockwise, decrement value
            if re.counter > 0:
                re.counter -= 1
                re.qtr_counter = round(re.counter / 4)

        # Set the previous CLK and DT values to the last readings
        re.prev_clk_state = clk_state
        re.prev_dt_state = dt_state

        # If the last quadrature counter doesn't match the current value, update previous value and update LCD
        if re.qtr_counter != re.last_qtr_counter:
            re.last_qtr_counter = re.qtr_counter
            lcd.update_duration(re.qtr_counter)


def button_handler(pin):
    """
    Handler function for the rotary encoder button

    Args:
        Pin: unused but required
    """
    # TODO: maybe make pressing the button cycle through the duration/ip/game name, that way you can always return to see the ip address for the webserver

    # Will need access to the LCD, Rotary Encoder, Database, and displaying_ip bool
    global lcd, displaying_ip, re, db

    # Temporarily set the button handler function to None to prevent conflicting function calls
    re.sw_pin.irq(handler=None)

    # If button current state is High and previous state was low
    if re.sw_pin.value() == 1 and re.prev_button_state == 0:
        # TODO: functionally these top two conditions are the same, condense them somehow
        # If the IP is currently displayed, replace with the duration display
        if displaying_ip:
            lcd.display_duration(re.qtr_counter)
            displaying_ip = False
        else:
            # Else a game result is displayed, replace with the duration display
            if re.button_pressed:
                lcd.display_duration(re.qtr_counter)
                re.button_pressed = False
            else:
                # Otherwise, get the additional parameter readings to query the database
                # Check the complexity toggle state, High->True, Low->False
                # is_complex = complexity_toggle.value()
                # TODO: need to incorporate the objects for the players rotary switch and complexity toggle
                # TODO: Replace the complexity parameter with the reading from the toggle and players rotary switch
                game = db.get_random_game(players=2, duration=re.qtr_counter, complexity=False)

                # Display the game selected from the database
                lcd.display_game(game)

                # Set the previous button state and displaying result to True(1)
                re.prev_button_state = 1
                re.button_pressed = True
    elif re.sw_pin.value() == 0 and re.prev_button_state == 1:
        re.prev_button_state = 0

    # Reset the button handler function to accept calls again
    re.sw_pin.irq(handler=button_handler)


# Create the LCD Wrapper class
lcd = LCDWrapper()

# Create the Rotary Encoder Class, passing in the necessary pins
re = RotaryEncoder(clk=8, dt=7, sw=6)

# TODO: rename this db file to something else, remove 'testing'
# Create the Database wrapper, passing in a name for the database
db = DBWrapper(db_name='testing_games_db.txt')

# Set interrupt request parameters for the CLK, DT and SW pins
re.clk_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_handler)

re.dt_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_handler)

re.sw_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=button_handler)

# Create the Webserver context manager
with Webserver() as ws:
    # Display the IP address on the LCD
    lcd.display_ip(ws.ip)
    displaying_ip = True

    while True:
        # Serve client requests from the webserver
        ws.serve(ws.connection)
