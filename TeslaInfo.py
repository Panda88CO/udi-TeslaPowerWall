#!/usr/bin/env python3

PG_CLOUD_ONLY = False

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    PG_CLOUD_ONLY = True
LOGGER = polyinterface.LOGGER



import requests
import json
import os 
from datetime import date
import time
from tesla_powerwall import Powerwall, GridStatus, OperationMode
from TeslaCloudAPI import TeslaCloudAPI
from ISYprofile import isyHandling


class tesla_info:
    def __init__ (self,  ISYname, ISY_Id, teslaConnection):
        self.TEST = False

        LOGGER.debug('class tesla_info - init')
        self.localPassword = ''
        self.localEmail = ''
        self.IPAddress = ''
        self.cloudEmail = ''
        self.cloudPassword = ''
        self.controllerID = ISY_Id
        self.controllerName = ISYname
        self.captchaMethod = ''
        self.captchaCode = ''
        self.captchaAPIKey = ''
        self.generatorInstalled  = True # I have not found a way to identify this on clould only connection so it will report even if not there
        self.solarInstalled = False
        self.ISYCritical = {}
        self.localAccessUp = False
        self.isyINFO = isyHandling()

        if teslaConnection == 'BOTH':
            self.TPWlocalAccess = True
            self.TPWcloudAccess = True
        elif teslaConnection == 'LOCAL':
            self.TPWlocalAccess = True
            self.TPWcloudAccess = False
        elif teslaConnection == 'CLOUD':
            self.TPWlocalAccess = False
            self.TPWcloudAccess = True
        else:
            self.TPWlocalAccess = False
            self.TPWcloudAccess = False
            LOGGER.debug('No connection specified')


    def loginLocal (self, email, password, IPaddress):
        self.localEmail = email
        self.localPassword = password
        self.IPAddress = IPaddress
        LOGGER.debug('Local Access Supported')
        self.lastDay = date.today()  

        self.TPWlocal = Powerwall(IPaddress)
        self.TPWlocal.login(self.localPassword, self.localEmail)
        if not(self.TPWlocal.is_authenticated()):            
            LOGGER.debug('Error Logging into Tesla Power Wall') 
            self.localAccessUp = False 
        else:
            self.localAccessUp = True
            self.metersDayStart = self.TPWlocal.get_meters()
            generator  = self.TPWlocal._api.get('generators')
            if not(generator['generators']):
                self.generatorInstalled = False
            else:
                self.generatorInstalled = True
            solar = self.TPWlocal.get_solars()
            if solar:
                self.solarInstalled = True
            else:
                self.solarInstalled = False


    def loginCloud(self, email, password, captchaMethod, captchaAPIkey = '' ):
        self.cloudEmail = email
        self.cloudPassword = password
        self.captchaMethod = captchaMethod
        self.captchaAPIKey = captchaAPIkey

        LOGGER.debug('Cloud Access Supported')
        self.TPWcloud = TeslaCloudAPI(self.cloudEmail, self.cloudPassword, self.captchaMethod)
        if self.captchaMethod == 'EMAIL':
            LOGGER.debug('sending email with captcha to email: ' + self.cloudEmail)
        else:
            LOGGER.debug('solving captcha automatically')
        self.TPWcloudAccess = True
           
    



    def teslaCloudConnect(self, captchaCode= '', captchaAPIKey = '',):
        LOGGER.debug('teslaCloudConnect')
        if not(self.TPWcloud.teslaCloudConnect(captchaCode, captchaAPIKey)):    
            LOGGER.debug('Error connecting to Tesla Could - check email, password')
            if self.captchaMethod == 'EMAIL':
                LOGGER.debug('Check email for new captcha -  may not have been correct.')
        else:
            LOGGER.debug('Logged in - retrieving data')
            self.TPWcloudAccess = True
            self.TPWcloud.teslaCloudInfo()
            self.TPWcloud.teslaRetrieveCloudData()
            self.solarInstalled = self.TPWcloud.teslaGetSolar()


    def teslaInitializeData(self):
        if not(self.TPWcloudAccess):
            LOGGER.debug ('no access to cloud data - starting accumulting from 0')
            self.yesterdayTotalSolar = 0
            self.yesterdayTotalConsumption = 0 
            self.yesterdayTotalGeneration  = 0 
            self.yesterdayTotalBattery =  0 
            self.yesterdayTotalGridServices = 0
            self.yesterdayTotalGenerator = 0
            self.daysTotalGridServices = 0 #Does not seem to exist
            self.daysTotalGenerator = 0 #needs to be updated - may not ex     
        else:
            self.TPWcloud.teslaUpdateCloudData('all')
            self.TPWcloud.teslaCalculateDaysTotals()
            self.daysTotalSolar = self.TPWcloud.teslaExtractDaysSolar()
            self.daysTotalConsumption = self.TPWcloud.teslaExtractDaysConsumption()
            self.daysTotalGeneraton = self.TPWcloud.teslaExtractDaysGeneration()
            self.daysTotalBattery = self.TPWcloud.teslaExtractDaysBattery()
            self.daysTotalGenerator = self.TPWcloud.teslaExtractDaysGeneratorUse()
            self.daysTotalGridServices = self.TPWcloud.teslaExtractDaysGridServicesUse()
            self.yesterdayTotalSolar = self.TPWcloud.teslaExtractYesteraySolar()
            self.yesterdayTotalConsumption = self.TPWcloud.teslaExtractYesterdayConsumption()
            self.yesterdayTotalGeneration  = self.TPWcloud.teslaExtractYesterdayGeneraton()
            self.yesterdayTotalBattery =  self.TPWcloud.teslaExtractYesterdayBattery() 
            self.yesterdayTotalGridServices = self.TPWcloud.teslaExtractYesterdayGridServiceUse()
            self.yesterdayTotalGenerator = self.TPWcloud.teslaExtractYesterdayGeneratorUse()

           
        #self.OPERATING_MODES = ["backup", "self_consumption", "autonomous"]
        #self.TOU_MODES = ["economics", "balanced"]
        self.metersStart = True
        self.gridstatus = {'on_grid':0, 'islanded_ready':1, 'islanded':2, 'transition ot grid':3}
        
        self.ISYgridEnum = {}
        for key in self.gridstatus:
            self.ISYgridEnum[self.gridstatus [key]]= key

        self.gridStatusEnum = {GridStatus.CONNECTED.value: 'on_grid', GridStatus.ISLANEDED_READY.value:'islanded_ready', GridStatus.ISLANEDED.value:'islanded', GridStatus.TRANSITION_TO_GRID.value:'transition ot grid' }
        self.operationLocalEnum =  {OperationMode.BACKUP.value:'backup',OperationMode.SELF_CONSUMPTION.value:'self_consumption', OperationMode.AUTONOMOUS.value:'autonomous', OperationMode.SITE_CONTROL.value: 'site_ctrl' }
        self.ISYoperationModeEnum = {'backup':0, 'self_consumption':1, 'autonomous':2, 'site_ctrl':3}

        self.operationCloudEnum = {}  

        if self.TPWcloudAccess:
            ModeList = self.TPWcloud.supportedOperatingModes()
            for i in range(0,len(ModeList)):
                self.operationCloudEnum[i]= ModeList[i] 
            ModeList = self.ISYoperationModeEnum

            for  key in ModeList:
                self.operationCloudEnum[ModeList[key]]= key
            
            ModeList = self.TPWcloud.supportedTouModes()
            self.touCloudEnum = {}
            self.ISYtouEnum = {}
            for i in range(0,len(ModeList)):
                self.touCloudEnum[i]= ModeList[i]
                self.ISYtouEnum[ModeList[i]] = i
        else:
            ModeList=None
        
        self.createISYsetup()
        self.pollSystemData('all')


    

    def createISYsetup (self):
        self.setupNodeID = 'pwsetup'
        self.setupNodeName = 'Control Parameters'

        self.nodeIDlist = [self.setupNodeID]
        self.chargeLevel = 'chargeLevel'
        self.backoffLevel = 'backoffLevel'
        self.gridStatus = 'gridStatus'
        self.solarSupply = 'solarSupply'
        self.batterySupply = 'batterySupply'     
        self.gridSupply = 'gridSupply'    
        self.load = 'load'   
        self.daysSolar = 'daysSolar'
        self.daysConsumption = 'daysConsumption'
        self.daysGeneration = 'daysGeneration'
        self.daysBattery = 'daysBattery'
        self.daysGridServices = 'daysGridServices'
        self.daysGenerator = 'daysGenerator'
        self.operationMode = 'operationMode' 

        self.ConnectedTesla = 'connectedTesla'


        self.running = 'running'
        self.powerSupplyMode = 'powerSupplyMode'
        self.gridServiceActive = 'gridServiceActive'

        self.stormMode = 'stormMode'
        self.touMode = 'touMode'
        #self.backupPercent = 'backup_percent'
        self.weekendOffPeakStartSec = 'weekendOffPeakStart'
        self.weekendOffPeakEndSec = 'weekendOffPeakStop'
        self.weekendPeakStartSec = 'weekendPeakStart'
        self.weekendPeakEndSec = 'weekendPeakStop'
        self.weekdayOffPeakStartSec = 'weekdayOffPeakStart'
        self.weekdayOffPeakEndSec = 'weekdayOffPeakStop'
        self.weekdayPeakStartSec = 'weekdayPeakStart'
        self.weekdayPeakEndSec = 'weekdayPeakStop'

        self.yesterdaySolar = 'yesterdaysSolar'
        self.yesterdayConsumption = 'yesterdayConsumption'
        self.yesterdayGeneration = 'yesterdayGeneration'
        self.yesterdayBattery = 'yesterdayBattery'
        self.yesterdayGridServices = 'yesterdayGridServices'
        self.yesterdayGenerator = 'yesterGenerator'

        self.isyINFO.addISYcontroller(self.controllerID, self.controllerName,'Electricity' )


        self.isyINFO.addISYcommandSend(self.controllerID, 'DON')
        self.isyINFO.addISYcommandSend(self.controllerID, 'DOF')
        self.isyINFO.addISYcommandReceive(self.controllerID, 'UPDATE', 'Update System Data', None)

        if self.solarInstalled or PG_CLOUD_ONLY: # only add if solar exist - cannot test if this works as intented, and I cannot remove solar (I have solar)
            self.isyINFO.addIsyVaraiable (self.controllerID, self.solarSupply, 'KWh', 0, 20, None, None, 2, 'Current Solar Supply', None ) 
            self.isyINFO.addIsyVaraiable (self.controllerID, self.daysSolar, 'KWh', - 100, 100, None, None, 2, 'Solar Power Today', None ) 
            self.isyINFO.addIsyVaraiable (self.controllerID,self.yesterdaySolar,  'KWh', -100, 100, None, None, 2, 'Solar Power Yesterday', None )


        self.isyINFO.addIsyVaraiable (self.controllerID, self.batterySupply, 'KWh', -20, 20, None, None, 2, 'Current Battery Supply', None ) 
        self.isyINFO.addIsyVaraiable (self.controllerID, self.daysBattery, 'KWh', -100, -100, None, None, 2, 'Battery Power Today', None ) 
        self.isyINFO.addIsyVaraiable (self.controllerID, self.yesterdayBattery, 'KWh', -100, 100, None, None, 2, 'Battery Power Yesterday', None ) 

        self.isyINFO.addIsyVaraiable (self.controllerID, self.gridSupply, 'KWh', -100, 100, None, None, 2, 'Current Grid Supply', None ) 
        self.isyINFO.addIsyVaraiable (self.controllerID, self.daysConsumption, 'KWh', -100, 100, None, None, 2, 'Power Consumed Today', None ) 
        self.isyINFO.addIsyVaraiable (self.controllerID, self.yesterdayConsumption, 'KWh', -100, 100, None, None, 2, 'Power Consumed Yesterday', None ) 

        self.isyINFO.addIsyVaraiable (self.controllerID, self.load, 'KWh', -100, 100, None, None, 1, 'Current Load', None ) 
        self.isyINFO.addIsyVaraiable (self.controllerID, self.daysGeneration, 'KWh', -100, 100, None, None, 2, 'Total Power Today', None ) 
        self.isyINFO.addIsyVaraiable (self.controllerID, self.yesterdayGeneration, 'KWh', -100, 100, None, None, 2, 'Total Power Yesterday', None ) 

        if self.TPWcloudAccess:
            self.isyINFO.addIsyVaraiable (self.controllerID, self.daysGridServices, 'KWh', -100, 100, None, None, 2, 'Grid Service Power Today', None ) 
            self.isyINFO.addIsyVaraiable (self.controllerID, self.yesterdayGridServices, 'KWh', -100, 100, None, None, 2, 'Grid Service Power Yesterday', None )   
            
        self.isyINFO.addIsyVaraiable(self.controllerID, self.chargeLevel, 'percent', 0, 100, None, None, 2, 'Battery Charge Level', None )


        if self.generatorInstalled and (self.TPWcloudAccess and not(self.TPWlocalAccess)) or (PG_CLOUD_ONLY): #I have no generator so I cannot test this if it 
            self.isyINFO.addIsyVaraiable (self.controllerID, self.daysGenerator, 'KWh', -100, 100, None, None, 2, 'Generator Power Today', None ) 
            self.isyINFO.addIsyVaraiable (self.controllerID, self.yesterdayGenerator, 'KWh', -100, 100, None, None, 2, 'Generator Power Yesterday', None ) 
        
        self.isyINFO.addIsyVaraiable (self.controllerID, self.gridStatus, 'list', None, None, '0-3', None, None, 'Grid Status', self.ISYgridEnum ) 

        self.isyINFO.addIsyVaraiable (self.controllerID, self.operationMode, 'list', None, None, '0-3', None, None, 'Operation Mode', self.ISYoperationModeEnum )                

        self.addISYCriticalParam(self.controllerID, self.operationMode)

        if self.TPWlocalAccess:
            self.isyINFO.addIsyVaraiable (self.controllerID, self.ConnectedTesla, 'list', None,None, '0-1',None, None, 'Connected to Tesla', { 0:'False', 1: 'True' }) 


        self.isyINFO.addIsyVaraiable (self.controllerID, self.gridServiceActive, 'list', None,None, '0-1',None, None, 'Grid Services Active', { 0:'False', 1: 'True' }) 
        self.isyINFO.addControllerDefStruct(self.controllerID, self.controllerName )

        if self.TPWcloudAccess:
            self.isyINFO.addISYnode(self.setupNodeID, self.setupNodeName, 'Electricity')

            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'BACKUP_PCT', 'Backup Reserve (%)', self.backoffLevel)
            self.isyINFO.addIsyVaraiable( self.setupNodeID, self.backoffLevel, 'percent', 0, 100, None, None, 1, 'Backup Reserve (%)', None ) 

            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'OP_MODE', 'Operating Mode', self.operationMode)
            self.isyINFO.addIsyVaraiable (self.setupNodeID, self.operationMode, 'list', None, None, '0-'+ str(len(self.ISYoperationModeEnum)-1), None, None, 'Operating Mode', self.ISYoperationModeEnum  ) 

            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'STORM_MODE', 'Set Storm Mode', self.stormMode)
            self.isyINFO.addIsyVaraiable( self.setupNodeID, self.stormMode,'list', None,None, '0-1',None, None, 'Storm Mode', { 0:'Disabled', 1: 'Enabled' }) 

            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'TOU_MODE', 'Time of Use Mode', self.touMode)
            self.isyINFO.addIsyVaraiable (self.setupNodeID, self.touMode,  'list', None, None, '0-'+ str(len(self.touCloudEnum)-1), None, None, 'Time of Use Mode', self.touCloudEnum  ) 
        
            self.isyINFO.addIsyVaraiable(self.setupNodeID, self.weekendOffPeakStartSec, 'durationSec', 0, 86400, None, None, 0, 'Weekend Off-peak Start time (sec)', None )
            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'WE_O_PEAK_START', 'Weekend Off-peak Start Time (sec)', self.weekendOffPeakStartSec)

            self.isyINFO.addIsyVaraiable(self.setupNodeID, self.weekendOffPeakEndSec, 'durationSec', 0, 86400, None, None, 0, 'Weekend Off-peak End time (sec)', None )
            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'WE_O_PEAK_END', 'Weekend Off-peak Stop Time (sec)', self.weekendOffPeakEndSec)

            self.isyINFO.addIsyVaraiable(self.setupNodeID, self.weekendPeakStartSec, 'durationSec', 0, 86400, None, None, 0, 'Weekend Peak Start Time (sec)', None )
            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'WE_PEAK_START', 'Weekend Peak Start Time (sec)', self.weekendPeakStartSec)

            self.isyINFO.addIsyVaraiable( self.setupNodeID, self.weekendPeakEndSec, 'durationSec', 0, 86400, None, None, 0, 'Weekend Peak End Time (sec)', None )
            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'WE_PEAK_END', 'Weekend Peak Stop Time (sec)', self.weekendPeakEndSec)

            self.isyINFO.addIsyVaraiable(self.setupNodeID, self.weekdayOffPeakStartSec, 'durationSec', 0, 86400, None, None, 0, 'Weekday Off-Peak Start Time (sec)', None )
            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'WK_O_PEAK_START', 'Weekday Off-peak Start Time (sec)', self.weekdayOffPeakStartSec)

            self.isyINFO.addIsyVaraiable(self.setupNodeID, self.weekdayOffPeakEndSec, 'durationSec', 0, 86400, None, None, 0, 'Weekday Off-peak End time (sec)', None )
            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'WK_O_PEAK_END', 'Weekday Off-peak Stop Time (sec)', self.weekdayOffPeakEndSec)

            self.isyINFO.addIsyVaraiable(self.setupNodeID, self.weekdayPeakStartSec, 'durationSec', 0, 86400, None, None, 0, 'Weekday Peak Start Time (sec)', None )
            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'WK_PEAK_START', 'Weekday Peak Start Time (sec)', self.weekdayPeakStartSec)

            self.isyINFO.addIsyVaraiable(self.setupNodeID, self.weekdayPeakEndSec, 'durationSec', 0, 86400, None, None, 0, 'Weekday Peak End Time (sec)', None )
            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'WK_PEAK_END', 'Weekday Peak Stop Time (sec)', self.weekdayPeakEndSec)
    
            self.isyINFO.addISYcommandReceive(self.setupNodeID, 'UPDATE', 'Update System Data', None)

            self.isyINFO.addNodeDefStruct(self.setupNodeID, self.setupNodeName)

        self.isyINFO.createSetupFiles('nodedefs.xml', 'editors.xml', 'en_us.txt')
        self.ISYmap = self.isyINFO.createISYmapping()

        

    def createISYsetupfiles(self, nodeDefFile, editorFile, nlsFile):
            self.isyINFO.createSetupFiles(nodeDefFile, editorFile, nlsFile)
            self.ISYmap = self.isyINFO.createISYmapping()

    def createLogFile(self, enabled):
        self.logFileEnabled = enabled


    def storeDaysData(self, filename, solar, consumption, generation, battery, gridUse, generator, dayInfo ):
        try:
            if not(os.path.exists('./dailyData')):
                os.mkdir('./dailyData')
                dataFile = open('./dailyData/'+filename, 'w+')
                dataFile.write('Date, solarKW, ConsumptionKW, GenerationKW, BatteryKW, GridServicesUseKW, GeneratorKW \n')
                dataFile.close()
            dataFile = open('./dailyData/'+filename, 'a')
            dataFile.write(str(dayInfo)+ ','+str(solar)+','+str(consumption)+','+str(generation)+','+str(battery)+','+str(gridUse)+','+str(generator)+'\n')
            dataFile.close()
        except Exception as e:
            LOGGER.debug('Exception storeDaysData: '+  str(e))         
            LOGGER.debug ('Failed to add data to '+str(filename))
        

    def getISYSendCommands(self, nodeId):
        LOGGER.debug('getISYSendCommands :' + str(nodeId))
        self.isyINFO.getISYSendCommands(nodeId)
    
    def getISYReceiveCommands(self, nodeId,):
        LOGGER.debug('getISYReceiveCommands :' + str(nodeId))
        self.isyINFO.getISYReceiveCommands(nodeId)

    def supportedParamters (self, nodeId):
        if nodeId in self.ISYmap:
            temp = self.ISYmap[nodeId]
        else:
            LOGGER.debug('Unknown Node Id: ' + str(nodeId))
            temp = None
        return(temp)

    def getNodeIdList(self):
        return(self.isyINFO.getISYnodeList())

    def getNodeName(self, nodeID):
        return(self.isyINFO.getISYNodeName(nodeID))

    def addISYCriticalParam(self, Id, value):
        if Id in self.ISYCritical:
            self.ISYCritical[Id].append(value)
        else:
            self.ISYCritical[Id] = []
            self.ISYCritical[Id].append(value)


    def criticalParamters (self, nodeId):
        temp = []
        if nodeId in self.ISYCritical:
            if self.ISYCritical[nodeId]:
                for key in self.ISYCritical[nodeId]:
                    temp.append(self.isyINFO.varToISY(nodeId, key))
            else:
                LOGGER.debug('No critical Params fpr  Node Id: ' + str(nodeId))
        else:
            LOGGER.debug('No critical Params fpr  Node Id: ' + str(nodeId))
        return(temp)
        #return(self.ISYCritical[nodeId])
    

    def pollSystemData(self, level):
        LOGGER.debug('PollSystemData - ' + str(level))

        try:
            self.nowDay = date.today() 
            if (self.lastDay.day != self.nowDay.day) or self.TEST: # we passed midnight
                if not(PG_CLOUD_ONLY) and self.logFileEnabled:
                    self.storeDaysData( 'dailydata.txt', self.daysTotalSolar, self.daysTotalConsumption, self.daysTotalGeneraton, self.daysTotalBattery, self.daysTotalGridServices, self.daysTotalGenerator , self.lastDay)
                self.yesterdayTotalSolar = self.daysTotalSolar
                self.yesterdayTotalConsumption = self.daysTotalConsumption
                self.yesterdayTotalGeneration  = self.daysTotalGeneraton
                self.yesterdayTotalBattery =  self.daysTotalBattery 
                self.yesterdayTotalGridServices = self.daysTotalGridServices
                self.yesterdayTotalGenerator = self.daysTotalGenerator
                if self.TPWlocalAccess:
                    self.metersDayStart = self.TPWlocal.get_meters()
                self.lastDay = self.nowDay


            if level == 'critical':
                if self.TPWcloudAccess:
                    LOGGER.debug('pollSystemData - CLOUD - critical')
                    self.TPWcloud.teslaUpdateCloudData('critical')

                if self.TPWlocalAccess:
                    LOGGER.debug('pollSystemData - local  CRITICAL - local connection = ' + str(self.localAccessUp))
                    if self.TPWlocal.is_authenticated():
                            self.localAccessUp = True
                            self.status = self.TPWlocal.get_sitemaster() 
                            self.meters = self.TPWlocal.get_meters()
                            #if self.getTPW_ConnectedTesla() and self.TPWcloudAccess:
                            #    self.TPWcloud.teslaUpdateCloudData('critical')
                            return(True)
                    else:
                        LOGGER.debug('No connection to Local Tesla Power Wall')
                        self.TPWlocal.logout()
                        time.sleep(1)
                        if self.loginLocal(self.localEmail, self.localPassword, self.IPAddress):
                            if self.TPWlocal.is_authenticated():
                                self.localAccessUp = True
                                self.status = self.TPWlocal.get_sitemaster() 
                                self.meters = self.TPWlocal.get_meters()                            
                                return(True)
                            else:
                                self.localAccessUp = False
                                return(False)
                            #LOGGER.debug('Exit poll SystemData Local')

            if level == 'all':
                if self.TPWlocalAccess:
                    LOGGER.debug('pollSystemData - local ALL - local connection = ' + str(self.localAccessUp))
                    if not(self.TPWlocal.is_authenticated()):
                        self.TPWlocal.logout()
                        time.sleep(1)
                        if self.loginLocal(self.localEmail, self.localPassword, self.IPAddress):
                            self.localAccessUp = True
                    if self.TPWlocal.is_authenticated():
                        self.localAccessUp = True
                        self.status = self.TPWlocal.get_sitemaster() 
                        self.meters = self.TPWlocal.get_meters()
                        self.daysTotalSolar =  (self.meters.solar.energy_exported - self.metersDayStart.solar.energy_exported)
                        self.daysTotalConsumption = (self.meters.load.energy_imported - self.metersDayStart.load.energy_imported)
                        self.daysTotalGeneraton = (self.meters.site.energy_exported - self.metersDayStart.site.energy_exported - 
                                                    (self.meters.site.energy_imported - self.metersDayStart.site.energy_imported))
                        self.daysTotalBattery =  (float(self.meters.battery.energy_exported - self.metersDayStart.battery.energy_exported - 
                                                    (self.meters.battery.energy_imported - self.metersDayStart.battery.energy_imported)))
                        if self.TPWcloudAccess:
                            self.daysTotalGenerator = self.TPWcloud.teslaExtractDaysGeneratorUse()
                            self.daysTotalGridServices = self.TPWcloud.teslaExtractDaysGridServicesUse()
                        else:
                            self.daysTotalGridServices = 0.0 #Does not seem to exist
                            self.daysTotalGenerator = 0.0 #needs to be updated - may not exist
                        LOGGER.debug('Local Access - total ')
                        return(True)
                    else:
                        LOGGER.debug('No connection to Local Tesla Power Wall')
                        self.localAccessUp = False
                        return(False)

                if self.TPWcloudAccess:
                    LOGGER.debug('pollSystemData - all')
                    self.TPWcloud.teslaUpdateCloudData('all')
                    self.TPWcloud.teslaCalculateDaysTotals()
                    self.daysTotalSolar = self.TPWcloud.teslaExtractDaysSolar()
                    self.daysTotalConsumption = self.TPWcloud.teslaExtractDaysConsumption()
                    self.daysTotalGeneraton = self.TPWcloud.teslaExtractDaysGeneration()
                    self.daysTotalBattery = self.TPWcloud.teslaExtractDaysBattery()
                    self.daysTotalGenerator = self.TPWcloud.teslaExtractDaysGeneratorUse()
                    self.daysTotalGridServices = self.TPWcloud.teslaExtractDaysGridServicesUse()
                    self.yesterdayTotalSolar = self.TPWcloud.teslaExtractYesteraySolar()
                    self.yesterdayTotalConsumption = self.TPWcloud.teslaExtractYesterdayConsumption()
                    self.yesterdayTotalGeneration  = self.TPWcloud.teslaExtractYesterdayGeneraton()
                    self.yesterdayTotalBattery =  self.TPWcloud.teslaExtractYesterdayBattery() 
                    self.yesterdayTotalGridServices = self.TPWcloud.teslaExtractYesterdayGridServiceUse()
                    self.yesterdayTotalGenerator = self.TPWcloud.teslaExtractYesterdayGeneratorUse()            

            return(True)

        except Exception as e:
            LOGGER.debug('Exception PollSystemData: '+  str(e))
            LOGGER.debug('problems extracting data from tesla power wall')
            # NEED To logout and log back in locally
            # Need to retrieve/renew token from cloud

        
    def getISYvalue(self, ISYvar, node):
        LOGGER.debug( 'getISYvalue - ' + str(node))
        if ISYvar in self.ISYmap[node]:
            self.teslaVarName = self.ISYmap[node][ISYvar]['systemVar']
            if self.teslaVarName == self.chargeLevel: 
                return(self.getTPW_chargeLevel())
            elif self.teslaVarName == self.backoffLevel: 
                return(self.getTPW_backoffLevel())
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
            elif self.teslaVarName == self.daysSolar:
                return(self.getTPW_daysSolar())
            elif self.teslaVarName == self.daysConsumption:
                return(self.getTPW_daysConsumption())
            elif self.teslaVarName == self.daysGeneration:
                return(self.getTPW_daysGeneration())        
            elif self.teslaVarName == self.daysBattery:
                return(self.getTPW_daysBattery())
            elif self.teslaVarName == self.daysGridServices:
                return(self.getTPW_daysGridServicesUse())      
            elif self.teslaVarName == self.daysGenerator:
                return(self.getTPW_daysGeneratorUse())      
            elif self.teslaVarName == self.operationMode:
                return(self.getTPW_operationMode())
            elif self.teslaVarName == self.powerSupplyMode:
                return(self.getTPW_powerSupplyMode())
            elif self.teslaVarName == self.gridServiceActive:
                return(self.getTPW_gridServiceActive())
            elif self.teslaVarName == self.stormMode:
                return(self.getTPW_stormMode())
            elif self.teslaVarName == self.touMode:
                return(self.getTPW_touMode())
            elif self.teslaVarName == self.daysBattery:
                return(self.getTPW_daysBattery())
            elif self.teslaVarName == self.daysGridServices:
                return(self.getTPW_daysGridServicesUse())
            elif self.teslaVarName == self.ConnectedTesla:
                return(self.getTPW_ConnectedTesla())               
            elif self.teslaVarName == self.yesterdaySolar:
                return(self.getTPW_yesterdaySolar())
            elif self.teslaVarName == self.yesterdayConsumption:
                return(self.getTPW_yesterdayConsumption())           
            elif self.teslaVarName == self.yesterdayGeneration:
                return(self.getTPW_yesterdayConsumption())
            elif self.teslaVarName == self.yesterdayBattery:
                return(self.getTPW_yesterdayBattery())                
            elif self.teslaVarName == self.yesterdayGridServices:
                return(self.getTPW_yesterdayGridServicesUse())
            elif self.teslaVarName == self.yesterdayGenerator:
                return(self.getTPW_yesterdayGeneratorUse())                                
            elif self.teslaVarName == self.weekendOffPeakStartSec:
                return(self.getTPW_getTouData('weekend', 'off_peak', 'start'))     
            elif self.teslaVarName == self.weekendOffPeakEndSec:
                return(self.getTPW_getTouData('weekend', 'off_peak', 'stop'))   
            elif self.teslaVarName == self.weekendPeakStartSec:
                return(self.getTPW_getTouData('weekend', 'peak', 'start'))   
            elif self.teslaVarName == self.weekendPeakEndSec:
                return(self.getTPW_getTouData('weekend', 'peak', 'stop'))   
            elif self.teslaVarName == self.weekdayOffPeakStartSec:
                return(self.getTPW_getTouData('weekday', 'off_peak', 'start'))   
            elif self.teslaVarName == self.weekdayOffPeakEndSec:
                return(self.getTPW_getTouData('weekday', 'off_peak', 'stop'))   
            elif self.teslaVarName == self.weekdayPeakStartSec:
                return(self.getTPW_getTouData('weekday', 'peak', 'start'))   
            elif self.teslaVarName == self.weekdayPeakEndSec:
                return(self.getTPW_getTouData('weekday', 'peak', 'stop'))   
            else:

                LOGGER.debug('Error - unknown variable: ' + str(self.teslaVarName )) 
           
        else:    
            LOGGER.debug('Error - unknown variable: ' + str(ISYvar)) 


    def TPW_updateMeter(self):
        self.pollSystemData('all')
        return(None)

    def getTPW_chargeLevel(self):
 
        if self.TPWlocalAccess:
            chargeLevel = self.TPWlocal.get_charge()
        else:
            chargeLevel = self.TPWcloud.teslaExtractChargeLevel()
        LOGGER.debug('\n getTPW_chargeLevel' + str(chargeLevel))
        return(round(chargeLevel,1))


    def getTPW_backoffLevel(self):
        if self.TPWlocalAccess:
            backoffLevel=self.TPWlocal.get_backup_reserve_percentage()
        else:
            backoffLevel=self.TPWcloud.teslaExtractBackoffLevel()
        LOGGER.debug('\n getTPW_backoffLevel' + str(backoffLevel))
        return(round(backoffLevel,1))

    def getBackupPercentISYVar(self, node):
        return(self.isyINFO.varToISY(node, self.backoffLevel))


    def setTPW_backoffLevel(self, backupPercent):
        return(self.TPWcloud.teslaSetBackoffLevel(backupPercent))

    def getTPW_gridStatus(self):
        if self.TPWlocalAccess:
            statusVal = self.TPWlocal.get_grid_status()
            if statusVal.value in self.gridStatusEnum:
                key = self.gridStatusEnum[statusVal.value ]
                LOGGER.debug(key)
        else:
            key = self.TPWcloud.teslaExtractGridStatus()
        LOGGER.debug('\ngrid status '+str(self.gridstatus[key]))
        return(self.gridstatus[key])


    def getTPW_solarSupply(self):
        
        if self.TPWlocalAccess:
            LOGGER.debug(self.meters)
            solarPwr = self.meters.solar.instant_power
        else:
            solarPwr = self.TPWcloud.teslaExtractSolarSupply()
        LOGGER.debug('getTPW_solarSupply - ' + str(solarPwr))
        return(round(solarPwr/1000,2))
        #site_live

    def getTPW_batterySupply(self):
        if self.TPWlocalAccess:
            batteryPwr = self.meters.battery.instant_power
        else:
            batteryPwr = self.TPWcloud.teslaExtractBatterySupply()
        LOGGER.debug('\ngetTPW_batterySupply' + str(batteryPwr))
        return(round(batteryPwr/1000,2))
 


        #site_live
    def getTPW_gridSupply(self):
        if self.TPWlocalAccess:
            gridPwr = self.meters.site.instant_power
        else:
            gridPwr = self.TPWcloud.teslaExtractGridSupply()
        LOGGER.debug('\n getTPW_gridSupply'+ str(gridPwr))            
        return(round(gridPwr/1000,2))


    def getTPW_load(self):
        if self.TPWlocalAccess:
            loadPwr = self.meters.load.instant_power
        else:
            loadPwr = self.TPWcloud.teslaExtractLoad()
        LOGGER.debug('\n getTPW_load ' + str(loadPwr))
        return(round(loadPwr/1000,2))


    def getTPW_daysSolar(self):
        if self.TPWlocalAccess:
            Pwr = self.daysTotalSolar
        else:
            Pwr = self.TPWcloud.teslaExtractDaysSolar()
        LOGGER.debug('\n getTPW_daysSolar ' + str(Pwr))
        return(round(Pwr/1000,2))


    def getTPW_daysConsumption(self):
        if self.TPWlocalAccess:
            Pwr = self.daysTotalConsumption
        else:
            Pwr = self.TPWcloud.teslaExtractDaysConsumption()
            LOGGER.debug('\n getTPW_daysConsumption ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_daysGeneration(self):  
        if self.TPWlocalAccess:
            Pwr = self.daysTotalGeneraton
        else:
            Pwr = self.TPWcloud.teslaExtractDaysGeneration()
        LOGGER.debug('\n getTPW_daysGeneration ' + str(Pwr))        
        return(round(Pwr/1000,2))

    def getTPW_daysBattery(self):  
        if self.TPWlocalAccess:
            Pwr = self.daysTotalBattery
        else:
            Pwr = self.TPWcloud.teslaExtractDaysBattery()
        LOGGER.debug('\n getTPW_daysBattery ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_daysGridServicesUse(self):  
        if self.TPWlocalAccess:
            Pwr = self.daysTotalGridServices
        else:
            Pwr = self.TPWcloud.teslaExtractDaysGridServicesUse()
        LOGGER.debug('\n getTPW_daysGridServicesUse ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_daysGeneratorUse(self):  
        if self.TPWlocalAccess:
            Pwr = self.daysTotalGenerator
        else:
            Pwr = self.TPWcloud.teslaExtractDaysGeneratorUse()
        LOGGER.debug('\n getTPW_daysGeneratorUse ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_yesterdaySolar(self):
        if self.TPWlocalAccess:
            Pwr = self.yesterdayTotalSolar
        else:
            Pwr = self.TPWcloud.teslaExtractYesteraySolar()
        LOGGER.debug('\n getTPW_daysSolar ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_yesterdayConsumption(self):
        if self.TPWlocalAccess:
            Pwr = self.yesterdayTotalConsumption
        else:
            Pwr = self.TPWcloud.teslaExtractYesterdayConsumption()
        LOGGER.debug('\n getTPW_daysConsumption ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_yesterdayGeneration(self):  
        if self.TPWlocalAccess:
            Pwr = self.yesterdayTotalGeneration
        else:
            Pwr = self.TPWcloud.teslaExtractYesterdayGeneraton()
        LOGGER.debug('\n getTPW_daysGeneration ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_yesterdayBattery(self):  

        if self.TPWlocalAccess:
            Pwr = self.yesterdayTotalBattery
        else:
            Pwr = self.TPWcloud.teslaExtractYesterdayBattery()
        LOGGER.debug('\n getTPW_daysBattery ' + str(Pwr))
        return(round(Pwr/1000,2))


    def getTPW_yesterdayGridServicesUse(self):  

        if self.TPWlocalAccess:
            Pwr = self.yesterdayTotalGridServices
        else:
            Pwr = self.TPWcloud.teslaExtractYesterdayGridServiceUse()
        LOGGER.debug('\n getTPW_daysGridServicesUse ' + str(Pwr))            
        return(round(Pwr/1000,2))
        #bat_history

    def getTPW_yesterdayGeneratorUse(self):  

        if self.TPWlocalAccess:
            Pwr = self.yesterdayTotalGenerator
        else:
            Pwr = self.TPWcloud.teslaExtractYesterdayGeneratorUse()
        LOGGER.debug('\n getTPW_daysGeneratorUse ' + str(Pwr))
        return(round(Pwr/1000,2))
        #bat_history


    def getTPW_operationMode(self):
        if self.TPWlocalAccess:
            operationVal = self.TPWlocal.get_operation_mode()
            key = self.operationLocalEnum[operationVal.value]
        else:
            key = self.TPWcloud.teslaExtractOperationMode()

        return( self.ISYoperationModeEnum [key])
    
    def getOperatingModeISYVar(self, node):
        return(self.isyINFO.varToISY(node, self.operationMode))

    def setTPW_operationMode(self, index):
        return(self.TPWcloud.teslaSetOperationMode(self.operationCloudEnum[index]))

    ''' 
    def getTPW_running(self):
        if self.status.is_running:  
           return(1)   
        else:
           return(0)
    '''

    def getTPW_powerSupplyMode(self):
        if self.status.is_power_supply_mode:
           return(1)   
        else:
           return(0)            
    
    def getTPW_ConnectedTesla(self):  # can check other direction 
        if self.status.is_connected_to_tesla:
            return(1)   
        else:
            return(0)


    def getTPW_gridServiceActive(self):
        if self.TPWlocalAccess:
            res = self.TPWlocal.is_grid_services_active()   
        else:
            res = self.TPWcloud.teslaExtractGridServiceActive()
        if res:
            return(1)
        else:
            return (0)


    def getTPW_stormMode(self):
        if self.TPWcloudAccess:
            if self.TPWcloud.teslaExtractStormMode():
                return (1)
            else:
                return(0)

    def getStormModeISYVar(self, node):
        return(self.isyINFO.varToISY(node, self.stormMode))

    def setTPW_stormMode(self, mode):
        return(self.TPWcloud.teslaSetStormMode(mode==1))

    def getTPW_touMode(self):
        if self.TPWcloudAccess:
            return(self.ISYtouEnum[self.TPWcloud.teslaExtractTouMode()])        


    def getTOUmodeISYVar(self, node):
        return(self.isyINFO.varToISY(node, self.touMode))            

    def getTPW_touSchedule(self):
        if self.TPWcloudAccess:        
            return(self.TPWcloud.teslaExtractTouScheduleList())


    def setTPW_touMode(self, index):
        if self.TPWcloudAccess:        
            return(self.TPWcloud.teslaSetTimeOfUseMode(self.touCloudEnum[index]))


    def setTPW_touSchedule(self, peakOffpeak, weekWeekend, startEnd, time_s):
        if self.TPWcloudAccess:        
            return(self.TPWcloud.teslaSetTouSchedule( peakOffpeak, weekWeekend, startEnd, time_s))

    def setTPW_updateTouSchedule(self, peakOffpeak, weekWeekend, startEnd, time_s):
        if self.TPWcloudAccess:        
            return(self.TPWcloud.teslaSetTouSchedule( peakOffpeak, weekWeekend, startEnd, time_s))

    def getTPW_getTouData(self, days, peakMode, startEnd ):
        if self.TPWcloudAccess:        
            return(self.TPWcloud.teslaExtractTouTime(days, peakMode, startEnd ))

    def getTouWeekendOffpeakStartISYVar(self, node):
        if self.TPWcloudAccess:        
            return(self.isyINFO.varToISY(node, self.weekendOffPeakStartSec))

    def getTouWeekendOffpeakEndISYVar(self, node):
        if self.TPWcloudAccess:        
            return(self.isyINFO.varToISY(node, self.weekendOffPeakEndSec))    

    def getTouWeekendPeakStartISYVar(self, node):
        if self.TPWcloudAccess:        
            return(self.isyINFO.varToISY(node, self.weekendPeakStartSec))

    def getTouWeekendPeakEndISYVar(self, node):
        if self.TPWcloudAccess:        
            return(self.isyINFO.varToISY(node, self.weekendPeakEndSec))    

    def getTouWeekOffpeakStartISYVar(self, node):
        if self.TPWcloudAccess:        
            return(self.isyINFO.varToISY(node, self.weekdayOffPeakStartSec))

    def getTouWeekOffpeakEndISYVar(self, node):
        if self.TPWcloudAccess:        
            return(self.isyINFO.varToISY(node, self.weekdayOffPeakEndSec))    

    def getTouWeekPeakStartISYVar(self, node):
        if self.TPWcloudAccess:        
            return(self.isyINFO.varToISY(node, self.weekdayPeakStartSec))

    def getTouWeekPeakEndISYVar(self, node):
        if self.TPWcloudAccess:        
            return(self.isyINFO.varToISY(node, self.weekdayPeakEndSec))    


    def disconnectTPW(self):
        if self.TPWlocalAccess:
            self.TPWlocal.close()

