#!/usr/bin/env python3

import sys
import polyinterface
LOGGER = polyinterface.LOGGER
from TeslaInfo import tesla_info
#from  ISYprofile import isyProfile


LOGGER = polyinterface.LOGGER
               
class TeslaPWController(polyinterface.Controller):

    def __init__(self, controllerName):
        super(TeslaPWController, self).__init__(polyglot)
        LOGGER.info('_init_ Tesla Power Wall Controller')
        self.ISYforced = False
        self.name = 'Tesla Power Wall'
        self.address ='teslapw'
        self.id = self.address
        #LOGGER.debug('Name/address: '+ self.name + ' ' + self.address)
        self.primary = self.address
        self.hb = 0
        self.drivers = []
        self.nodeDefineDone = False



    def defineInputParams(self):
        self.IPAddress = self.getCustomParam('IP_ADDRESS')
        if self.IPAddress is None:
            self.addNotice('Please Set IP address of Tesla Power Wall system (IP_ADDRESS)')
            self.addNotice('E.g. 192.168.1.2')
            LOGGER.error('IP address not set')
            self.addCustomParam({'IP_ADDRESS': '192.168.1.2'})


        self.UserEmail = self.getCustomParam('USER_EMAIL')
        if self.UserEmail is None:
            self.addNotice('Please Set Tesla Power Wall login email (USER_EMAIL)')
            self.addNotice('E.g. nobody@email.com')
            LOGGER.error('check_params: user email not specified')
            self.addCustomParam({'USER_EMAIL': 'nobody@email.com'})

        self.UserPassword= self.getCustomParam('USER_PASSWORD')
        if self.UserEmail is None:
            self.addNotice('Please Set Tesla Power Wall password (USER_PASSWORD)')
            self.addNotice('E.g. XXXXXXXX')
            LOGGER.error('check_params: user password not specified')
            self.addCustomParam({'USER_PASSWORD': 'XXXXXXXX'})

        self.addNotice('Please restart Node server after setting the parameters')



    def start(self):
        self.removeNoticesAll()
        LOGGER.info('Start Messana Main NEW')
        self.IPAddress = self.getCustomParam('IP_ADDRESS')
        if self.IPAddress == None:
            LOGGER.error('No IPaddress retrieved:' )
        else:
            LOGGER.debug('IPaddress retrieved: ' + self.IPAddress)
        self.UserEmail = self.getCustomParam('USER_EMAIL')
        if self.UserEmail == None:
            LOGGER.error('No USER_EMAILretrieved:')
        else:
            LOGGER.debug('USER_EMAIL retrieved: '+ self.UserEmail)
        self.UserPassword =self.getCustomParam('USER_PASSWORD')
        if self.UserPassword == None:
            LOGGER.error('No USER_PASSWORD:')
        else:
            LOGGER.debug('USER_PASSWORD retrieved: XXXXXXXX')

        if (self.IPAddress is None) or (self.UserEmail is None) or(self.UserPassword is None)  :
            self.defineInputParams()
            self.stop()

        else:
            LOGGER.info('Connecting to Tesla Power Wall')
            TPW = tesla_info(self.IPAddress, self.UserPassword, self.UserEmail, self.name, self.id )
            LOGGER.debug ('Install Profile')    
            self.poly.installprofile()
            self.ISYparams = TPW.supportedParamters(self.id)
            for key in self.ISYparams:
                info = self.ISYparams[key]
                if info != {}:
                    val = TPW.getISYValue(key, self.id)
                    self.drivers.append({'driver':key, 'value':value, 'uom':info['uom'] })
                    self.setDriver(key, value, report = True, force = True)   
        self.nodeDefineDone = True
        self.discover()


              


    def stop(self):
        #self.removeNoticesAll()
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
        TPW.pollSystemData()
        self.updateISYdrivers()
        

    def longPoll(self):
        LOGGER.debug('Tesla Power Wall  Controller longPoll - heat beat')
        self.heartbeat()            

    def updateISYdrivers(self):
        LOGGER.debug('System updateISYdrivers')
        for key in ISYparams:
            info = ISYparams[key]
            if info != {}:
                value = TPW.getISYValue(key, self.id)
                LOGGER.debug('Update ISY drivers :' + str(ISYkey)+ ' ' + info['systemVar']+ ' value:' + str(value) )
                self.setDriver(key, value, report = True, force = False)          

    def query(self, command=None):
        LOGGER.debug('TOP querry')
        self.updateISYdrivers()
        self.reportDrivers()

    def discover(self, command=None):
        #LOGGER.debug('discover zones')
        self.nodeDefineDone = True

    def check_params(self, command=None):
        LOGGER.debug('Check Params')
 

    def ISYupdate (self, command):
        LOGGER.info('ISY-update called')
        TPW.pollSystemData()
        self.updateISYdrivers()
        self.reportDrivers()
 

    commands = { 'UPDATE': ISYupdate
                }

  
if __name__ == "__main__":
    try:
        LOGGER.info('Starting Messana Controller')
        polyglot = polyinterface.Interface('Tesla Power Wall Control')
        polyglot.start()
        control = TeslaPWController(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
