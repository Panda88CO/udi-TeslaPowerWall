#!/usr/bin/env python3
PG_CLOUD_ONLY = False

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    PG_CLOUD_ONLY = True

#from os import truncate
import sys
import time 
from  TeslaInfo import tesla_info
from TeslaPWSetupNode import teslaPWSetupNode
from TeslaPWStatusNode import teslaPWStatusNode


LOGGER = polyinterface.LOGGER
               
class TeslaPWController(polyinterface.Controller):

    def __init__(self, polyglot):
        super(TeslaPWController, self).__init__(polyglot)
        LOGGER.info('_init_ Tesla Power Wall Controller - 1')
        self.ISYforced = False
        self.name = 'Tesla PowerWall Info'

        LOGGER.debug('self.address : ' + str(self.address))
        LOGGER.debug('self.name :' + str(self.name))
        self.hb = 0
        #if not(PG_CLOUD_ONLY):
        #self.drivers = []
        #LOGGER.debug('MAIN ADDING DRIVER' + str(self.drivers))
        self.nodeDefineDone = False
        #self.setDriver('ST', 0, report = True, force = True)
        #self.setDriver('GV2', 0, report = True, force = True)
        LOGGER.debug('Controller init DONE')
        self.longPollCountMissed = 0
        
        self.defaultParams = {   'CLOUD':  { } ,
                                'LOCAL':  { },
                            }   

    def start(self):
        self.stopped = False
        
        self.cloudAccess = False
        self.localAccess = False
        self.captcha = ''
        if PG_CLOUD_ONLY:
            self.cloudAccess = True
            self.logFile = False
            self.access = 'CLOUD'

            self.cloudUserEmail = self.getCustomParam('CLOUD_USER_EMAIL')
            if self.cloudUserEmail == None:
                self.addCustomParam({'CLOUD_USER_EMAIL': 'me@myTeslaCloudemail.com'})
                self.defaultParams['CLOUD']['CLOUD_USER_EMAIL'] = 'me@myTeslaCloudemail.com'

            self.cloudUserPassword =self.getCustomParam('CLOUD_USER_PASSWORD')
            if self.cloudUserPassword == None:
                self.addCustomParam({'CLOUD_USER_PASSWORD': 'XXXXXXXX'})
                self.defaultParams['CLOUD']['CLOUD_USER_PASSWORD'] = 'XXXXXXXX'

            self.captchaAPIkey = self.getCustomParam('CAPTCHA_APIKEY')
            if self.captchaAPIkey == None:
                self.addCustomParam({'CAPTCHA_APIKEY': 'api key to enable AUTO captcha solver'})        
                self.defaultParams['CLOUD']['CAPTCHA_APIKEY'] =  'api key to enable AUTO captcha solver'
        else:

            self.removeNoticesAll()
            self.addNotice('Check CONFIG to make sure all relevant paraeters are set - Restart after setting all parameters')

            self.access = self.getCustomParam('ACCESS') 
            if self.access == None:
                self.addCustomParam({'ACCESS': 'LOCAL/CLOUD/BOTH'})
                
            self.localUserEmail = self.getCustomParam('LOCAL_USER_EMAIL')
            if self.localUserEmail == None:
                self.addCustomParam({'LOCAL_USER_EMAIL': 'me@localPowerwall.com'})
                self.defaultParams['LOCAL']['LOCAL_USER_EMAIL'] =  'me@localPowerwall.com'

            self.localUserPassword =self.getCustomParam('LOCAL_USER_PASSWORD')
            if self.localUserPassword == None:
                self.addCustomParam({'LOCAL_USER_PASSWORD': 'XXXXXXXX'})
                self.defaultParams['LOCAL']['LOCAL_USER_PASSWORD'] =  'XXXXXXXX'
                
            self.IPAddress = self.getCustomParam('IP_ADDRESS')
            if  self.IPAddress == None:
                self.addCustomParam({'IP_ADDRESS': '192.168.1.xxx'})  
                self.defaultParams['LOCAL']['IP_ADDRESS'] =  '192.168.1.xxx'

            self.cloudUserEmail = self.getCustomParam('CLOUD_USER_EMAIL')
            if self.cloudUserEmail == None:
                self.addCustomParam({'CLOUD_USER_EMAIL': 'me@myTeslaCloudemail.com'})
                self.defaultParams['CLOUD']['CLOUD_USER_EMAIL'] = 'me@myTeslaCloudemail.com'

            self.cloudUserPassword =self.getCustomParam('CLOUD_USER_PASSWORD')
            if self.cloudUserPassword == None:
                self.addCustomParam({'CLOUD_USER_PASSWORD': 'XXXXXXXX'})
                self.defaultParams['CLOUD']['CLOUD_USER_PASSWORD'] = 'XXXXXXXX'

            self.captchaAPIkey = self.getCustomParam('CAPTCHA_APIKEY')
            if self.captchaAPIkey == None:
                self.addCustomParam({'CAPTCHA_APIKEY': 'api key to enable AUTO captcha solver'})
                self.defaultParams['CLOUD']['CAPTCHA_APIKEY'] =  'api key to enable AUTO captcha solver'

            self.logFile = self.getCustomParam('LOGFILE')
            if self.logFile == None:
                self.addCustomParam({'LOGFILE':'DISABLED'})

            # Wait for self.access to be updated
            if self.getCustomParam('ACCESS') == 'LOCAL/CLOUD/BOTH':
                self.addNotice(' ACCESS must be set start' )
                self.stop()
            

        if self.access == 'BOTH' or self.access == 'CLOUD':
            # check for user to set parameters
            allKeysSet = True
            for keys in self.defaultParams['CLOUD']:
                if self.getCustomParam(keys) ==  self.defaultParams['CLOUD'][keys]:
                    # ok to not set captcha API KEY if method is email 
                    allKeysSet = False
                    self.addNotice(str(keys) + ' not set')
            if not allKeysSet:
                LOGGER.debug('Not all CLOUD parameters are sprcified' )
                self.stop()
            else:
                self.cloudAccess = True
            # All cloud keys defined

        if  self.access == 'BOTH' or self.access == 'LOCAL':
            allKeysSet = True       
            for keys in self.defaultParams['LOCAL']:
                if self.getCustomParam(keys) ==  self.defaultParams['LOCAL'][keys]:
                    allKeysSet = False
                    self.addNotice(str(keys) + ' not set')
            if not allKeysSet:
                LOGGER.debug('Not all LOCAL parameters are sprcified' )
                self.stop()
            else:
                self.cloudAccess = True

            #all local keys defined
        
        try:
            self.TPW = tesla_info(self.name, self.address, self.access)
            self.removeNoticesAll()
            if self.localAccess:
                self.TPW.loginLocal(self.localUserEmail, self.localUserPassword, self.IPAddress)
            if self.cloudAccess:
                self.TPW.loginCloud(self.cloudUserEmail, self.cloudUserPassword, self.captchaAPIkey)
                self.TPW.teslaCloudConnect()

            self.TPW.teslaInitializeData()
            self.TPW.pollSystemData('all')          
     
            if self.logFile:
                self.TPW.createLogFile(self.logFile)
            if not(PG_CLOUD_ONLY):
                self.poly.installprofile()
                self.removeNoticesAll()
            
            LOGGER.info('Creating Nodes')
            nodeList = self.TPW.getNodeIdList()
            
            for node in nodeList:
                name = self.TPW.getNodeName(node)
                LOGGER.debug('Setup Node(node, name, address) ' + str(node) + ' , '+ str(name) + ' , '+str(self.address))
                if node == self.TPW.getSetupNodeID():  
                    self.addNode(teslaPWSetupNode(self,self.address, node, name))
                if node == self.TPW.getStatusNodeID():    
                    self.addNode(teslaPWStatusNode(self,self.address, node, name))
            LOGGER.debug('Node installation complete')
            self.nodeDefineDone = True
            LOGGER.debug('updateISYdrivers')
            self.updateISYdrivers('all')
            self.longPoll() # Update all drivers

        except Exception as e:
            LOGGER.error('Exception Controller start: '+ str(e))
            LOGGER.info('Did not connect to power wall')
            self.stopped = True 
            self.stop()
        LOGGER.debug ('Controler - start done')

    def stop(self):
        try:
            if not(PG_CLOUD_ONLY):
                self.removeNoticesAll()
            if self.TPW != None:
                self.TPW.disconnectTPW()
            self.stopped = True
            LOGGER.debug('stop - Cleaning up')
        except Exception as e:
            LOGGER.error('Stop Exception: '+str(e))
            LOGGER.debug('stopping')


    def heartbeat(self):
        LOGGER.debug('heartbeat: ' + str(self.hb))
        
        if self.hb == 0:
            self.reportCmd('DON',2)
            self.hb = 1
        else:
            self.reportCmd('DOF',2)
            self.hb = 0
        

    def shortPoll(self):
        LOGGER.info('Tesla Power Wall Controller shortPoll')
        if self.nodeDefineDone and not self.stopped:
            self.heartbeat()    
            if self.TPW.pollSystemData('critical'):
                self.updateISYdrivers('critical')
                #self.reportDrivers()
                for node in self.nodes:
                    #LOGGER.debug('Node : ' + node)
                    if node != self.address:
                        self.nodes[node].shortPoll()
            else:
                LOGGER.info('Problem polling data from Tesla system') 
        elif not self.stopped:
            LOGGER.info('Waiting for system/nodes to get created')
        else:
            LOGGER.error('System Stopped.')
        

    def longPoll(self):
        LOGGER.info('Tesla Power Wall  Controller longPoll')
        if self.nodeDefineDone and not self.stopped:
            #self.heartbeat()

            if self.TPW.pollSystemData('all'):
                self.updateISYdrivers('all')
                #self.reportDrivers() 
                for node in self.nodes:
                    #LOGGER.debug('Node : ' + node)
                    if node != self.address :
                        self.nodes[node].longPoll()
            else:
                LOGGER.error ('Problem polling data from Tesla system')
        elif not self.stopped:
            LOGGER.info('Waiting for system/nodes to get created')
        else:
            LOGGER.error('System Stopped.')
        
        

    def updateISYdrivers(self, level):
        LOGGER.debug('System updateISYdrivers - ' + str(level))
        value = 1
        if level == 'all':
            value = self.TPW.getISYvalue('ST', self.address)
            self.setDriver('ST',value, report = True, force = True) 
            #LOGGER.debug('Update ISY drivers :' + str('ST')+ '  value:' + str(value) )
            if value == 0:
                self.longPollCountMissed = self.longPollCountMissed + 1
            else:
                self.longPollCountMissed = 0
            self.setDriver('GV2', int(self.longPollCountMissed), report = True, force = True)     
            #LOGGER.debug('Update ISY drivers :' + str('GV2')+ '  value:' + str(self.longPollCountMissed) )
        elif level == 'critical':
            value = self.TPW.getISYvalue('ST', self.address)
            self.setDriver('ST', value, report = True, force = True)  
            #LOGGER.debug('Update ISY drivers :' + str('ST')+ '  value:' + str(value) )   
            if value == 0:
                self.longPollCountMissed = self.longPollCountMissed + 1
            else:
                self.longPollCountMissed = 0
            self.setDriver('GV2', int(self.longPollCountMissed), report = True, force = True)   
            #LOGGER.debug('Update ISY drivers :' + str('GV2')+ '  value:' + str(self.longPollCountMissed) )
        else:
            LOGGER.error('Wrong parameter passed: ' + str(level))
 


    def ISYupdate (self, command):
        LOGGER.debug('ISY-update called')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            #self.reportDrivers()
            for node in self.nodes:
                #LOGGER.debug('Node : ' + node)
                if node != self.address :
                    self.nodes[node].longPoll()
 
    commands = { 'UPDATE': ISYupdate }

    #if PG_CLOUD_ONLY:
    drivers= [{'driver': 'ST', 'value':0, 'uom':2},
                {'driver': 'GV2', 'value':0, 'uom':107}]


if __name__ == "__main__":
    try:
        #LOGGER.info('Starting Tesla Power Wall Controller')
        polyglot = polyinterface.Interface('TeslaPWControl')
        polyglot.start()
        control = TeslaPWController(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
