#!/usr/bin/env python3
from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD

import time
from datetime import datetime
import RPi.GPIO as GPIO
import threading
import Freenove_DHT as DHT
import CIMIS
import logging
 
LED_pin = 12
PIR_pin = 29
DHT_pin = 11
hourly_temp_avg = 0
hourly_humidity_avg = 0
logger = None
et_station_total = 0
et_local_total = 0
CIMIS_temp_total = 0
CIMIS_humidity_total = 0
def setup_motion():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)        # use PHYSICAL GPIO Numbering
    GPIO.setup(LED_pin, GPIO.OUT)    # set ledPin to OUTPUT mode
    GPIO.setup(PIR_pin, GPIO.IN)  # set sensorPin to INPUT mode
    GPIO.output(LED_pin, GPIO.LOW)
def CIMIS_irrigation(): # get CIMIS data and display on LCD
    global et_station_total
    global et_local_total
    global CIMIS_temp_total
    global CIMIS_humidity_total
    CIMIS_data = CIMIS.get_CIMIS_data() # get latest CIMIS data
    et_station_total += CIMIS_data["et0"]
    CIMIS_temp_total += CIMIS_data["temp"]
    CIMIS_humidity_total += CIMIS_data["hum"]
    et_local = CIMIS.derate(hourly_temp_avg, hourly_humidity_avg, CIMIS_data["temp"], CIMIS_data["hum"], CIMIS_data["et0"]) # derate ET based on local values
    et_local_total += et_local
    local_gallons = CIMIS.calculate_gallons(et_local) # calculate gallons of water needed with local ET
    CIMIS_gallons = CIMIS.calculate_gallons(CIMIS_data["et0"]) # calculate gallons of water needed with CIMIS ET
    irrigation_time = CIMIS.get_irrigation_time(local_gallons) # get irrigation time
    lcd.clear() # display all this on LCD in future lines
    title_str = "CIMIS Values\n"
    CIMIS_values_str = "Temp: " + str(CIMIS_data["temp"]) + " F " + " Humidity: " + str(CIMIS_data["hum"]) + "%"
    logger.debug("CIMIS Values")
    logger.debug(CIMIS_values_str)
    scroll_bottom_line(title_str, CIMIS_values_str)
    time.sleep(2)
    lcd.clear()
    title_str = "ET Values\n"
    et_local_str = "{:.2f}".format(et_local)
    et_str = "Local: " + et_local_str + " CIMIS: " + str(CIMIS_data["et0"])
    logger.debug("ET Values")
    logger.debug(et_str)
    scroll_bottom_line(title_str, et_str)
    time.sleep(2)
    logger.debug("Gallons used in this hour: " + str(local_gallons))
    if(local_gallons < CIMIS_gallons): # get number of gallons difference to determine if savings or deficit
        savings = CIMIS_gallons - local_gallons
        savings_str = "{:.2f}".format(savings)
        lcd.clear()
        lcd.message("Water Savings!\n")
        lcd.message(savings_str + " gallons")
    else:
        deficit = local_gallons - CIMIS_gallons
        deficit_str = "{:.2f}".format(deficit)
        lcd.clear()
        lcd.message("More Water Used!\n")
        lcd.message(deficit_str + " gallons")
    time.sleep(2)
    lcd.clear()
    irrigation_time_str = "{:.2f}".format(irrigation_time)
    lcd.message("Irrigating... \n")
    lcd.message("Time: " + irrigation_time_str + " sec")
    logger.debug("Irrigating...")
    logger.debug("Time: " + irrigation_time_str + "sec")
    irrigation_thread = threading.Thread(target=irrigation, args=(irrigation_time, time.time(),))
    irrigation_thread.start() # start irrigation (indicated by blinking LED)
    time.sleep(2)
def irrigation(irrigation_time, irrigation_start_time):
    output = GPIO.HIGH
    while(True):
        if(GPIO.input(PIR_pin)==GPIO.HIGH): # if motion is detected
            irrigation_time = irrigation_time - (time.time() - irrigation_start_time)
            motion_start_time = time.time()
            GPIO.output(LED_pin, GPIO.LOW)
            while(time.time() - motion_start_time <= 60):
                if(GPIO.input(PIR_pin) == GPIO.HIGH):
                    continue
                else:
                    irrigation_start_time == time.time()
                    break
        if(time.time() - irrigation_start_time >= irrigation_time): # if timer over
            logger.debug("Irrigation done\n")
            GPIO.output(LED_pin, GPIO.LOW)
            break
        if(output == GPIO.HIGH):
            output = GPIO.LOW
        else:
            output = GPIO.HIGH
        GPIO.output(LED_pin, output)
        time.sleep(0.2)
def get_time_now():     # get system time
    return datetime.now().strftime('%H:%M:%S')
def scroll_bottom_line(static_str, scrolling_str):
    for i in range(0, len(scrolling_str)-15):
        lcd.message(static_str)
        lcd.message(scrolling_str[i:(i+17)])
