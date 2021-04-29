#!/usr/bin/env python3
import requests
#from subprocess import call
import json
import os 
from tesla_powerwall import Powerwall, GridStatus, OperationMode
from  ISYprofile import isyProfile
#import polyinterface
#LOGGER = polyinterface.LOGGER

ISYunit = {'percent' : 51, 'list': 25,  'KW':30}
class tesla_info:
    def __init__ (self, IPaddress, password, email):
       
        self.TPW = Powerwall(IPaddress)
        self.TPW.login(password, email)
        self.controllerName = 'teslawall'
        self.chargeLevel = 'chargeLevel'
        self.backupLevel = 'backupLevel'
        
        self.ISYname
        ISYinfo = isyProfile('teslawall','powerwall')
        ISYinfo.addIsyVaraiable (self.chargeLevel, self.controllerName, IYSinfo.ISYunit('percent'), 0, 100, None, None, 1, 'Battery Charge Level', None )
        ISYinfo.addIsyVaraiable (self.backupLevel, self.controllerName, IYSinfo.ISYunit('percent'), 0, 100, None, None, 1, 'Battery Hold-off Level', None )
        ISYinfo.addIsyVaraiable (self.chargeLevel, self.controllerName, IYSinfo.ISYunit('list'), None, None, '0-3', None, 1, 'Grid Status', {0:GridStatus.CONNECTED.value
                                                                                                                                            ,1:GridStatus.ISLANEDED_READY.value
                                                                                                                                            ,2:GridStatus.ISLANEDED.value
                                                                                                                                            ,3:GridStatus.TRANSITION_TO_GRID.value } )
                                            

        if not(self.TPW.is_authenticated()):
            print('Error Logging into Tesla Power Wall')

    

  
    def setTeslaCredentials (self, IPaddress, password, email):
        self.IPaddress = IPaddress
        self.password = password
        self.email = email


    def getTPWchargeLevel(self):
        chargePercentage = self.TPW.get_charge()
        
    