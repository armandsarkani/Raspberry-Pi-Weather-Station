# Raspberry Pi Weather Station
Raspberry Pi Weather Station based on CIMIS (California Irrigation Management Information System) data created for EECS 113 final project. 

## Overview

In this project, I designed a smart weather station using a Raspberry Pi that is able to constantly capture data about the current local temperature and humidity using a DHT sensor, and compare it with values received from the state of California’s website (CIMIS) to estimate how much water should be used for irrigation on a 200 square foot lawn. Evapotranspiration (ET) data from CIMIS is used alongside frequent local DHT readings to estimate a local ET value, which in turn is used to calculate how many gallons of water should be used for irrigation, how long the system should irrigate in a one-hour time period, and any potential water savings/deficits that are accrued by using this localized estimate (rather than the CIMIS ET values). An additional feature was implemented to temporarily pause irrigation if motion is detected by the PIR sensor. Irrigation is happening once per hour, and at the end of a 24 hour 
period, total statistics are provided.

## Hardware Setup 

The detailed hardware setup is shown in the report PDF. Requires access to Raspberry Pi GPIO pins as well as open-source Adafruit and Freenove libraries (included in Code directory). 

<img src="https://github.com/armandsarkani/Raspberry-Pi-Weather-Station/blob/master/Images/IMG_1860.jpeg" width="1024" height="768" />


