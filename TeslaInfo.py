#!/usr/bin/env python3
import requests
#from subprocess import call
import json
import os 
import datetime
from tesla_powerwall import Powerwall, GridStatus, OperationMode
from  ISYprofile import isyProfile
#import polyinterface
#LOGGER = polyinterface.LOGGER

#ISYunit = {'boolean':2, 'list':25, 'KW' :30, 'percent':51}
class tesla_info:
    def __init__ (self, IPaddress, password, email, ISY_Id):
       
        self.TPW = Powerwall(IPaddress)
        self.TPW.login(password, email)
        self.controllerID = ISY_Id
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
        self.gridServiceActive = 'gridServiceActive'


        self.metersStart = True
        self.gridStatusEnum = {0:GridStatus.CONNECTED.value, 1:GridStatus.ISLANEDED_READY.value, 2:GridStatus.ISLANEDED.value, 3:GridStatus.TRANSITION_TO_GRID.value }
        self.operationEnum =  {0:OperationMode.BACKUP.value, 1:OperationMode.SELF_CONSUMPTION.value, 2:OperationMode.AUTONOMOUS.value, 3:OperationMode.SITE_CONTROL.value }
        ISYinfo = isyProfile( self.controllerName ,self.controllerID )
        self.ISYvariables = {}

        #self.ISYname
       
        ISYinfo.addISYnode(self.controllerID,self.controllerName,'Electricity' )
        ISYinfo.addISYcommandSend(self.controllerID, 'DON')
        ISYinfo.addISYcommandSend(self.controllerID, 'DOF')
        ISYinfo.addISYcommandReceive(self.controllerID, 'UPDATE', 'Update System Data', None)
        ISYinfo.addISYcommandReceive(self.controllerID, 'TEST', 'Test', self.chargeLevel)

        ISYinfo.addIsyVaraiable(self.chargeLevel, self.controllerID, 'percent', 0, 100, None, None, 1, 'Battery Charge Level', None )
        ISYinfo.addIsyVaraiable(self.backupLevel, self.controllerID, 'percent', 0, 100, None, None, 1, 'Battery Hold-off Level', None )       
        ISYinfo.addIsyVaraiable (self.gridStatus, self.controllerID, 'list', None, None, '0-3', None, None, 'Grid Status', self.gridStatusEnum )
        ISYinfo.addIsyVaraiable (self.solarSupply, self.controllerID, 'KW', 0, 20, None, None, 1, 'Current Solar Supply', None ) 
        ISYinfo.addIsyVaraiable (self.batterySupply, self.controllerID, 'KW', -20, 20, None, None, 1, 'Current Battery Supply', None ) 
        ISYinfo.addIsyVaraiable (self.gridSupply, self.controllerID, 'KW', -100, 100, None, None, 1, 'Current Grid Supply', None ) 
        ISYinfo.addIsyVaraiable (self.load, self.controllerID, 'KW', -100, 100, None, None, 1, 'Current Load', None ) 
        ISYinfo.addIsyVaraiable (self.dailySolar, self.controllerID, 'KW', 0, 1000, None, None, 1, 'Solar Power today', None ) 
        ISYinfo.addIsyVaraiable (self.dailyConsumption, self.controllerID, 'KW', 0, 1000, None, None, 1, 'Power Consumed today', None ) 
        ISYinfo.addIsyVaraiable (self.dailyGeneration, self.controllerID, 'KW', 0, 1000, None, None, 1, 'Net Power today', None ) 
        ISYinfo.addIsyVaraiable (self.operationMode, self.controllerID, 'list', None, None, '0-3', None, 1, 'Operation Mode', self.operationEnum )                
        ISYinfo.addIsyVaraiable (self.ConnectedTesla, self.controllerID, 'boolean', None,None, 0-1,None, None, 'Connected to Tesla', { 0:'False', 1: 'True' }) 
        ISYinfo.addIsyVaraiable (self.running, self.controllerID, 'boolean', None,None, 0-1,None, None, 'Power Wall Running', { 0:'False', 1: 'True' }) 
        ISYinfo.addIsyVaraiable (self.powerSupplyMode, self.controllerID, 'boolean', None,None, 0-1,None, None, 'Power Supply Mode', { 0:'False', 1: 'True' }) 
        ISYinfo.addIsyVaraiable (self.gridServiceActive, self.controllerID, 'boolean', None,None, 0-1,None, None, 'Grid Services Active (supplying?)', { 0:'False', 1: 'True' }) 

        ISYinfo.addControllerDefStruct(self.controllerName, self.controllerID )
        ISYinfo.createSetupFiles('./profile/nodedef/nodedefs.xml','./profile/editor/editors.xml', './profile/nls/en_us.txt')
        self.ISYmap = ISYinfo.createISYmapping()
        self.TPW = Powerwall(IPaddress)
        self.TPW.login(password, email)
        if not(self.TPW.is_authenticated()):
            print('Error Logging into Tesla Power Wall')            
        else:        
            self.pollSystemData()


    '''
    def addISYvariables(self, variable, ID):
        if ID in self.ISYvariables:
            self.ISYvariables[ID].append(variable)
        else:
            self.ISYvariables[ID] = []
            self.ISYvariables[ID].append(variable)
    '''

    def supportedParamters (self, nodeId):
        if nodeId in self.ISYmap:
            temp = self.ISYmap[nodeId]
        else:
            print('Unknown Node Id: ' + str(nodeId))
            temp = None
        return(temp)


    def pollSystemData(self):
        self.meters = self.TPW.get_meters()
        self.status = self.TPW.get_sitemaster()
        if self.metersStart: 
            self.meterDayStart = self.meters
            self.timeLast = datetime.timede()
            sleep(1)
            self.meterStart = False
        self.timeNow = datetime.time()    
        if self.timeNow < self.timeLast: # we passed midnight
            self.metersDayStart = self.meters
        self.timeLast = self.timeNow



    def getISYvalue(self, ISYvar, node):
        if ISYvar in self.ISYmap[node]:
            self.teslaVarName = self.ISYmap[node][ISYvar]['systemVar']
            if self.teslaVarName == self.chargeLevel: 
                return(self.getTPW_chargeLevel())
            elif self.teslaVarName == self.backupLevel: 
                return(self.getTPW_backupLevel())
            elif self.teslaVarName == self.gridStatus: 
                return(self.getTPW_gridStatus())
            elif self.teslaVarName == self.solarSupply:
                return(self.getTPW_solarSupply())
            elif self.teslaVarName == self.batterySupply:
                return(self.getTPW_batterySupply())
            elif self.teslaVarName == self.gridSupply:
                return(self.getTPW_gridSupply())
            elif self.teslaVarName == self.load:
                return(self.getTPW_load())
            elif self.teslaVarName == self.dailySolar:
                return(self.getTPW_dailySolar())
            elif self.teslaVarName == self.dailyConsumption:
                return(self.getTPW_dailyConsumption())
            elif self.teslaVarName == self.dailyGeneration:
                return(self.getTPW_dailyGeneration())             
            elif self.teslaVarName == self.operationMode:
                return(self.getTPW_operationMode())
            elif self.teslaVarName == self.ConnectedTesla:
                return(self.getTPW_ConnectedTesla())
            elif self.teslaVarName == self.running:
                return(self.getTPW_running())
            elif self.teslaVarName == self.powerSupplyMode:
                return(self.getTPW_powerSupplyMode())
            elif self.teslaVarName == self.gridServiceActive:
                return(self.getTPW_gridServiceActive())
            else:
                print('Error - unknown variable: ' + str(self.teslaVarName )) 
        else:
            print('Error - unknown variable: ' + str(ISYvar)) 

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
        EnumVal = -1
        statusVal = self.TPW.get_grid_status()
        for key in self.gridStatusEnum:
            if statusVal.value == self.gridStatusEnum[key]:
                EnumVal = key
        return(EnumVal)

    def getTPW_solarSupply(self):
        return(self.meters.solar.instant_power)
    
    def getTPW_batterySupply(self):
        return(self.meters.battery.instant_power)

    def getTPW_gridSupply(self):
        return(self.meters.site.instant_power)

    def getTPW_load(self):
        return(self.meters.load.instant_power)

    def getTPW_dailySolar(self):
        return(None)

    def getTPW_dailyConsumption(self):
        return(None)

    def getTPW_dailyGeneration(self):
        return(None)

    def getTPW_operationMode(self):
        EnumVal = -1
        operationVal = self.TPW.get_operation_mode()
        for key in self.operationEnum:
            if operationVal.value == self.operationEnum[key]:
                EnumVal = key
        return(EnumVal)
    
    def getTPW_running(self):
        return(self.status.is_running)   
    
    def getTPW_powerSupplyMode(self):
        return(self.status.status)   

    def getTPW_ConnectedTesla(self):
        return(self.status.is_connected_to_tesla)   
    
    def getTPW_gridServiceActive(self):
        return(self.TPW.is_grid_services_active())