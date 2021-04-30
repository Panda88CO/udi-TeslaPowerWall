#!/usr/bin/env python3

import sys



LOGGER = polyinterface.LOGGER
               
class TeslaPWController(polyinterface.Controller):

    def __init__(self, messanaName):
        super(TeslaPWController, self).__init__(polyglot)
        LOGGER.info('_init_ Tesla Power Wall Controller')
        self.messanaImportOK = 0
        self.ISYforced = False
        self.name = 'Tesla Power Wall'
        self.address ='teslapw'
        self.id = self.address
        #LOGGER.debug('Name/address: '+ self.name + ' ' + self.address)
        self.primary = self.address
        self.hb = 0
        self.ISYdrivers=[]
        self.ISYcommands = {}
        self.ISYTempUnit = 0
        self.drivers = []
        self.nodeDefineDone = False



    def defineInputParams(self):
        self.IPAddress = self.getCustomParam('IP_ADDRESS')
        if self.IPAddress is None:
            self.addNotice('Please Set IP address of Messana system (IP_ADDRESS)')
            self.addNotice('E.g. 192.168.1.2')
            LOGGER.error('IP address not set')
            self.addCustomParam({'IP_ADDRESS': '192.168.1.2'})
            #self.IPAddress= '192.168.2.65'
            #self.addCustomParam({'IP_ADDRESS': self.IPAddress})
        
        if self.MessanaKey is None:
            self.addNotice('Please Set Messana API access Key (MESSANA_KEY)')
            self.addNotice('E.g. 12345678-90ab-cdef-1234-567890abcdef')
            LOGGER.error('check_params: Messana Key not specified')
            self.addCustomParam({'MESSANA_KEY': '12345678-90ab-cdef-1234-567890abcdef'})

            #self.MessanaKey =  '9bf711fc-54e2-4387-9c7f-991bbb02ab3a'
            #self.addCustomParam({'MESSANA_KEY': self.MessanaKey})
        self.addNotice('Please restart Node server after setting the parameters')



    def start(self):
        self.removeNoticesAll()
        LOGGER.info('Start Messana Main NEW')
        self.IPAddress = self.getCustomParam('IP_ADDRESS')
        if self.IPAddress == None:
            LOGGER.error('No IPaddress retrieved:' )
        else:
            LOGGER.debug('IPaddress retrieved: ' + self.IPAddress)
        self.MessanaKey = self.getCustomParam('MESSANA_KEY')
        if self.MessanaKey == None:
            LOGGER.error('No MESSANA_KEY retrieved:')
        else:
            LOGGER.debug('MESSANA_KEY retrieved: '+ self.MessanaKey)

        if (self.IPAddress is None) or (self.MessanaKey is None):
            self.defineInputParams()
            self.stop()

        else:
            LOGGER.info('Retrieving info from Messana System')
            self.messana = messanaInfo( self.IPAddress, self.MessanaKey, self.address )
            if self.messana == False:
                self.stop()
            self.id = self.messana.getSystemAddress()
            self.address = self.messana.getSystemAddress()
            self.messana.updateSystemData('all')
            self.systemGETKeys = self.messana.systemPullKeys()
            self.systemPUTKeys = self.messana.systemPushKeys()
            self.systemActiveKeys = self.messana.systemActiveKeys()
            
            
            for key in self.systemGETKeys:
                temp = self.messana.getSystemISYdriverInfo(key)
                if  temp != {}:
                    self.drivers.append(temp)
                    #LOGGER.debug(  'driver:  ' +  temp['driver'])

            LOGGER.debug ('Install Profile')    
            self.poly.installprofile()
            #LOGGER.debug('Install Profile done')
        self.updateISYdrivers('all')
        self.messanaImportOK = 1
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
        LOGGER.debug('Messana Controller shortPoll')

        if self.messanaImportOK == 1:
            LOGGER.debug('Short Poll System Up')
            if self.ISYforced:
                #self.messana.updateSystemData('active')
                self.updateISYdrivers('active')
            else:
                #self.messana.updateSystemData('all')
                self.updateISYdrivers('all')
            self.ISYforced = True
            LOGGER.debug('Short POll controller: ' )
            if self.nodeDefineDone == True:
                for node in self.nodes:
                    if node != self.address and node != 'controller':
                        #LOGGER.debug('Calling SHORT POLL for node : ' + node )
                        self.nodes[node].shortPoll()      

    def longPoll(self):
        LOGGER.debug('Messana Controller longPoll')
        if self.messanaImportOK == 1:
            self.heartbeat()
            self.messana.updateSystemData('all')
            LOGGER.debug( self.drivers)
            self.updateISYdrivers('all')
            self.reportDrivers()
            self.ISYforced = True   
            if self.nodeDefineDone == True:       
                for node in self.nodes:
                    if node != self.address and node != 'controller':
                        #LOGGER.debug('Calling LONG POLL for node : ' + node )
                        self.nodes[node].longPoll()
                    
                    

    def updateISYdrivers(self, level):
        LOGGER.debug('System updateISYdrivers')
        for ISYdriver in self.drivers:
            ISYkey = ISYdriver['driver']
            if level == 'active':
                temp = self.messana.getMessanaSystemKey(ISYkey)
                if temp in self.systemActiveKeys:
                    #LOGGER.debug('MessanaController ISYdrivers ACTIVE ' + temp)
                    status, value = self.messana.getSystemISYValue(ISYkey)
                    if status:
                        if self.ISYforced:
                            self.setDriver(ISYdriver['driver'], value, report = True, force = False)
                        else:
                            self.setDriver(ISYdriver['driver'], value, report = True, force = True)
                        #LOGGER.debug('driver updated :' + ISYdriver['driver'] + ' =  '+str(value))
                    else:
                        LOGGER.error('Error getting ' + ISYdriver['driver'])
            elif level == 'all':
                temp = self.messana.getMessanaSystemKey(ISYkey)
                #LOGGER.debug('MessanaController ISYdrivers ACTIVE ' + temp)
                status, value = self.messana.getSystemISYValue(ISYkey)
                if status:
                    if self.ISYforced:
                        self.setDriver(ISYdriver['driver'], value, report = True, force = False)
                    else:
                        self.setDriver(ISYdriver['driver'], value, report = True, force = True)
                    #LOGGER.debug('driver updated :' + ISYdriver['driver'] + ' =  '+str(value))
                else:
                    LOGGER.error('Error getting ' + ISYdriver['driver'])
            else:
                 LOGGER.error('Error!  Unknown level passed: ' + level)


    def query(self, command=None):
        LOGGER.debug('TOP querry')
        self.teslaPW.updateSystemData('all')
        self.reportDrivers()

    def discover(self, command=None):

        LOGGER.debug('discover zones')
        self.nodeDefineDone = True
  
    

    def check_params(self, command=None):
        LOGGER.debug('Check Params')
 
    def setStatus(self, command):
        #LOGGER.debug('set Status Called')
        value = int(command.get('value'))
        LOGGER.debug('set Status Recived:' + str(value))
        if self.messana.systemSetStatus(value):
            ISYdriver = self.messana.getSystemStatusISYdriver()
            self.setDriver(ISYdriver, value, report = True)

    def setEnergySave(self, command):
        #LOGGER.debug('setEnergySave Called')
        value = int(command.get('value'))
        LOGGER.debug('SetEnergySave Recived:' + str(value))
        if self.messana.systemSetEnergySave(value):
            ISYdriver = self.messana.getSystemEnergySaveISYdriver()
            self.setDriver(ISYdriver, value, report = True)

    def setSetback(self, command):
        #LOGGER.debug('setSetback Called')
        value = int(command.get('value'))
        LOGGER.debug('setSetback Reeived:' + str(value))
        if self.messana.systemSetback(value):
            ISYdriver = self.messana.getSystemSetbackISYdriver()
            self.setDriver(ISYdriver, value, report = True)

    def ISYupdate (self, command):
        LOGGER.info('ISY-update called')
        self.messana.updateSystemData('all')
        self.updateISYdrivers('all')
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
