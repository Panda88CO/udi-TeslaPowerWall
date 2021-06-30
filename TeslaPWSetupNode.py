#!/usr/bin/env python3
PG_CLOUD_ONLY = False

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface

    PG_CLOUD_ONLY = True

#from os import truncate
import sys
import TeslaInfo
import ISYprofile

import polyinterface
LOGGER = polyinterface.LOGGER
               
class teslaPWSetupNode(polyinterface.Node):

    def __init__(self, controller, primary, address, name):
        super().__init__(controller, primary, address, name)

        LOGGER.debug('_init_ Tesla Power Wall Controller')
        self.ISYforced = False
        self.TPW = self.parent.TPW
        self.address = address 
        self.id = address
        self.name = name
        self.hb = 0

        self.drivers = []
        self.nodeDefineDone = False
        LOGGER.debug('Start Tesla Power Wall Setup Node')  
        self.ISYparams = self.TPW.supportedParamters(self.id)
        self.ISYcriticalParams = self.TPW.criticalParamters(self.id)
        for key in self.ISYparams:
            info = self.ISYparams[key]
            LOGGER.debug(key )
            if info != {}:
                value = self.TPW.getISYvalue(key, self.id)
                self.drivers.append({'driver':key, 'value':value, 'uom':info['uom'] })
                LOGGER.debug('SetupNode: driver' + str(key)+ ' value:' + str(value) + ' uom:' + str(info['uom']) )

        self.heartbeat()


    def start(self):                
        self.updateISYdrivers('all')
        self.reportDrivers()
        self.discover()
        self.nodeDefineDone = True

        #except:
        #    LOGGER.error('Did not connect to power wall')
        #    self.disconnectTPW()
        #    self.stop()

        


    def stop(self):
        LOGGER.debug('stop - Cleaning up')

    def heartbeat(self):
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd('DON',2)
            self.hb = 1
        else:
            self.reportCmd('DOF',2)
            self.hb = 0

    
    def shortPoll(self):
        LOGGER.debug('Tesla Power Wall Controller shortPoll')
        if self.nodeDefineDone:
            self.heartbeat()
            self.updateISYdrivers('critical')
        else:
           LOGGER.debug('waiting for system/nodes to get created')

                

    def longPoll(self):
        LOGGER.debug('Tesla Power Wall  Controller longPoll - heat beat')
        if self.nodeDefineDone:
           self.updateISYdrivers('all')
           self.reportDrivers() 
        else:
           LOGGER.debug('waiting for system/nodes to get created')

    def updateISYdrivers(self, level):
        LOGGER.debug('Node updateISYdrivers')
        params = []
        if level == 'all':
            params = self.ISYparams
        elif level == 'critical':
            params = self.ISYparams
        else:
           LOGGER.debug('Wrong parameter passed: ' + str(level))
        for key in params:
            info = params[key]
            if info != {}:
                value = self.TPW.getISYvalue(key, self.id)
                #LOGGER.debug('Update ISY drivers :' + str(key)+ ' ' + info['systemVar']+ ' value:' + str(value) )
                self.setDriver(key, value, report = True, force = False)          

    '''
    def query(self, command=None):
       LOGGER.debug('TOP querry')
        self.updateISYdrivers(ll''a)
        self.reportDrivers('all')
    '''

    def discover(self, command=None):
        #LOGGER.debug('discover zones')
        self.nodeDefineDone = True

    def setStormMode(self, command):
        LOGGER.debug('setStormMode')
        value = int(command.get('value'))
        self.TPW.setTPW_stormMode(value)
        ISYvar = self.TPW.getStormModeISYVar(self.id)
        self.setDriver(ISYvar, value, report = True,force = True)
        self.reportDrivers() 
        
    def setOperatingMode(self, command):
        LOGGER.debug('setOperatingMode')
        value = int(command.get('value'))
        self.TPW.setTPW_operationMode(value)
        ISYvar = self.TPW.getOperatingModeISYVar(self.id)
        self.setDriver(ISYvar, value, report = True,force = True)
        self.reportDrivers() 
    
    def setBackupPercent(self, command):
        LOGGER.debug('setBackupPercent')
        value = float(command.get('value'))
        self.TPW.setTPW_backoffLevel(value)
        ISYvar = self.TPW.getBackupPercentISYVar(self.id)
        self.setDriver(ISYvar, value, report = True,force = True)
        self.reportDrivers() 

    def setTOUmode(self, command):
        LOGGER.debug('setTOUmode')
        value = int(command.get('value'))
        self.TPW.setTPW_touMode(value)
        ISYvar = self.TPW.getTOUmodeISYVar(self.id)
        self.setDriver(ISYvar, value, report = True,force = True)
        self.reportDrivers() 

    def setWeekendOffpeakStart(self, command):
        LOGGER.debug('setWeekendOffpeakStart')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('off_peak', 'weekend', 'start', value)
        ISYvar = self.TPW.getTouWeekendOffpeakStartISYVar(self.id)
        self.setDriver(ISYvar, value, report = True,force = True)
        self.reportDrivers() 

    def setWeekendOffpeakEnd(self, command):
        LOGGER.debug('setWeekendOffpeakEnd')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('off_peak', 'weekend', 'end', value)
        ISYvar = self.TPW.getTouWeekendOffpeakEndISYVar(self.id)
        self.setDriver(ISYvar, value, report = True,force = True)
        self.reportDrivers() 

    def setWeekendPeakStart(self, command):
        LOGGER.debug('setWeekendPeakStart')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('peak', 'weekend', 'start', value)
        ISYvar = self.TPW.getTouWeekendPeakStartISYVar(self.id)
        self.setDriver(ISYvar, value, report = True,force = True)
        self.reportDrivers()       

    def setWeekendPeakEnd(self, command):
        LOGGER.debug('setWeekendPeakEnd')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('peak', 'weekend', 'end', value)
        ISYvar = self.TPW.getTouWeekendPeakEndISYVar(self.id)
        self.setDriver(ISYvar, value, report = True,force = True)
        self.reportDrivers()    

    def setWeekOffpeakStart(self, command):
        LOGGER.debug('setWeekOffpeakStart')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('off_peak', 'week', 'start', value)
        ISYvar = self.TPW.getTouWeekOffpeakStartISYVar(self.id)
        self.setDriver(ISYvar, value, report = True,force = True)
        self.reportDrivers() 

    def setWeekOffpeakEnd(self, command):
        LOGGER.debug('setWeekOffpeakEnd')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('off_peak', 'week', 'end', value)
        ISYvar = self.TPW.getTouWeekOffpeakEndISYVar(self.id)
        self.setDriver(ISYvar, value, report = True,force = True)
        self.reportDrivers() 

    def setWeekPeakStart(self, command):
        LOGGER.debug('setWeekPeakStart')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('peak', 'week', 'start', value)
        ISYvar = self.TPW.getTouWeekPeakStartISYVar(self.id)
        self.setDriver(ISYvar, value, report = True,force = True)
        self.reportDrivers()   

    def setWeekPeakEnd(self, command):
        LOGGER.debug('setWeekPeakEnd')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('peak', 'week', 'end', value)
        ISYvar = self.TPW.getTouWeekPeakEndISYVar(self.id)
        self.setDriver(ISYvar, value, report = True,force = True)
        self.reportDrivers() 


    def ISYupdate (self, command):
        LOGGER.debug('ISY-update called')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            self.reportDrivers()
 

    commands = { 'UPDATE': ISYupdate
                ,'BACKUP_PCT' : setBackupPercent
                ,'STORM_MODE' :setStormMode
                ,'OP_MODE': setOperatingMode
                ,'TOU_MODE':setTOUmode
                ,'WE_O_PEAK_START': setWeekendOffpeakStart
                ,'WE_O_PEAK_END':setWeekendOffpeakEnd
                ,'WE_PEAK_START':setWeekendPeakStart
                ,'WE_PEAK_END':setWeekendPeakEnd
                ,'WK_O_PEAK_START':setWeekOffpeakStart
                ,'WK_O_PEAK_END':setWeekOffpeakEnd
                ,'WK_PEAK_START':setWeekPeakStart
                ,'WK_PEAK_END':setWeekPeakEnd

                }
