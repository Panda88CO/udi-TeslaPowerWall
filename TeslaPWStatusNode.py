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

LOGGER = polyinterface.LOGGER
               
class teslaPWStatusNode(polyinterface.Node):

    def __init__(self, controller, primary, address, name):
        super().__init__(controller, primary, address, name)

        LOGGER.info('_init_ Tesla Power Wall Status NOde')
        self.ISYforced = False
        self.TPW = self.parent.TPW
        self.address = address 
        self.id = address
        self.name = name
        self.hb = 0

        if not(PG_CLOUD_ONLY):
             self.drivers = []

        self.nodeDefineDone = False
        LOGGER.debug('Start Tesla Power Wall Status Node')  

        self.ISYparams = self.TPW.supportedParamters(self.id)
        #LOGGER.debug ('Node = ISYparams :' + str(self.ISYparams))

        self.ISYcriticalParams = self.TPW.criticalParamters(self.id)
        #LOGGER.debug ('Node = ISYcriticalParams :' + str(self.ISYcriticalParams))
    

        for key in self.ISYparams:
            info = self.ISYparams[key]
            #LOGGER.debug(key )
            if info != {}:
                value = self.TPW.getISYvalue(key, self.id)
                LOGGER.debug('StatusNode: driver' + str(key)+ ' value:' + str(value) + ' uom:' + str(info['uom']) )
                self.drivers.append({'driver':key, 'value':value, 'uom':info['uom'] })



    def start(self):                
        self.updateISYdrivers('all')
        #self.reportDrivers()
        self.nodeDefineDone = True


    def stop(self):
        LOGGER.debug('stop - Cleaning up')
    
    def shortPoll(self):
        #No need to poll data - done by Controller
        LOGGER.debug('Tesla Power Wall Status Node shortPoll')
        if self.nodeDefineDone:
            self.updateISYdrivers('critical')
        else:
           LOGGER.info('Status Node: waiting for system/nodes to get created')

                

    def longPoll(self):
        #No need to poll data - done by Controller
        LOGGER.debug('Tesla Power Wall  status Node longPoll')
        if self.nodeDefineDone:
           self.updateISYdrivers('all')
           #self.reportDrivers() 
        else:
           LOGGER.info('Status Node: waiting for system/nodes to get created')

    def updateISYdrivers(self, level):
        LOGGER.debug('Node updateISYdrivers')
        params = []
        if level == 'all':
            params = self.ISYparams
            if params:
                for key in params:
                    info = params[key]
                    if info != {}:
                        value = self.TPW.getISYvalue(key, self.id)
                        #LOGGER.debug('Update ISY drivers :' + str(key)+ ' ' + info['systemVar']+ ' value:' + str(value) )
                        self.setDriver(key, value, report = True, force = True)      
        elif level == 'critical':
            params = self.ISYcriticalParams
            if params:
                for key in params:
                    value = self.TPW.getISYvalue(key, self.id)
                    #LOGGER.debug('Update ISY drivers :' + str(key)+ ' value: ' + str(value) )
                    self.setDriver(key, value, report = True, force = True)        

        else:
           LOGGER.debug('Wrong parameter passed: ' + str(level))
  





    def ISYupdate (self, command):
        LOGGER.debug('ISY-update called')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            #self.reportDrivers()
 

    commands = { 'UPDATE': ISYupdate, 
                }


