"""
# this program is supposed to run in two threads, one thread for
# continiously reading the accelerometer and gyroscope, the other
# one to read at lower rate the BME280 (temperature, pressure & humidity)
# The csv file will contain all values all the time, but for
# the ones from the BME, only few ones will be updated. A flag
# identifies that new values are available at this datapoint.
"""

# simple example from adafruit, I believe
from time import sleep, ticks_ms
# use multiporcessor
import _thread

# https://leanpub.com/rpitandt/read
import os
import sys
import array
import config
import machine
import sdcard

from micropython import RingIO
from micropython_lsm6dsox import lsm6dsox
from machine import Pin, I2C, SoftI2C
import bme280_float as BME280

PRINT = False
# PRINT = True

# might need this for the odd SDcard
#from micropython import const
#import time
#_CMD_TIMEOUT = const(1000)

cnf=config.config()

# Set the Chip Select (CS) pin high
cs = machine.Pin(17, machine.Pin.OUT)

# Intialize the SD Card
spi = machine.SPI(0,
                  baudrate=1000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(18),
                  mosi=machine.Pin(19),
                  miso=machine.Pin(16))
try:
    sd = sdcard.SDCard(spi, cs)
except:
    sd = None
    
# initialize the accelerometer & gyroscope
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=1000000)

# documentation : https://micropython-lsm6dsox.readthedocs.io/en/stable/examples.html
lsm = lsm6dsox.LSM6DSOX(i2c)
# lsm.acceleration_data_rate = lsm6dsox.RATE_833_HZ # - gives ~ 550-650 Hz in plain python
# lsm.gyro_data_rate = lsm6dsox.RATE_833_HZ

led = Pin(25, Pin.OUT)

# read temperature chip or not (True/False)
readbme=True

# allocate Ring buffer to transfer printout to SDcard write thread
rb = RingIO(32768)  # is 32k

# ring buffer to tranfer bme data back to main thread
rb_bme = RingIO(512)

# threading support is very new, and some global variables can disappear
# suggestion was to use arrays, which apparently don't disappear
### 'filled' and 'run' not used any more
f=array.array('L',(0,0,0,))
filled=0
run=True
f[0]=1
f[1]=1
f[2]=ticks_ms()

def finish(what):
    """ finish either with error (LED blink) or just exit normally """
    led1=Pin(12)
    led2=Pin(13)
    if what == 1:
        # configuration error, all LED flash for 30 seconds
        for _ in range(60):
            led.on()
            led1.on()
            led2.on()
            sleep(0.25)
            led.off()
            led1.off()
            led2.off()
            sleep(0.25)
    elif what == 2:
        # no SD card, quickly flash LEDs just one at a time for 30 seconds
        for _ in range(60):
            led.on()
            sleep(0.16)
            led.off()
            led1.on()
            sleep(0.16)
            led1.off()
            led2.on()
            sleep(0.16)
            led2.off()
    else:
        # default, no error, steady LED
        led.on()
    sys.exit()

def read_bme(tm, cbme):
    """ read out temperature sensor and put into its ring buffer """
    led.toggle()
    t, p, h = cbme.read_compensated_data()
    #s=str(t)
    s="{:.2f}".format(t)
    s+=','
    s+="{:.3f}".format(p)
    s+=','
    s+="{:.3f}".format(h)
    rb_bme.write(s)
    while f[2]<tm:
        f[2]+=f[0]*100

def write_thread():
    """ check, if enough time elapsed, and read out BME, which is much slower """
    """ fill string into 2nd ringbuffer to transfer back to mainthread """
    if readbme:
        i2cs = SoftI2C(sda=Pin(2), scl=Pin(3), freq=400000)
        bme = BME280.BME280(i2c=i2cs)

        now=ticks_ms()
        read_bme(now, bme)

    filename=cnf.next_datafile()
    # close after writing header
    with open(filename, "w") as file:
        # write info about data takin conditions to output
        file.write("# StartCondition: ")
        file.write(str(cnf.startcondition) + "\r\n")
        file.write("# StopCondition : ")
        file.write(str(cnf.stopcondition) + "\r\n")
        file.write("# DataRate(A/T) : " + str(cnf.datarate_a)+ " - " +
                   str(cnf.datarate_t) + "\r\n")
        file.write("# Metadata : " + cnf.metadata + "\r\n")
        file.write("")
        file.write("# time,ax,ay,az,gx,gy,gz,tA,new,t,p,h\r\n")

    # re-open and flush to ensure most data is written to file
    #  in case user turns off power during data taking
    with open(filename, "a") as file:
        # while run:
        while f[1]>0:
            file.write(rb.read())
            # f[0] += 1
            if readbme:
                now=ticks_ms()
                if now-f[2] >= f[0]*100:
                    read_bme(now, bme)
            #sleep(0.01)
            file.flush()
    #if readbme:
        #tim.deinit()
    led.on()
    _thread.exit()

