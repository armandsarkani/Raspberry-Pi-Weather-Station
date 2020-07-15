from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD
import time
import RPi.GPIO as GPIO
import Freenove_DHT as DHT
import urllib.request
import codecs
import csv


def get_CIMIS_data():
    data = {}
    et0 = 0
    hum = 0
    temp = 0
    url = "ftp://ftpcimis.water.ca.gov/pub2/hourly/hourly075.csv"
    ftpstream = urllib.request.urlopen(url) # open FTP URL
    csvfile = csv.reader(codecs.iterdecode(ftpstream, 'utf-8')) # parse CSV
    for line in reversed(list(csvfile)):
        if(line[4] == "--"):
            continue
        else:
            et0 = round(float(line[4]), 2)
            temp = round(float(line[12]), 2)
            hum = round(float(line[14]), 2)
            data.update({"et0": et0, "temp": temp, "hum": hum})
            return data
def derate(local_temp, local_humidity, cimis_temp, cimis_humidity, et_station): # this function derates CIMIS ET based on local values (get local ET value)
    CIMIS_data = get_CIMIS_data()
    temp_derate = local_temp/cimis_temp
    humidity_derate = local_humidity/cimis_humidity
    et_derate = et_station * (temp_derate/humidity_derate)
    return et_derate
def calculate_gallons(ET): # calculate gallons for a given ET
    PF = 1.0
    SF = 200
    IE = 0.75
    gallons = (ET * PF * SF * 0.62)/IE
    return gallons
def get_irrigation_time(gallons): # convert gallons to time based on assumption of irrigation at 1020 gal/hr
    seconds = (gallons/1020)*60*60
    return seconds

    