def loop():
    global hourly_temp_avg
    global hourly_humidity_avg
    global et_station_total
    global CIMIS_temp_total
    global CIMIS_humidity_total
    global et_local_total
    num_hours = 0
    local_temp_total = 0
    local_humidity_total = 0
    mcp.output(3,1)     # turn on LCD backlight
    lcd.begin(16,2)     # set number of LCD lines and columns
    setup_motion()
    dht = DHT.DHT(DHT_pin)
    while(True):
        hourly_temp_total = 0
        hourly_humidity_total = 0
        counter = 0
        init_time = time.time()
        num_readings = 0
        while(time.time() - init_time <= 3600): # calculate an hour's worth of data
            lcd.setCursor(0,0)  # set cursor position
            DHT_checksum = dht.readDHT11()
            if(DHT_checksum is dht.DHTLIB_OK and dht.humidity <= 100.0):
                dht_temp_f = dht.temperature * 9/5 + 32
                hourly_temp_total += dht_temp_f
                hourly_humidity_total += dht.humidity
                dht_temp = "{:.2f}".format(dht_temp_f)
                dht_humidity = "{:.2f}".format(dht.humidity)
                lcd.clear()
                lcd.message("Temp: " + dht_temp + " F\n") # display temp and humidity every minute
                lcd.message("Humidity: " + dht_humidity + "%\n")
                num_readings += 1
                time.sleep(60)
            else:
                continue
        # get hourly averages
        num_hours += 1
        logger.debug("Hour: " + str(num_hours))
        hourly_temp_avg = hourly_temp_total/num_readings
        hourly_humidity_avg = hourly_humidity_total/num_readings
        local_temp_total += hourly_temp_avg
        local_humidity_total += hourly_humidity_avg
        hourly_temp_avg_str = "{:.2f}".format(hourly_temp_avg)
        hourly_humidity_avg_str = "{:.2f}".format(hourly_humidity_avg)
        lcd.clear()
        title_str = "Hourly Averages \n" # display hourly averages
        hourly_avg_str = "Temp: " + hourly_temp_avg_str + " F " + " Humidity: " + hourly_humidity_avg_str + "%"
        logger.debug("Hourly Averages")
        logger.debug(hourly_avg_str)
        scroll_bottom_line(title_str, hourly_avg_str)
        time.sleep(2)
        CIMIS_irrigation()
        if(num_hours == 24): #24 hour report
            CIMIS_temp_avg = CIMIS_temp_total/24
            CIMIS_humidity_avg = CIMIS_humidity_total/24
            local_temp_avg = local_temp_total/24
            local_humidity_avg = local_humidity_total/24
            local_gallons_total = CIMIS.calculate_gallons(et_local_total)
            CIMIS_gallons_total = CIMIS.calculate_gallons(et_station_total)
            irrigation_time_total = CIMIS.get_irrigation_time(local_gallons_total)
            lcd.clear()
            title_str = "Daily ET Values\n"
            et_local_str = "{:.2f}".format(et_local_total)
            et_str = "Local: " + et_local_str + " CIMIS: " + str(et_station_total)
            scroll_bottom_line(title_str, et_str)
            time.sleep(2)
            logger.debug("After 24 hours ...")
            logger.debug("Total ET Station: " + str(et_station_total))
            logger.debug("Total ET Local: " + str(et_local_total))
            logger.debug("CIMIS Temperature Average: " + str(CIMIS_temp_avg))
            logger.debug("CIMIS Humidity Average: " + str(CIMIS_humidity_avg))
            logger.debug("Local Temperature Average: " + str(local_temp_avg))
            logger.debug("Local Humidity Average: " + str(local_humidity_avg))
            logger.debug("Total gallons local: " + str(local_gallons_total))
            logger.debug("Total gallons CIMIS: " + str(CIMIS_gallons_total))
            logger.debug("Total irrigation time: " + str(irrigation_time_total))
            if(local_gallons_total < CIMIS_gallons_total): # get number of gallons difference to determine if savings or deficit
                savings = CIMIS_gallons_total - local_gallons_total
                savings_str = "{:.2f}".format(savings)
                lcd.clear()
                lcd.message("Water Savings!\n")
                lcd.message(savings_str + " gallons")
            else:
                deficit = local_gallons_total - CIMIS_gallons_total
                deficit_str = "{:.2f}".format(deficit)
                lcd.clear()
                lcd.message("More Water Used!\n")
                lcd.message(deficit_str + " gallons")
            time.sleep(2)
            return
def destroy():
    lcd.clear() # if KeyboardInterrupt
    
PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.
# Create PCF8574 GPIO adapter.
try:
    mcp = PCF8574_GPIO(PCF8574_address)
except:
    try:
        mcp = PCF8574_GPIO(PCF8574A_address)
    except:
        print ('I2C Address Error !')
        exit(1)
# Create LCD, passing in MCP GPIO adapter.
lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)

if __name__ == '__main__':
    try:
        logging.basicConfig(filename="HourlyLog.log", format='%(asctime)s %(message)s', filemode='w')
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.debug("Start time\n")
        loop() #start program
    except KeyboardInterrupt:
        destroy()