def main():
    """ Mount filesystem on SD card """
    global filled
    global run
    global readbme
    
    if sd is None:
        finish(2)

    vfs = os.VfsFat(sd)
    os.mount(vfs, "/sd")

    cnf.read_config()
    if PRINT:
        print(cnf.datarate_a)
        print(cnf.datarate_t)
    f[0]=int(cnf.datarate_t)

    ws=1
    if cnf.datarate_a == "1":
        lsm.acceleration_data_rate = lsm6dsox.RATE_416_HZ
        lsm.gyro_data_rate = lsm6dsox.RATE_416_HZ
    elif cnf.datarate_a == "2":
        lsm.acceleration_data_rate = lsm6dsox.RATE_208_HZ
        lsm.gyro_data_rate = lsm6dsox.RATE_208_HZ
    elif cnf.datarate_a == "3":
        lsm.acceleration_data_rate = lsm6dsox.RATE_104_HZ
        lsm.gyro_data_rate = lsm6dsox.RATE_104_HZ
    elif cnf.datarate_a == "4":
        lsm.acceleration_data_rate = lsm6dsox.RATE_52_HZ
        lsm.gyro_data_rate = lsm6dsox.RATE_52_HZ
    elif cnf.datarate_a == "5":
        lsm.acceleration_data_rate = lsm6dsox.RATE_26_HZ
        lsm.gyro_data_rate = lsm6dsox.RATE_26_HZ
    elif cnf.datarate_a == "6":
        lsm.acceleration_data_rate = lsm6dsox.RATE_12_5_HZ
        lsm.gyro_data_rate = lsm6dsox.RATE_12_5_HZ
    elif cnf.datarate_a == "7":
        lsm.acceleration_data_rate = lsm6dsox.RATE_12_5_HZ
        lsm.gyro_data_rate = lsm6dsox.RATE_12_5_HZ
        ws=5
    elif cnf.datarate_a == "8":
        lsm.acceleration_data_rate = lsm6dsox.RATE_12_5_HZ
        lsm.gyro_data_rate = lsm6dsox.RATE_12_5_HZ
        ws=10
    elif cnf.datarate_a == "9":
        lsm.acceleration_data_rate = lsm6dsox.RATE_12_5_HZ
        lsm.gyro_data_rate = lsm6dsox.RATE_12_5_HZ
        ws=50
    elif cnf.datarate_a == "10":
        lsm.acceleration_data_rate = lsm6dsox.RATE_12_5_HZ
        lsm.gyro_data_rate = lsm6dsox.RATE_12_5_HZ
        ws=100
        # print("10/10")
    else:
        led.off()
        finish(1)
        sys.exit()

    if int(cnf.datarate_t)<1:
        readbme=False
        
    sleep(0.5)

    cnf.wait_until_start(led)

    parallel = _thread.start_new_thread(write_thread, ())

    # empty buffer and start new
    rb_bme.read()
    all_values='0,0,0'

    filled=0
    n='0'
    while cnf.run_condition():
    # while True:
        # d return parameter from data_available - to see which sensor has new data
        lsm.data_available()
        accx, accy, accz = lsm.acceleration
        astr="{:.3f},{:.3f},{:.3f},".format(accx, accy, accz)
        gyrox, gyroy, gyroz = lsm.gyro
        gstr="{:.3f},{:.3f},{:.3f},".format(gyrox, gyroy, gyroz)
        tmpr= lsm.temperature
        tstr="{:.3f},".format(tmpr)
        if readbme and rb_bme.any() > 0:
            n='1'
            all_values=rb_bme.read()
        if filled%ws == 0:
            timestamp=ticks_ms()
            rb.write(str(timestamp))
            rb.write(',')
            rb.write(astr)
            rb.write(gstr)
            rb.write(tstr)
            rb.write(n)
            rb.write(',')
            rb.write(all_values)
            rb.write("\r\n")
            n='0'
        filled=filled+1
        if filled>=1000:
            filled=0

    run=False
    f[1]=0
    # wait for thread to end
    sleep(2.5)
    finish(0)

if __name__ == "__main__":
    main()
