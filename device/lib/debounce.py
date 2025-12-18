""" module to debounce keys/buttons """
import time
from machine import Pin, Timer

class button:
    """ class to debounce buttons """
    def __init__(self, pin, led, label="", fnc=None):
        self.pin=pin
        self.button=Pin(self.pin, Pin.IN, Pin.PULL_UP)
        self.led=Pin(led, Pin.OUT)
        self.tim=Timer(-1)
        self.window=20
        self.label=label
        self.fnc=fnc
        self.button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self.callback)

    def tcb(self, t):
        """ tobble button with callback """
        v=self.button.value()
        if self.label != "":
            self.led.value(1-v)
        if not self.fnc is None:
            self.fnc(self.label, v)

    # Interrupt callback function
    def callback(self, pin):
        self.tim.init(period=self.window, mode=Timer.ONE_SHOT, callback=self.tcb)

if __name__ == "__main__":
    # Attach interrupt to button
    a=button(14, 12, label="A", fnc=test)
    b=button(15, 13, label="B")

    # Main loop
    while True:
        time.sleep(0.01)  # Small delay to avoid busy-waiting
