# PiDAQ
The PiDAQ is a small microcontroller board based on the
[Raspberry Pico Pi 2 device](https://www.raspberrypi.com/products/raspberry-pi-pico-2/)
and aims to be a simple and easy to use data aquisition ("DAQ") system that can be
used by students in teaching labs at high schools and universities. The device writes
the measurement data to files in CSV (comma separated values) to a SD card that can then
be read on the students laptops.
The Pico 2 board is connected to a custom PCB board providing access to two specialized sensor chips:

1. [BME280](https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/)
   for measuring temperature, pressure and humidity, the data on the SD card will be
   in degree Celsius, hPa and percent. The ranges are roughtly for the temperature sensor
   from -40 to 85 deg C, about 300 to 1100 hPa for the pressure sensor and 0-100% of humidity.
1. [LSM6DSOX](https://www.st.com/en/mems-and-sensors/lsm6dsox.html) is an IMU
   (inertial measurements units) providing a 3-axis accelerometer and a 3-axis
   gyroscope, the data on the SD card will be in m/s^2 and degrees per second ("dps").
   The maximum ranges are +- 16g and +- 2000dps, whereas the default settings are +-4g and
   +-250dps.

The software has been written in [MicroPython](https://micropython.org/) and is described
[here in more defails](SWdetails.md) together with some details about the hardware.
Below we describe how to install the software on the board and includes setting up an
environment for further software development.

## Taking Measurements
Once the [software is installed](#installation_instructions) on the device and the battery
charged, the users will want to set the proper [start and stop conditions](/SWdetails/#configuration-file)
for the measurement.

The device has 3 LEDs, the internal LED of the Pico 2 board and two LEDs next to the two buttons.
Once the device is switched on it will emit a short flash once per second on the internal LED to indicate
its readyness. All other modes of LED flashing points to an error, e.g. the SD card
might be missing.

Then, once the start condition is met, the device will then take data and write o SD card.
The flashing will change to about 50% duty cycle, still at 1Hz.

Once the stop condition is met, the internal LED will be constantly lit, indicating the end
of the measurement.

## Installation Instructions
To install the PiDAQ software on a fresh device, please follow the instructions below.
If you experience problems, please first re-format the SD card and re-install from
scratch including installation of the lastest micropython version for the Pico2 (W).

1. clone this repository
   ```
   git clone https://github.com/rseuster/PiDAQ
   cd PiDAQ
   ```
1. create a virtual environment, activate it and pip-install all required packages
   ```
   virtualenv .
   . bin/activate
   pip install -r requirements.txt
   ```
1. download the corresponding micropython image for your version of Pico2,
   follow the links for the [Pico2](https://micropython.org/download/RPI_PICO2) or
   for the [Pico2 W](https://micropython.org/download/RPI_PICO2_W)
1. While connecting the device to the computer via a USB cable where you downloaded
   the micropython image to, keep the "**boot**" button pressed. The Pico2 should now show
   up as an external storage device. Copy/move the micropython image with the uf2
   extension to this storage device, preferencially from a terminal.
1. Once the micropython image is uploaded, the storage device should disappear and the
   Pico2 reboot. The terminal prompt should have returned.
1. Run the script upload_PiDAQ.sh to upload all necessary files to the device.
   ```
   ./upload_PiDAQ.sh
   ```
1. Either insert an empty SD card into the device and run the first time to
   create a default configuration file or create a valid configuration file according
   to <reference> and put it into the root of the SDcard, with the name "configuration".

Once the battery is charged, the unit is ready for [data aquisition](#taking-measurements).

## Configuration file
Normally, the SD card will contain the configuration file. Students can
write to this file to set suitable start and stop conditions for the experiment.

### Start and Stop Conditions
The start and stop of a datataking can be initiated by either a time or
press/release of one of the two buttons of the device.

### Default Configuration File
If the SD card contains no configuration file, this default file will be used. Note, that
lines starting with "#" will be treated as comments and ignored for the configuration settings:

```
Metadata: taken on XYZ by A, B
StartCondition: button1[off]
# StopCondition:  time[30s]
StopCondition:  button2[on]
DataRate(A/T):  3 - 1
```

This will trigger the following behaviour:
After switching on the device, it will emit short pulses on the internal
LED, indicating that it's ready to start data taking. It will then wait
for the user to push and release button1 ("button1[off]") to start writing
out the data. The device will then continue to take data until button2
is pressed ("button2[on]"). The internal LED will then light up to indicate the
data taking has ended.

### Other Configuration Options
The other option for the start or stop condition is to configure "time".
Typically it will only apply to the StopCondition. The user can define
a time frame for the measurement. Possible timeunits are "[s,m,h]".
Only integer values are allowed, no fractions.

### DataRate
The "DataRate" will take two integers as a configuration,
separated by a minus sign.
The first integer labelled "A" has an allowed range from 1-10, with the meaning:

| A | rate |
|:---:|:-----------:|
| 1 | 416 Hz    |
| 2 | 208 Hz    |
| 3 | 104 Hz    |
| 4 |  52 Hz    |
| 5 |  26 Hz    |
| 6 |  12.5 Hz    |
| 7 | 12.5 Hz, record only every 5th sample |
| 8 | 12.5 Hz, record only every 10th sample |
| 9 | 12.5 Hz, record only every 50th sample |
| 10 | 12.5 Hz, record only every 100th sample |

The allowed range for the DataRate "T" for the BME sensor is integer range, however
values smaller than 1 will switch off reading out this sensor.

| T | rate |
| :---: | :-------------: |
| n | once every n * 100ms |



## Data Format
The data is stored in CSV (comma separated values) with a few comments at the top of the file.
An example of a data file  is given here:
```
# StartCondition: {'S': 'off', 'T': 0, 'C': 'button1'}
# StopCondition : {'S': 'on', 'T': 0, 'C': 'button2'}
# DataRate(A/T) : 3 - 1
# Metadata : taken on XYZ by A, B
# time,ax,ay,az,gx,gy,gz,tA,new,t,p,h
11043,-0.433,4.043,-10.594,-0.856,-0.437,-0.466,18.441,0,0,0,0
11049,-1.836,6.195,-9.082,-1.302,-0.361,-0.249,18.441,0,0,0,0
```
The first four lines repeat the current content of the configuration file, the order
might be different though. The fifth line describes the data which is as follows.


| variablename | comment |
|:---:|:-----------:|
| time | timestamp in milliseconds (time since power on)  |
| ax, ay, az | 3-D coordinates of the accelerometer, magnitude of ~ 9.81 at rest, units in m/s^2 |
| gx, gy, gz | 3-D coordinates of gyroscope, zero at rest, units in dps ("degrees per second") |
| tA   | temperature of the accelerometer sensor, used for applying calibration |
| new  | "1" indicates a new measurements for the BME sensor, "0" indicates same values as the line above |
| t, p, h | temperature, pressure and humidity, in degree Celsius, hPa and percent (%) |


## LED / Error Codes / End of Measurement Indication
The PiDAQ has only 3 LEDs to communicate with the world, one on board of the Pico2
and two lights right next to the two buttons.

In normal conditions, so before or during a measurement, when the software detects a button
is pressed, the corresponding light will go on. If this doesn't happen, either the
measurement is done and enough time has passed so that all LEDs are off. Or the device is
in an error condition.

After a measurement is done, the internal LED will turn on and the program finishes. Interrupts
are still handled, so the LEDs for buttons should still function.

Currently there are two error conditions detected:

1. no SD card, so data cannot be stored. All 3 LEDs will turn on one at a time for 1/6th of a second
   for a period of 30 seconds, then all 3 LEDs are off.
2. the configuration file had an error and could not be processed. All three LEDs will flash at 2Hz
   for 30 seconds, then all 3 LEDs are off.