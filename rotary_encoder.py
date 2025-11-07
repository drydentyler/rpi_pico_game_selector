from machine import Pin


class RotaryEncoder:
    def __init__(self, clk: int, dt: int, sw: int):
        """
        A rotary encoder is also a quadrature encoder meaning that the two waves of CLK and DT are offset by 90 degrees,
        this simply means that they are out of sync with each other by a quarter of a cycle, the change in the degrees
        value would change how out of sync they are.

        180 degree offset would mean that when one is at its highest the other is at its lowest, but 90 degrees would
        mean that at ones highest, the other is at the midpoint between its lowest and highest. However, since there are
        pull downs in place, and we are only concerned with high and low peak values, it would look like one at the
        highest while the other is already at a high or low, there are no midpoints.

                 _____      _____      _____      _____      _____      _____     _____
                |     |    |     |    |     |    |     |    |     |    |     |    |
        CLK ____|     |____|     |____|     |____|     |____|     |____|     |____|
           __      _____      _____      _____      _____      _____      _____     _____
             |    |     |    |     |    |     |    |     |    |     |    |     |    |
        DT   |____|     |____|     |____|     |____|     |____|     |____|     |____|

        Reading the CLK line from left to right, when the CLK signal goes high, the DT is at a low point, indicating
        moving clock wise. Conversely, reading CLK right to left will show CLK as High or Low when DT is already in that
        same state, indicating moving counter-clockwise.
        """
        # Set up CLK pin with given pin and take initial reading
        self.clk_pin = Pin(clk, Pin.IN, Pin.PULL_DOWN)
        self.prev_clk_state = self.clk_pin.value()

        # Set up DT pin with given pin and take initial reading
        self.dt_pin = Pin(dt, Pin.IN, Pin.PULL_DOWN)
        self.prev_dt_state = self.dt_pin.value()

        # Set up SW (button) with given pin
        self.sw_pin = Pin(sw, Pin.IN, Pin.PULL_UP)

        # Set initial and previous quadrature counts to 0
        self.qtr_counter = 0
        self.last_qtr_counter = 0

        # Initial counter is set to 0
        self.counter = 0

        # Set the related button variables to high state and button has not been pressed yet
        self.prev_button_state = 1
        self.button_pressed = False
