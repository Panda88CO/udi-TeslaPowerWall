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
        self.drivers = [{'driver': 'GV1', 'value':0, 'uom':25} ]
        #LOGGER.debug('MAIN ADDING DRIVER' + str(self.drivers))
        self.nodeDefineDone = False
        self.setDriver('GV1', 0, report = True, force = True)

        LOGGER.debug('Controller init DONE')
        
        
        self.defaultParams = {   'CLOUD':  { } ,
                                'LOCAL':  { },
                            }   

    def start(self):
        self.removeNoticesAll()
        self.addNotice('Check CONFIG to make sure all relevant paraeters are set')
        
        self.cloudAccess = False
        self.localAccess = False
        self.captcha = ''
        if PG_CLOUD_ONLY:
            self.cloudAccess = True
            self.logFile = False
            self.access = 'CLOUD'
            '''
            if self.getCustomParam('CAPTCHA'):
                self.removeCustomParam('CAPTCHA')
            self.addCustomParam({'CAPTCHA': self.captcha})
            self.defaultParams['CLOUD']['CAPTCHA'] =  self.captcha 
            '''
            self.cloudUserEmail = self.getCustomParam('CLOUD_USER_EMAIL')
            if self.cloudUserEmail == None:
                self.addCustomParam({'CLOUD_USER_EMAIL': 'me@myTeslaCloudemail.com'})
                self.defaultParams['CLOUD']['CLOUD_USER_EMAIL'] = 'me@myTeslaCloudemail.com'

            self.cloudUserPassword =self.getCustomParam('CLOUD_USER_PASSWORD')
            if self.cloudUserPassword == None:
                self.addCustomParam({'CLOUD_USER_PASSWORD': 'XXXXXXXX'})
                self.defaultParams['CLOUD']['CLOUD_USER_PASSWORD'] = 'XXXXXXXX'
            '''
            self.captchaMethod = self.getCustomParam('CAPTCHA_METHOD')
            if self.captchaMethod == None:
                self.addCustomParam({'CAPTCHA_METHOD': 'EMAIL/AUTO'})
                self.defaultParams['CLOUD']['CAPTCHA_METHOD'] = 'EMAIL/AUTO'
            '''    
            self.captchaAPIkey = self.getCustomParam('CAPTCHA_APIKEY')
            if self.captchaAPIkey == None:
                self.addCustomParam({'CAPTCHA_APIKEY': 'api key to enable AUTO captcha solver'})        
                self.defaultParams['CLOUD']['CAPTCHA_APIKEY'] =  'api key to enable AUTO captcha solver'
        else:
            '''
            if self.getCustomParam('CAPTCHA'):
                self.removeCustomParam('CAPTCHA')
            self.addCustomParam({'CAPTCHA': self.captcha})
            '''
            #We check if sel later so no need to include in self.defaultParams
            #  
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
            '''
            self.captchaMethod = self.getCustomParam('CAPTCHA_METHOD')
            if self.captchaMethod == None:
                self.addCustomParam({'CAPTCHA_METHOD': 'EMAIL/AUTO'})
                self.defaultParams['CLOUD']['CAPTCHA_METHOD'] = 'EMAIL/AUTO'
            '''
            self.captchaAPIkey = self.getCustomParam('CAPTCHA_APIKEY')
            if self.captchaAPIkey == None:
                self.addCustomParam({'CAPTCHA_APIKEY': 'api key to enable AUTO captcha solver'})
                self.defaultParams['CLOUD']['CAPTCHA_APIKEY'] =  'api key to enable AUTO captcha solver'

            self.logFile = self.getCustomParam('LOGFILE')
            if self.logFile == None:
                self.addCustomParam({'LOGFILE':'DISABLED'})

            # Wait for self.access to be updated
            while self.getCustomParam('ACCESS') == 'LOCAL/CLOUD/BOTH':
                time.sleep(2)
            self.access = self.getCustomParam('ACCESS')

        if self.access == 'BOTH' or self.access == 'CLOUD':
            # wait for user to set parameters
            allKeysSet = False
            while not(allKeysSet):
                allKeysSet = True
                for keys in self.defaultParams['CLOUD']:
                    if self.getCustomParam(keys) ==  self.defaultParams['CLOUD'][keys]:
                        # ok to not set captcha API KEY if method is email 
                        if not (keys == 'CAPTCHA_APIKEY' and self.getCustomParam('CAPTCHA_METHOD') == 'EMAIL') :
                            allKeysSet = False
                time.sleep(2)
            self.cloudAccess = True
            # All cloud keys defined

        if  self.access == 'BOTH' or self.access == 'LOCAL':
            allKeysSet = False
            while not(allKeysSet):
                allKeysSet = True
                for keys in self.defaultParams['LOCAL']:
                    if self.getCustomParam(keys) ==  self.defaultParams['LOCAL'][keys]:
                        allKeysSet = False
                time.sleep(2)
            self.localAccess = True
            #all local keys defined
        


        try:
            self.TPW = tesla_info(self.name, self.address, self.access)
            self.removeNoticesAll()
            if self.localAccess:
                self.TPW.loginLocal(self.localUserEmail, self.localUserPassword, self.IPAddress)
            if self.cloudAccess:
                self.TPW.loginCloud(self.cloudUserEmail, self.cloudUserPassword, 'AUTO', self.captchaAPIkey)
                self.TPW.teslaCloudConnect('', self.captchaAPIkey)
                '''
                if  self.captchaMethod == 'AUTO':
                    self.TPW.loginCloud(self.cloudUserEmail, self.cloudUserPassword, self.captchaMethod, self.captchaAPIkey)
                else:
                    self.TPW.loginCloud(self.cloudUserEmail, self.cloudUserPassword, self.captchaMethod, self.captchaAPIkey)
                    self.captcha = self.getCustomParam('CAPTCHA')
                    self.addNotice('Input CAPTCHA value from received email')
                    while self.captcha == '' or self.captcha == None:
                        LOGGER.info('Input CAPTCHA value from received email')
                        time.sleep(10)
                        self.captcha = self.getCustomParam('CAPTCHA')
                self.TPW.teslaCloudConnect(self.captcha, self.captchaAPIkey)
                '''
            self.removeNoticesAll()
            '''
            self.captcha = ''
            if self.getCustomParam('CAPTCHA'):    
                self.removeCustomParam('CAPTCHA')
            self.addCustomParam({'CAPTCHA': self.captcha})     
            '''
            self.TPW.teslaInitializeData()
            self.TPW.pollSystemData('all')          
     
            if self.logFile:
                self.TPW.createLogFile(self.logFile)
            if not(PG_CLOUD_ONLY):
                self.poly.installprofile()
            
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
            self.stop()
        LOGGER.debug ('Controler - start done')

    def stop(self):
       
        self.removeNoticesAll()
        if self.TPW:
            self.TPW.disconnectTPW()
        
        LOGGER.debug('stop - Cleaning up')

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
        
        

        if self.nodeDefineDone:
            self.heartbeat()    
            if self.TPW.pollSystemData('critical'):
                self.updateISYdrivers('critical')
                self.reportDrivers()
                for node in self.nodes:
                    #LOGGER.debug('Node : ' + node)
                    if node != self.address:
                        self.nodes[node].shortPoll()
            else:
                LOGGER.info('Problem polling data from Tesla system') 
        else:
            LOGGER.info('Waiting for system/nodes to get created')
        

    def longPoll(self):
        LOGGER.info('Tesla Power Wall  Controller longPoll')
        if self.nodeDefineDone:
            self.heartbeat()
            if self.TPW.pollSystemData('all'):
                self.updateISYdrivers('all')
                self.reportDrivers() 
                for node in self.nodes:
                    #LOGGER.debug('Node : ' + node)
                    if node != self.address :
                        self.nodes[node].longPoll()
            else:
                LOGGER.error ('Problem polling data from Tesla system')
        else:
            LOGGER.info('Waiting for system/nodes to get created')
        

    def updateISYdrivers(self, level):
        LOGGER.debug('System updateISYdrivers - ' + str(level))
        value = 1
        if level == 'all':
            value = self.TPW.getISYvalue('GV1', self.address)
            self.setDriver('GV1', value, report = True, force = True) 
            LOGGER.debug('Update ISY drivers :' + str('GV1')+ '  value:' + str(value) )
        elif level == 'critical':
            value = self.TPW.getISYvalue('GV1', self.address)
            self.setDriver('GV1', value, report = True, force = True) 
            LOGGER.debug('Update ISY drivers :' + str('GV1')+ '  value:' + str(value) )         
        else:
            LOGGER.error('Wrong parameter passed: ' + str(level))
 


    def ISYupdate (self, command):
        LOGGER.debug('ISY-update called')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            self.reportDrivers()
            for node in self.nodes:
                #LOGGER.debug('Node : ' + node)
                if node != self.address :
                    self.nodes[node].longPoll()
 
    commands = { 'UPDATE': ISYupdate }

if __name__ == "__main__":
    try:
        #LOGGER.info('Starting Tesla Power Wall Controller')
        polyglot = polyinterface.Interface('TeslaPWControl')
        polyglot.start()
        control = TeslaPWController(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
