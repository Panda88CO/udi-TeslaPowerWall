#!/usr/bin/env python3
import requests
#from subprocess import call
import json
import os 
from tesla_powerwall import Powerwall, GridStatus, OperationMode
from  ISYprofile import isyProfile
#import polyinterface
#LOGGER = polyinterface.LOGGER


class tesla_info:
    def __init__ (self, IPaddress, password, email):
       
        self.TPW = Powerwall(IPaddress)
        self.TPW.login(password, email)
        ISYinfo = isyProfile('teslawall','powerwall')

        if not(self.TPW.is_authenticated()):
            print('Error Logging into Tesla Power Wall')



  
    def setTeslaCredentials (self, IPaddress, password, email):
        self.IPaddress = IPaddress
        self.password = password
        self.email = email


    def getTPWchargeLevel(self):
        chargePercentage = self.TPW.get_charge()
        
    