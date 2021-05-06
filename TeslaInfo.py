#!/usr/bin/env python3
import requests
import json
import os 
from datetime import date
import time
from tesla_powerwall import Powerwall, GridStatus, OperationMode
from  ISYprofile import isyHandling
import polyinterface
LOGGER = polyinterface.LOGGER

class tesla_info:
    def __init__ (self, IPaddress, password, email, ISYname, ISY_Id):
        self.TEST = False
        LOGGER.debug('class tesla_info - init')
        self.TPW = Powerwall(IPaddress)
        self.TPW.login(password, email)
        self.controllerID = ISY_Id
        self.controllerName = ISYname

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
        self.ISYinfo = isyHandling()
        self.ISYvariables = {}
        self.ISYCritical = {}

        #self.ISYname
        self.TPW = Powerwall(IPaddress)
        self.TPW.login(password, email)
        if not(self.TPW.is_authenticated()):
            LOGGER.error('Error Logging into Tesla Power Wall')            
        else:        
            self.pollSystemData('all')
            self.ISYinfo.addISYnode(self.controllerID,self.controllerName,'Electricity' )
            
            self.ISYinfo.addISYcommandSend(self.controllerID, 'DON')
            self.ISYinfo.addISYcommandSend(self.controllerID, 'DOF')
            self.ISYinfo.addISYcommandReceive(self.controllerID, 'UPDATE', 'Update System Data', None)
            self.ISYinfo.addIsyVaraiable(self.chargeLevel, self.controllerID, 'percent', 0, 100, None, None, 1, 'Battery Charge Level', None )
            self.ISYinfo.addIsyVaraiable(self.backupLevel, self.controllerID, 'percent', 0, 100, None, None, 1, 'Battery Hold-off Level', None )       
            if self.TPW.get_solars() != None: # only add if solar exist - cannot test if this works as I have solar
                self.ISYinfo.addIsyVaraiable (self.solarSupply, self.controllerID, 'KW', 0, 20, None, None, 1, 'Current Solar Supply', None ) 
            self.ISYinfo.addIsyVaraiable (self.batterySupply, self.controllerID, 'KW', -20, 20, None, None, 1, 'Current Battery Supply', None ) 
            self.ISYinfo.addIsyVaraiable (self.gridSupply, self.controllerID, 'KW', -100, 100, None, None, 1, 'Current Grid Supply', None ) 
            self.ISYinfo.addIsyVaraiable (self.load, self.controllerID, 'KW', -100, 100, None, None, 1, 'Current Load', None ) 
            if self.TPW.get_solars() != None: # only add if solar exist - cannot test if this works as I have solar
                self.ISYinfo.addIsyVaraiable (self.dailySolar, self.controllerID, 'KW', 0, 1000, None, None, 1, 'Solar Power today', None ) 
            self.ISYinfo.addIsyVaraiable (self.dailyConsumption, self.controllerID, 'KW', 0, 1000, None, None, 1, 'Power Consumed today', None ) 
            self.ISYinfo.addIsyVaraiable (self.dailyGeneration, self.controllerID, 'KW', 0, 1000, None, None, 1, 'Net Power today', None ) 
            self.ISYinfo.addIsyVaraiable (self.gridStatus, self.controllerID, 'list', None, None, '0-3', None, None, 'Grid Status', self.gridStatusEnum ) 
            self.ISYinfo.addIsyVaraiable (self.operationMode, self.controllerID, 'list', None, None, '0-3', None, None, 'Operation Mode', self.operationEnum )                
            self.ISYCritical[self.controllerID].append(self.operationMode)
            self.ISYinfo.addIsyVaraiable (self.ConnectedTesla, self.controllerID, 'boolean', None,None, 0-1,None, None, 'Connected to Tesla', { 0:'False', 1: 'True' }) 
            self.ISYinfo.addIsyVaraiable (self.running, self.controllerID, 'boolean', None,None, 0-1,None, None, 'Power Wall Running', { 0:'False', 1: 'True' }) 
            self.ISYinfo.addIsyVaraiable (self.powerSupplyMode, self.controllerID, 'boolean', None,None, 0-1,None, None, 'Power Supply Mode', { 0:'False', 1: 'True' }) 
            self.ISYCritical[self.controllerID].append(self.powerSupplyMode)
            self.ISYinfo.addIsyVaraiable (self.gridServiceActive, self.controllerID, 'boolean', None,None, 0-1,None, None, 'Grid Services Active', { 0:'False', 1: 'True' }) 
            self.ISYinfo.addControllerDefStruct(self.controllerName, self.controllerID )
            self.ISYinfo.createSetupFiles('nodedefs.xml','editors.xml', 'en_us.txt')
            self.ISYmap = self.ISYinfo.createISYmapping()

    def createISYsetupfiles(self, nodeDefFile, editorFile, nlsFile):
            self.ISYinfo.createSetupFiles(nodeDefFile, editorFile, nlsFile)
            self.ISYmap = self.ISYinfo.createISYmapping()/profile/editor/editor

    def storeDailyData(self, filename, solar, consumption, generation, dayInfo ):
        try:
            if not(os.path.exists('./dailyData')):
                os.mkdir('./dailyData')
            dataFile = open('./dailyData/'+filename, 'a')
            dataFile.write('Date,'+str(dayInfo)+ ','+'solarKW,'+str(solar)+',ConsumptionKW,'+str(consumption)+',Generation,'+str(generation)+'\n')
            dataFile.close()
        except: 
            
            LOGGER.debug ('Failed to add data to '+str(filename))
        

    def getISYSendCommands(self, nodeId):
        LOGGER.debug('getISYSendCommands :' + str(nodeId))
        self.ISYinfo.getISYSendCommands(nodeId)
    
    def getISYReceiveCommands(self, nodeId,):
        LOGGER.debug('getISYReceiveCommands :' + str(nodeId))
        self.ISYinfo.getISYReceiveCommands(nodeId)

    def supportedParamters (self, nodeId):
        if nodeId in self.ISYmap:
            temp = self.ISYmap[nodeId]
        else:
            LOGGER.error('Unknown Node Id: ' + str(nodeId))
            temp = None
        return(temp)


    def criticalParamters (self, nodeId):
        return(self.ISYCritical)

    def pollSystemData(self, level):
        try:
            if level == 'critical':
                self.status = self.TPW.get_sitemaster() 
                return(True)
            if level == 'all':
                self.status = self.TPW.get_sitemaster() 
                self.meters = self.TPW.get_meters()
                if self.metersStart: 
                    self.metersDayStart = self.meters
                    self.lastDay = date.today() 
                    time.sleep(1)
                    self.metersStart = False
                self.nowDay = date.today() or self.TEST 
                if self.lastDay.day != self.nowDay.day: # we passed midnight
                    self.dailyTotalSolar =  self.getTPW_dailySolar()
                    self.dailyTotalConsumption = self.getTPW_dailyConsumption()
                    self.dailyTotalGeneraton = self.getTPW_dailyGeneration()
                    self.storeDailyData( 'dailydata.txt', self.dailyTotalSolar, self.dailyTotalConsumption, self.dailyTotalGeneraton, self.lastDay)
            
                    self.metersDayStart = self.meters
                self.lastDay = self.nowDay
                self.TEST = True
                return(True)
        except:
            LOGGER.error('problems extracting data from tesla power wall')
            if self.TPW.is_authenticated():
                LOGGER.error('Connected to Power Wall but error occured')
                return(False)
            else:
                try:
                    self.TPW.close()
                    self.TPW = Powerwall(IPaddress)
                    self.TPW.login(password, email)
                    if self.TPW.is_authenticated():
                        LOGGER.info('Reconnect to Tesla Power Wall Successful')
                        return(True)
                    else:
                        LOGGER.error('Reconnect to Tesla Power Wall Failed')
                        return(False)
                except:
                    LOGGER.error('Reconnect to Tesla Power Wall Failed')
                    return(False)
                    

    def getISYvalue(self, ISYvar, node):
        #LOGGER.debug( 'getISYvalue')
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
                LOGGER.error('Error - unknown variable: ' + str(self.teslaVarName )) 
                
        else:
            
            LOGGER.error('Error - unknown variable: ' + str(ISYvar)) 

    def setSendCommand(self, name, NodeId):
        
        LOGGER.debug('setSendCommand - Not implemented yet ')

    def setAcceptCommand(self, name, nodeId, TeslaVariable, ButtonText):
        
        LOGGER.debug('setAcceptCommand - Not implemented yet ')

    def setTeslaCredentials (self, IPaddress, password, email):
        self.IPaddress = IPaddress
        self.password = password
        self.email = email

    def getTPW_AvailableVars(self, nodeId):
        return(ISYvariables)

    def TPW_updateMeter(self):
        self.pollSystemData('all')
        return(None)

    def getTPW_chargeLevel(self):
        return(round(self.TPW.get_charge(),2))
        
    def getTPW_backupLevel(self):
        return(round(self.TPW.get_backup_reserve_percentage(),2))

    def getTPW_gridStatus(self):
        EnumVal = -1
        statusVal = self.TPW.get_grid_status()
        for key in self.gridStatusEnum:
            if statusVal.value == self.gridStatusEnum[key]:
                EnumVal = key
        return(EnumVal)

    def getTPW_solarSupply(self):
        return(round(self.meters.solar.instant_power/1000, 2))
    
    def getTPW_batterySupply(self):
        return(round(self.meters.battery.instant_power/1000, 2))

    def getTPW_gridSupply(self):
        return(round(self.meters.site.instant_power/1000, 2))

    def getTPW_load(self):
        return(round(self.meters.load.instant_power/1000, 2))

    def getTPW_dailySolar(self):
        return(round((self.meters.solar.energy_exported - self.metersDayStart.solar.energy_exported)/1000,2))

    def getTPW_dailyConsumption(self):
        return(round((self.meters.load.energy_imported - self.metersDayStart.load.energy_imported)/1000,2))


    def getTPW_dailyGeneration(self):  
        return(round((self.meters.site.energy_exported - self.metersDayStart.site.energy_exported - 
                      (self.meters.site.energy_imported - self.metersDayStart.site.energy_imported))/1000,2))


    def getTPW_operationMode(self):
        EnumVal = -1
        operationVal = self.TPW.get_operation_mode()
        for key in self.operationEnum:
            if operationVal.value == self.operationEnum[key]:
                EnumVal = key
        return(EnumVal)
    
    def getTPW_running(self):
        if self.status.is_running:  
           return(1)   
        else:
           return(0)
            
    def getTPW_powerSupplyMode(self):
        if self.status.is_power_supply_mode:
           return(1)   
        else:
           return(0)            

    def getTPW_ConnectedTesla(self):
        if self.status.is_connected_to_tesla:
            return(1)   
        else:
            return(0)

    def getTPW_gridServiceActive(self):
        if self.TPW.is_grid_services_active():
           return(1)   
        else:
           return(0)            

    def TPWdisconnect(self):
        self.TPW.close()