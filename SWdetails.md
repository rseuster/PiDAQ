# Software and Hardware Details about PiDAQ
The requested features of the designed device was to take inertial
measurements at up to 100Hz, and possibly take data with less frequency
for an extended period of time, typically over 12-24h, but possibly also
over long weekends.

We tested several popular microcontrollers and boards and finally settled
on the following configuration.
The hardware consists of a standard Raspberry Pi Pico2
and two specialized sensor chips:

1. [BME280](https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/)
   for measuring temperature, pressure and humidity.
1. [LSM6DSOX](https://www.st.com/en/mems-and-sensors/lsm6dsox.html) is a IMU
   (inertial measurements units) providing a 3-axis accelerometer and a 3-axis
   gyroscope.

Data is stored on a conventional SD Card, that can be taken out and read
out by a standard computer with an internal micro SD cardreader or
an external one. This leaves plenty of storage space for multiple measurements,
even for long measurements at a high data rate. The data is stored on the
SD card as a CSV file with a 3 digit suffix, increasing the number for
each measurement. Metadata at the beginning of the file lists the measurement
conditions, as well as user defined string, that can list the names of the
students that have conducted the experiment.

The IMU is typically read out at a rate of about 100Hz, but the BME280
typically only at about 10Hz. Therefore, and to allow for future extensions,
the IMU is read out from a single hardware I2C bus, but the BME280 from
a single software driven I2C bus.

## More Details about the Software
Early tests resulted in frequent gaps in the IMU measurements when the BME was
read out. This was eventually traced back to the fact that MicroPython typically
runs only on one core, even if the MCU has multiple cores. The python processing
and print out of the BME measurements were taking significant time resulting in
the gaps in the IMU measurements, although the Pico2 MCU has two cores available.
To reduce this effect, the writing out of the measurement data was moved into its
own thread. Since writing to SD card is not time critical and can be paused for
short periods of time, the same thread is also reading out the BME.

Two ringbuffers are used to transfer the data in ASCII format between the two
threads, one is 32kB big and transfers all text data that's going to be written
out. The other ringbuffer is 512bytes long and is just used to move the text data
from the BME to the main thread where it is appended to the IMU data.

Since the threading support in micropython is at the time of writing relatively
new, there were a few quirks to avoid missing features. The mayor deficiency is
that global variables often are not visible in all threads, but arrays are. So,
some variables are mirrored in an array.

### Standard Libraries for IMU and Temperature Sensors
Both the IMU and the BME are read out by standard libraries, commonly used.
Both libraries are based on code from Adafruit, which in turn is based on
code provided by the manufacturer.

The code for the IMU is still available on
[github](https://github.com/jposada202020/MicroPython_LSM6DSOX),
but according to the author is not maintained any more. The alternative from
Adafruit however pulls in many dependencies, that during testing other
microprocessors, the available flash memory got exhausted. The Pico2 should
provide enough flash memory, but we decided to stick to the working library.
We have created a [fork](https://github.com/uvic-rs/MicroPython_LSM6DSOX) of
this library, to ensure continuous access to this repository.

For the BME sensor the code is part of this
[repository](https://github.com/robert-hh/BME280)
where we took the float version of this library.

The code for accessing the SDCard is from the official
[MicroPython repository](https://github.com/micropython/micropython-lib/tree/master/micropython/drivers/storage/sdcard),
which is not included in the micropython for the Pico2, because by default
it doesn't provide a SDcard.

### Code for Debouncing Keys
Although libraries exist that handle debouncing of keys, it was decided to
write an own implementation, as in this application it's very simple.

Keys need to be typically debounced, as when users press or release a button,
the output will still ripple between on and off within several micro seconds.
For the users, this is undetectable, but even todays microprocessors are fast
enough to easily detect those ripples.

To reliably detect a button event from a user, following code was implemented:
1. any change in the state of the button will trigger an interrupt.
1. all the interrupt is doing is to start a timer of a confgurable time window, typically
   around 20 microseconds
1. any further state change within this time window of this button will delete the
   timer and restart a new timer
1. if no further state change is detected within this time window, the value for the button
   will toggle its state between on and off.

The whole code for this is in file ```lib/debounce.py``` and is about 1kB in length
including some code for basic testing.

### Code for SD Card
The code for accessing the SD card is again a provided library and based on examples.

The only complication arises from a possible use case, when users take longer data runs,
but finish early and just switch off power to the device. Initially, the filesize
of the resulting data file was zero, so it contained no data, even for longer runs
where some data must have been flushed to the SD card. In such a situation, the data
file was never closed, leading to this problem.

The code then was modified such that initially the MetaData is written to the file,
then the file is closed and for writing the data, the file is opened in "append" mode.
After each data point is written, now the file is flushed, resulting in
almost all data will then be contained in the data file with only very small
time period of data possibly missing in the file.


## Creating an Environment for Software Development
The section "Installation Instructions" in the README will at the same time create a
suitable environment for software development. The developer can choose between using
Thonny to modify the code and run and debug it, or an editor of choise and the mpremote
upload scripts.