from game import Game
from lcd_wrapper import LCDWrapper
from machine import Pin
from rotary_encoder import RotaryEncoder
from webserver import Webserver
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

def get_players() -> int:
    """
    Read the output values from the 8:3 priority encoder and convert to decimal value
    
    Returns:
        int: decimal value of number of players
    """
    global priority_encoder_a0, priority_encoder_a1, priority_encoder_a2
    
    curr_a0 = priority_encoder_a0.value()
    curr_a1 = priority_encoder_a1.value()
    curr_a2 = priority_encoder_a2.value()
    
    return (curr_a2*4)+(curr_a1*2)+curr_a0+1

def get_random_game_wrapper(qtr_counter: int):
    """
    Wrapper function to the database call to get the randomly selected game
    """
    global db
    print(qtr_counter)
    return db.get_random_game(players=get_players(), duration=qtr_counter, complexity=False)

def set_display():
    """
    Cycle through displaying the webserver IP address, desired duration and randomly selected game on the LCD screen
    """
    global displays, display_index
    
    # Unpack the function and argumentsfrom the displays list and call the function, passing in the arguments
    func, params = displays[display_index]
    func(params)
    
    # If the display index is 2, the end of the displays list, reset it to 0
    if display_index == 2:
        display_index = 0
    # Otherwise, increment by 1
    else:
        display_index += 1
    
    print(display_index)

def button_handler(pin):
    """
    Handler function for the rotary encoder button

    Args:
        Pin: unused but required
    """
    # Will need access to the LCD, Rotary Encoder, Database, and displaying_ip bool
    global re, display_index, displays

    # Temporarily set the button handler function to None to prevent conflicting function calls
    re.sw_pin.irq(handler=None)

    # If button current state is High and previous state was low
    if re.sw_pin.value() == 1 and re.prev_button_state == 0:
        
        if display_index == 2:
            displays[display_index][1] = get_random_game_wrapper(re.qtr_counter)
        
        set_display()
        re.prev_button_state = 1
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

priority_encoder_a0 = Pin(10, Pin.IN)
priority_encoder_a1 = Pin(11, Pin.IN)
priority_encoder_a2 = Pin(12, Pin.IN)

displays = [[lcd.display_ip, None], [lcd.display_duration, re.qtr_counter], [lcd.display_game, None]]
display_index = 0

# Create the Webserver context manager
with Webserver() as ws:
    displays[0][1] = ws.ip
    set_display()
    
    displaying_ip = True
    prev_status = None

    while True:
        try:
            # Serve client requests from the webserver
            new_game_params = ws.serve(ws.connection, prev_status)
            print(f'new game params: {new_game_params}')
            if new_game_params:
                print(f'previous status: {prev_status}')
                prev_status = db.insert_game(Game(None, *new_game_params))
                print(f'new status: {prev_status}')
        except StopIteration:
            pass
