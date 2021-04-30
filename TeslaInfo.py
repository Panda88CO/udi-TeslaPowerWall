#!/usr/bin/env python3
import requests
#from subprocess import call
import json
import os 
from tesla_powerwall import Powerwall, GridStatus, OperationMode
from  ISYprofile import isyProfile
#import polyinterface
#LOGGER = polyinterface.LOGGER

#ISYunit = {'boolean':2, 'list':25, 'KW' :30, 'percent':51}
class tesla_info:
    def __init__ (self, IPaddress, password, email):
       
        self.TPW = Powerwall(IPaddress)
        self.TPW.login(password, email)
        self.controllerID = 'teslawall'
        self.controllerName = 'powerwall'
        self.chargeLevel = 'chargeLevel'
        self.backupLevel = 'backupLevel'
        self.gridStatus = 'gridStatus'
        self.solarSupply = 'solarSupply'
        self.batterySupply = 'batterySupply'     
        self.gridSupply = 'gridSupply'    
        self.load = 'load'   
        self.dailySolar = 'dailySolar'
        self.dailyConsumption = 'dailyConsumption'
        self.dailyGeneration = 'dailyGeneration'
        self.operationMode = 'operationMode' 
        self.ConnectedTesla = 'connectedTesla'
        self.running = 'running'
        self.powerSupplyMode = 'powerSupplyMode'

        ISYinfo = isyProfile( self.controllerName ,self.controllerID )
        self.ISYvariables = []

        #self.ISYname
       
        ISYinfo.addISYnode(self.controllerID,self.controllerName,'Electricity' )
        ISYinfo.addISYcommandSend(self.controllerID, 'DON')
        ISYinfo.addISYcommandSend(self.controllerID, 'DOF')
        ISYinfo.addISYcommandReceive(self.controllerID, 'UPDATE', 'Update System Data', None)
        ISYinfo.addISYcommandReceive(self.controllerID, 'TEST', 'Test', self.chargeLevel)

        ISYinfo.addIsyVaraiable(self.chargeLevel, self.controllerID, 'percent', 0, 100, None, None, 1, 'Battery Charge Level', None )
        self.ISYvariables.append(self.chargeLevel)
        ISYinfo.addIsyVaraiable (self.backupLevel, self.controllerID, 'percent', 0, 100, None, None, 1, 'Battery Hold-off Level', None )
        self.ISYvariables.append(self.backupLevel)
        ISYinfo.addIsyVaraiable (self.gridStatus, self.controllerID, 'list', None, None, '0-3', None, None, 'Grid Status', {0:GridStatus.CONNECTED.value, 1:GridStatus.ISLANEDED_READY.value, 2:GridStatus.ISLANEDED.value, 3:GridStatus.TRANSITION_TO_GRID.value } )
        self.ISYvariables.append(self.gridStatus)
        ISYinfo.addIsyVaraiable (self.solarSupply, self.controllerID, 'KW', 0, 20, None, None, 1, 'Current Solar Supply', None ) 
        self.ISYvariables.append(self.solarSupply)
        ISYinfo.addIsyVaraiable (self.batterySupply, self.controllerID, 'KW', -20, 20, None, None, 1, 'Current Battery Supply', None ) 
        self.ISYvariables.append(self.batterySupply)
        ISYinfo.addIsyVaraiable (self.gridSupply, self.controllerID, 'KW', -100, 100, None, None, 1, 'Current Grid Supply', None ) 
        self.ISYvariables.append(self.gridSupply)
        ISYinfo.addIsyVaraiable (self.load, self.controllerID, 'KW', -100, 100, None, None, 1, 'Current Load', None ) 
        self.ISYvariables.append(self.load)
        ISYinfo.addIsyVaraiable (self.dailySolar, self.controllerID, 'KW', 0, 1000, None, None, 1, 'Solar Power today', None ) 
        self.ISYvariables.append(self.dailySolar)
        ISYinfo.addIsyVaraiable (self.dailyConsumption, self.controllerID, 'KW', 0, 1000, None, None, 1, 'Power Consumed today', None ) 
        self.ISYvariables.append(self.dailyConsumption)
        ISYinfo.addIsyVaraiable (self.dailyGeneration, self.controllerID, 'KW', 0, 1000, None, None, 1, 'Net Power today', None ) 
        self.ISYvariables.append(self.dailyGeneration)
        ISYinfo.addIsyVaraiable (self.operationMode, self.controllerID, 'list', None, None, '0-3', None, 1, 'Operation Mode', {0:OperationMode.BACKUP.value, 1:OperationMode.SELF_CONSUMPTION.value, 2:OperationMode.AUTONOMOUS.value, 3:OperationMode.SITE_CONTROL.value } )                
        self.ISYvariables.append(self.operationMode)
        ISYinfo.addIsyVaraiable (self.ConnectedTesla, self.controllerID, 'boolean', None,None, 0-1,None, None, 'Connected to Tesla', { 0:'False', 1: 'True' }) 
        self.ISYvariables.append(self.ConnectedTesla)
        ISYinfo.addIsyVaraiable (self.running, self.controllerID, 'boolean', None,None, 0-1,None, None, 'Power Wall Running', { 0:'False', 1: 'True' }) 
        self.ISYvariables.append(self.running)
        ISYinfo.addIsyVaraiable (self.powerSupplyMode, self.controllerID, 'boolean', None,None, 0-1,None, None, 'Power Supply Mode', { 0:'False', 1: 'True' }) 
        self.ISYvariables.append(self.powerSupplyMode)
        ISYinfo.addIsyVaraiable (self.gridServiceActive, self.controllerID, 'boolean', None,None, 0-1,None, None, 'Grid Services Active (supplying?)', { 0:'False', 1: 'True' }) 
        self.ISYvariables.append(self.gridServiceActive)

        ISYinfo.addControllerDefStruct(self.controllerName, self.controllerID )
        ISYinfo.createSetupFiles('./profile/nodedef/nodedefs.xml','./profile/editor/editors.xml', './profile/nls/en_us.txt')
        self.ISYmap = ISYinfo.createISYmapping()

        if not(self.TPW.is_authenticated()):
            print('Error Logging into Tesla Power Wall')

    
    def setSendCommand(self, name, NodeId):
        print()

    def setAcceptCommand(self, name, nodeId, TeslaVariable, ButtonText):
        print()

    def setTeslaCredentials (self, IPaddress, password, email):
        self.IPaddress = IPaddress
        self.password = password
        self.email = email

    def getTPW_AvailableVars(self, nodeId):
        return(ISYvariables)

    def TPW_updateMeter(self):
        #call meters to variable
        return(None)


    def getTPW_chargeLevel(self):
        return(self.TPW.get_charge())
        
    def getTPW_backupLevel(self):
        return(self.TPW.get_backup_reserve_percentage())

    def getTPW_gridStatus(self):
        return(None)

    def getTPW_solarSupply(self):
        return(None)
    
    def getTPW_batterySupply(self):
        return(None)

    def getTPW_gridSupply(self):
        return(None)

    def getTPW_load(self):
        return(None)

    def getTPW_dailySolar(self):
        return(None)

    def getTPW_dailyConsumption(self):
        return(None)

    def getTPW_dailyGeneration(self):
        return(None)

    def getTPW_operationMode(self):
        return(None)   
    
    
    def getTPW_running(self):
        return(None)   
    
    def getTPW_powerSupplyMode(self):
        return(None)   