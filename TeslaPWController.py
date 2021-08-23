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
        LOGGER.info('_init_ Tesla Power Wall Controller')
        self.ISYforced = False
        self.name = 'Tesla PowerWall Info'
        self.id = 'teslapw'
        self.address = self.id
        self.primary = self.address
        LOGGER.debug('self address : ' + str(self.address))
        self.hb = 0
        if not(PG_CLOUD_ONLY):
            self.drivers = []
  
        self.nodeDefineDone = False
        self.TPW = None

    def start(self):
        self.removeNoticesAll()
        self.addNotice('Check CONFIG to make sure all relevant paraeters are set')
        #self.customParams = self.poly.config['customParams']
        #LOGGER.debug(self.customParams)
        self.cloudAccess = False
        self.localAccess = False
        self.captcha = ''
        if self.getCustomParam('CAPTCHA'):
            self.removeCustomParam('CAPTCHA')
        self.addCustomParam({'CAPTCHA': self.captcha})


        self.access = self.getCustomParam('ACCESS') 
        if self.access == None:
            self.addCustomParam({'ACCESS': 'LOCAL/CLOUD/BOTH'})

        self.localUserEmail = self.getCustomParam('LOCAL_USER_EMAIL')
        if self.localUserEmail == None:
            self.addCustomParam({'LOCAL_USER_EMAIL': 'me@localPowerwall.com'})
        
        self.localUserPassword =self.getCustomParam('LOCAL_USER_PASSWORD')
        if self.localUserPassword == None:
            self.addCustomParam({'LOCAL_USER_PASSWORD': 'XXXXXXXX'})
        
        self.IPAddress = self.getCustomParam('IP_ADDRESS')
        if  self.IPAddress == None:
            self.addCustomParam({'IP_ADDRESS': '192.168.1.200'})  

        self.cloudUserEmail = self.getCustomParam('CLOUD_USER_EMAIL')
        if self.cloudUserEmail == None:
            self.addCustomParam({'CLOUD_USER_EMAIL': 'me@myTeslaCloudemail.com'})

        self.cloudUserPassword =self.getCustomParam('CLOUD_USER_PASSWORD')
        if self.cloudUserPassword == None:
            self.addCustomParam({'CLOUD_USER_PASSWORD': 'XXXXXXXX'})

        self.captchaMethod = self.getCustomParam('CAPTCHA_METHOD')
        if self.captchaMethod == None:
            self.addCustomParam({'CAPTCHA_METHOD': 'EMAIL/AUTO'})

        self.captchaAPIkey = self.getCustomParam('CAPTCHA_APIKEY')
        if self.captchaAPIkey == None:
            self.addCustomParam({'CAPTCHA_APIKEY': 'api key to enable AUTO captcha solver'})


        self.logFile = self.getCustomParam('LOGFILE')
        if self.logFile == None:
            self.addCustomParam({'LOGFILE':'DISABLED'})


        if PG_CLOUD_ONLY:
            self.cloudAccess = True
            self.logFile = False
            self.access = 'CLOUD'
            self.addCustomParam({'ACCESS':'CLOUD'})
            self.addCustomParam({'LOGFILE':'DISABLED'})
            self.removeCustomParam('LOCAL_USER_EMAIL')
            self.removeCustomParam('LOCAL_USER_PASSWORD')
            self.removeCustomParam('IP_ADDRESS')

        if self.access == 'BOTH' or self.access== 'CLOUD':
            self.cloudAccess = True
        if  self.access == 'BOTH' or self.access== 'LOCAL':
            self.localAccess = True


        try:
            self.TPW = tesla_info(self.name, self.id , self.access)
            self.removeNoticesAll()
            if self.localAccess:
                self.TPW.loginLocal(self.localUserEmail, self.localUserPassword, self.IPAddress)
            if self.cloudAccess:
                if  self.captchaMethod == 'AUTO':
                    self.TPW.loginCloud(self.cloudUserEmail, self.cloudUserPassword, self.captchaMethod, self.captchaAPIkey)
                else:
                    self.TPW.loginCloud(self.cloudUserEmail, self.cloudUserPassword, self.captchaMethod, self.captchaAPIkey)
                    self.captcha = self.getCustomParam('CAPTCHA')
                    while self.captcha == '' or self.captcha == None:
                        LOGGER.info('Input CAPTCHA value from received email ')
                        time.sleep(10)
                        self.captcha = self.getCustomParam('CAPTCHA')
                self.TPW.teslaCloudConnect(self.captcha, self.captchaAPIkey)
            self.removeNoticesAll()
            self.TPW.teslaInitializeData()
            self.TPW.pollSystemData('all')          
            #self.poly.installprofile()

            self.captcha = ''
            if self.getCustomParam('CAPTCHA'):    
                self.removeCustomParam('CAPTCHA')
            self.addCustomParam({'CAPTCHA': self.captcha})

            if self.logFile:
                self.TPW.createLogFile(self.logFile)
            self.ISYparams = self.TPW.supportedParamters(self.id)
            self.ISYcriticalParams = self.TPW.criticalParamters(self.id)
            LOGGER.debug('Controller start params: ' + str(self.ISYparams))
            LOGGER.debug('Controller start critical params: ' + str(self.ISYcriticalParams))
            
            for key in self.ISYparams:
                info = self.ISYparams[key]
                if info != {}:
                    value = self.TPW.getISYvalue(key, self.id)
                    LOGGER.debug('driver: ' + str(key)+ ' value:' + str(value) + ' uom:' + str(info['uom']) )
                    if not(PG_CLOUD_ONLY):
                        self.drivers.append({'driver':key, 'value':value, 'uom':info['uom'] })
                
            #if PG_CLOUD_ONLY:
            #    self.poly.installprofile()            
            self.poly.installprofile()

            LOGGER.info('Creating Setup Node')
            nodeList = self.TPW.getNodeIdList()
            LOGGER.debug('Setup start ' + str(nodeList))
    
            for node in nodeList:
                name = self.TPW.getNodeName(node)
                LOGGER.debug('Setup Node node, name ' + str(node) + ' , '+ str(name))
                if node == self.TPW.getSetupNodeID():           #LOGGER.debug(node)
                    self.addNode(teslaPWSetupNode(self, self.address, node, name))
                if node == self.TPW.getStatusNodeID():    
                    self.addNode(teslaPWStatusNode(self, self.address, node, name))

            self.TPW.pollSystemData('all')
            self.updateISYdrivers('all')
            #self.reportDrivers()
            self.TPW.createLogFile(self.logFile)
            self.nodeDefineDone = True
        except Exception as e:
            LOGGER.debug('Exception Controller start: '+ str(e))
            LOGGER.info('Did not connect to power wall')
            self.stop()


    def stop(self):
        self.removeNoticesAll()
        if self.TPW:
            self.TPW.disconnectTPW()
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
        LOGGER.info('Tesla Power Wall Controller shortPoll')
        self.heartbeat()

        if self.nodeDefineDone:
            for node in self.nodes:
                #LOGGER.debug('Node : ' + node)
                if node != self.address and node != 'controller':
                    self.nodes[node].shortPoll()
        
            if self.TPW.pollSystemData('critical'):
                self.updateISYdrivers('critical')
                self.reportDrivers()
            else:
                LOGGER.info ('Problem polling data from Tesla system')
        else:
            LOGGER.info('Waiting for system/nodes to get created')

    def longPoll(self):
        LOGGER.info('Tesla Power Wall  Controller longPoll')
        self.heartbeat()
        if self.nodeDefineDone:
            if self.TPW.pollSystemData('all'):
                self.updateISYdrivers('all')
                self.reportDrivers() 
            else:
                LOGGER.info ('Problem polling data from Tesla system')
        else:
            LOGGER.info('Waiting for system/nodes to get created')
        for node in self.nodes:
            #LOGGER.debug('Node : ' + node)
            if node != self.address and node != 'controller':
                self.nodes[node].longPoll()
        
    def updateISYdrivers(self, level):
        LOGGER.debug('System updateISYdrivers - ' + str(level))
        params = []
        #LOGGER.debug(self.id)
        #LOGGER.debug(self.ISYparams)
        if level == 'all':
            params = self.ISYparams
            #LOGGER.debug ('all: ' + str(params) )
            if params:
                for key in params:
                    info = params[key]
                    if info != {}:
                        value = self.TPW.getISYvalue(key, self.id)
                        #LOGGER.debug('Update ISY drivers :' + str(key)+ ' ' + info['systemVar']+ ' value:' + str(value) )
                        #self.setDriver(str(key), value) 
                        self.setDriver(key, value, report = True, force = True) 
                        LOGGER.debug('Update ISY drivers :' + str(key)+ ' ' + info['systemVar']+ ' value:' + str(value) )
        elif level == 'critical':
            params = self.ISYcriticalParams
            #LOGGER.debug ('Critial: ' + str(params) )
            if params:
                for key in params:
                    value = self.TPW.getISYvalue(key, self.id)
                    LOGGER.debug('Update ISY drivers :' + str(key)+ '  value: ' + str(value) )
                    self.setDriver(key, value, report = True, force = True)       
                    #self.setDriver(str(key), value)       
                    #LOGGER.debug('Update ISY drivers :' + str(key)+ '  value: ' + str(value) )
        else:
            LOGGER.debug('Wrong parameter passed: ' + str(level))
            #LOGGER.debug(params)

    '''
    def query(self, command=None):
        LOGGER.debug('TOP querry')
        self.updateISYdrivers(ll''a)
        self.reportDrivers('all')
    '''

    '''
    def discover(self, command=None):
        #LOGGER.debug('discover zones')
        self.nodeDefineDone = True
    '''

    def ISYupdate (self, command):
        LOGGER.debug('ISY-update called')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            #self.reportDrivers()
 
    commands = { 'UPDATE': ISYupdate}

    drivers = [{'driver': 'GV1', 'value':1, 'uom':2}]
    '''
    if PG_CLOUD_ONLY:
        drivers= [{'driver': 'GV1', 'value':0, 'uom':33}
                 ,{'driver': 'GV2', 'value':0, 'uom':33}
                 ,{'driver': 'GV3', 'value':0, 'uom':33}
                 ,{'driver': 'GV4', 'value':0, 'uom':33}
                 ,{'driver': 'GV5', 'value':0, 'uom':33}
                 ,{'driver': 'GV6', 'value':0, 'uom':33}
                 ,{'driver': 'GV7', 'value':0, 'uom':33}
                 ,{'driver': 'GV8', 'value':0, 'uom':33}
                 ,{'driver': 'GV9', 'value':0, 'uom':33}
                 ,{'driver': 'GV10', 'value':0, 'uom':33}
                 ,{'driver': 'GV11', 'value':0, 'uom':33}
                 ,{'driver': 'GV12', 'value':0, 'uom':33}
                 ,{'driver': 'GV13', 'value':0, 'uom':33}
                 ,{'driver': 'GV14', 'value':0, 'uom':33}
                 ,{'driver': 'GV15', 'value':0, 'uom':51}
                 ,{'driver': 'GV16', 'value':0, 'uom':33}
                 ,{'driver': 'GV17', 'value':0, 'uom':33}   
                 ,{'driver': 'GV18', 'value':0, 'uom':25}
                 ,{'driver': 'GV19', 'value':0, 'uom':25}
                 ,{'driver': 'GV20', 'value':0, 'uom':25}
        ] 
    '''
if __name__ == "__main__":
    try:
        #LOGGER.info('Starting Tesla Power Wall Controller')
        polyglot = polyinterface.Interface('Tesla Power Wall')
        polyglot.start()
        control = TeslaPWController(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
