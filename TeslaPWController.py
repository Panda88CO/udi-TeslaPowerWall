#!/usr/bin/env python3
PG_CLOUD_ONLY = False

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface

    PG_CLOUD_ONLY = True

#from os import truncate
import sys
from datetime import time 
from  TeslaInfo import tesla_info
from TeslaPWSetupNode import teslaPWSetupNode

LOGGER = polyinterface.LOGGER
               
class TeslaPWController(polyinterface.Controller):

    def __init__(self, polyglot):
        super(TeslaPWController, self).__init__(polyglot)
        LOGGER.info('_init_ Tesla Power Wall Controller')
        self.ISYforced = False
        self.name = 'Tesla PowerWall Info'
        self.id = 'teslapw'
        self.primary = self.address
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

        self.logFile = self.getCustomParam('LOGFILE')
        self.access = self.getCustomParam('ACCESS') 
        self.localUserEmail = self.getCustomParam('LOCAL_USER_EMAIL')
        self.localUserPassword =self.getCustomParam('LOCAL_USER_PASSWORD')
        self.IPAddress = self.getCustomParam('IP_ADDRESS')
        self.captchaMethod = self.getCustomParam('CAPTCHA_METHOD')
        self.captchaAPIkey = self.getCustomParam('CAPTCHA_APIKEY')
        self.cloudUserEmail = self.getCustomParam('CLOUD_USER_EMAIL')
        self.cloudUserPassword =self.getCustomParam('CLOUD_USER_PASSWORD')

        if self.captchaMethod == None:
            self.addCustomParam({'CAPTCHA_METHOD': 'EMAIL/AUTO'})
        if self.logFileParam == None: 
            self.addCustomParam({'LOGFILE': 'DISABLED'})

        if PG_CLOUD_ONLY:
            self.cloudAccess = True
            self.logFile = False
            self.access = 'CLOUD'
            self.addCustomParam({'ACCESS':'CLOUD'})
            self.addCustomParam({'LOGFILE':'DISABLED'})
            if self.cloudUserEmail == None:
                self.addCustomParam({'CLOUD_USER_EMAIL': 'me@myTeslaCloudemail.com'})
            if self.cloudUserPassword == None:
                self.addCustomParam({'CLOUD_USER_PASSWORD': 'XXXXXXXX'})
            if self.captchaAPIkey == None:
                self.addCustomParam({'CAPTCHA_APIKEY': 'api key to enable AUTO captcha solver'})
            if self.captcha != '' and self.captcha != None:
                self.addCustomParam({'CAPTCHA': 'captcha received in email'})
        else:
            #determine access method
            while self.access != 'LOCAL' and self.access != 'CLOUD' and self.access != 'BOTH':
                LOGGER.info('Waiting for ACCESS to be set - current value:' + self.access)           
                time.sleep(10)
                self.access = self.getCustomParam('ACCESS') 
            #handle local info 
            if self.access == 'LOCAL' or self.access == 'BOTH':
                self.localAccess = True
                while self.localUserEmail == None or self.localUserPassword == None or self.IPAddress == None:
                    if self.localUserEmail == None:
                        self.addCustomParam({'LOCAL_USER_EMAIL': 'me@localPowerwall.com'})
                    if self.localUserPassword == None:
                        self.addCustomParam({'LOCAL_USER_PASSWORD': 'XXXXXXXX'})
                    if self.IPAddress == None:
                        self.addCustomParam({'IP_ADDRESS': '192.168.1.200'})  
            if self.access == 'CLOUD' or self.access == 'BOTH':
                self.cloudAccess= True
                while self.localUserEmail == None or self.localUserPassword == None or self.IPAddress == None:
                    if self.cloudUserEmail == None:
                        self.addCustomParam({'CLOUD_USER_EMAIL': 'me@TeslaCloud.com'})
                    if self.cloudUserPassword == None:
                        self.addCustomParam({'CLOUD_USER_PASSWORD': 'XXXXXXXX'})    

        while self.captchaMethod != 'EMAIL' and self.captchaMethod != 'AUTO':
            LOGGER.info('Waiting for CAPTCHA method to be set - current value:' + self.captchaMethod)           
            time.sleep(10)
            self.access = self.getCustomParam('CAPTCHA_METHOD') 
        if self.captchaMethod == 'AUTO':
            if self.captchaAPIkey == None:
                self.addCustomParam({'CAPTCHA_APIKEY': 'api key to enable AUTO captcha solver'})
            else:
                self.captcha = ''
                if self.getCustomParam('CAPTCHA'):
                    self.removeCustomParam('CAPTCHA')
                self.addCustomParam({'CAPTCHA': self.captcha})

        try:
            self.TPW = tesla_info(self.name, self.id , self.access)
            if self.localAccess:
                self.TPW.loginLocal(self.localUserEmail, self.localUserPassword, self.IPAddress)
            if self.cloudAccess and self.captchaMethod == 'AUTO':
                self.TPW.loginCloud(self.cloudUserEmail, self.cloudUserPassword, self.captchaMethod, self.captchaAPIkey)
            else:
                self.TPW.loginCloud(self.cloudUserEmail, self.cloudUserPassword, self.captchaMethod, self.captchaAPIkey)
                self.captcha = self.getCustomParam('CAPTCHA')
                while self.captcha == '':
                    LOGGER.info('Input CAPTA value from received email ')
                    time.sleep(10)
                    self.captcha = self.getCustomParam('CAPTCHA')
                self.TPW.teslaCloudConnect(self.captcha)
            self.TPW.teslaInitializeData()
            self.TPW.pollSystemData('all')          
            self.poly.installprofile()
            if self.logFile:
                self.TPW.createLogFile(self.logFile)
            self.ISYparams = self.TPW.supportedParamters(self.id)
            self.ISYcriticalParams = self.TPW.criticalParamters(self.id)
            #LOGGER.debug('Controller start params: ' + str(self.ISYparams))
            #LOGGER.debug('Controller start critical params: ' + str(self.ISYcriticalParams))
            
            for key in self.ISYparams:
                info = self.ISYparams[key]
                if info != {}:
                    value = self.TPW.getISYvalue(key, self.id)
                    #LOGGER.debug('driver: ' + str(key)+ ' value:' + str(value) + ' uom:' + str(info['uom']) )
                    if not(PG_CLOUD_ONLY):
                        self.drivers.append({'driver':key, 'value':value, 'uom':info['uom'] })
                
            #if PG_CLOUD_ONLY:
            #    self.poly.installprofile()            

            LOGGER.info('Creating Setup Node')
            nodeList = self.TPW.getNodeIdList()
            LOGGER.debug("controller start" + str(nodeList))
            for node in nodeList:
                #LOGGER.debug(node)
                name = self.TPW.getNodeName(node)
                self.addNode(teslaPWSetupNode(self, self.address, node, name))
            
            #self.heartbeat()
            
            self.TPW.pollSystemData('all')
            self.updateISYdrivers('all')
            #self.reportDrivers()
            self.TPW.createLogFile(self.logFile)
            self.nodeDefineDone = True
        except Exception as e:
            LOGGER.debug('Exception Controller start: '+ str(e))
            LOGGER.info('Did not connect to power wall')

            self.stop()



    '''
    def start1(self):
        self.removeNoticesAll()
        self.access = ''
        #LOGGER.info('Start Tesla Power Wall Main New')
        self.localAccess= False # Assume no local access initially
        self.cloudAccess= False # Assume no cloud access initially
        if not(PG_CLOUD_ONLY):
            self.localAccess = True # Assume local access initially
            self.cloudAccess = True # Assume cloud access initially
            self.logFileParam = self.getCustomParam('LOGFILE')

            if self.logFileParam == None: 
                LOGGER.info('LOGFILE type not retrieved - ENABLED, DISABLED' )
                self.defineAccessInputParam()
                self.logFile = False
            else:
                param = str(self.logFileParam).upper()
                if param == 'ENABLED' or param == 'ENABLE':
                    self.logFile = True
                    LOGGER.info('LogFile enabled @ ./dailyData')
                else:
                    self.logFile = False                    
                    LOGGER.info('LogFile disabled')
            
            self.access = self.getCustomParam('ACCESS') 
            if self.access == None:
                LOGGER.info('Access type not retrieved - LOCAL, CLOUD, BOTH' )
                self.defineAccessInputParam()
                self.localAccess = False
                self.stop()
            
            LOGGER.debug(self.access)
            if self.access.upper() == 'LOCAL' or self.access.upper() == 'BOTH':
                self.localAccess = True
                self.IPAddress = self.getCustomParam('IP_ADDRESS')
                if self.IPAddress == None:
                    LOGGER.info('No IPaddress specified:' )
                    self.localAccess = False
                else:
                    LOGGER.debug('IPaddress retrieved: ' + self.IPAddress)

                self.localUserEmail = self.getCustomParam('LOCAL_USER_EMAIL')
                if self.localUserEmail == None:
                    LOGGER.info('No LOCAL_USER_EMAIL retrieved:')
                    self.localAccess = False
                else:
                    LOGGER.info('OCAL_USER_EMAIL retrieved: '+ self.localUserEmail)
                self.localUserPassword =self.getCustomParam('LOCAL_USER_PASSWORD')
                if self.localUserPassword == None:
                    LOGGER.info('No LOCAL_USER_PASSWORD:')
                    self.LocalAccess = False
                else:
                    LOGGER.debug('LOCAL_USER_PASSWORD retrieved: XXXXXXXX')
                
                if not(self.localAccess):
                    self.defineLocalInputParams()                              
            if self.access.upper() == 'CLOUD' or self.access.upper() == 'BOTH':
                self.cloudAccess= True
                self.captchaMethod = self.getCustomParams('CAPTCHA_METHOD')
                if self.captchaMethod == None:
                    self.addNotice('Please select captcha sover method - email or automatic (requires Key)')
                    LOGGER.debug('check_params: cloud user password not specified')
                    self.addCustomParam({'CLOUD_USER_PASSWORD': 'XXXXXXXX'})
                self.cloudUserEmail = self.getCustomParam('CLOUD_USER_EMAIL')
                if self.cloudUserEmail == None:
                    LOGGER.info('No CLOUD_USER_EMAIL retrieved:')
                    self.cloudAccess = False
                else:
                    LOGGER.debug('CLOUD_USER_EMAIL retrieved: '+ self.cloudUserEmail)
                self.cloudUserPassword =self.getCustomParam('CLOUD_USER_PASSWORD')
                if self.cloudUserPassword == None:
                    LOGGER.info('No CLOUD_USER_PASSWORD:')
                    self.cloudAccess = False
                else:
                    LOGGER.debug('CLOUD_USER_PASSWORD retrieved: XXXXXXXX')
                if not(self.cloudAccess):
                    self.defineCloudInputParams()
        else:
            self.access = 'CLOUD'
            self.cloudAccess = True
            self.localAccess = False
            self.logFile = False
            self.cloudUserEmail = self.getCustomParam('CLOUD_USER_EMAIL')
            if self.cloudUserEmail == None:
                LOGGER.info('No cloud USER_EMAIL retrieved:')
                self.addCustomParam({'CLOUD_USER_EMAIL': 'nobody@email.com'})
            else:
                LOGGER.info('Cloud USER_EMAIL retrieved: '+ self.cloudUserEmail)
            self.cloudUserPassword =self.getCustomParam('CLOUD_USER_PASSWORD')
            if self.cloudUserPassword == None:
                LOGGER.info('No cloud USER_PASSWORD:')
                self.addCustomParam({'CLOUD_USER_PASSWORD': 'XXXXXXXX'})
            else:
                LOGGER.debug('CLOUD_USER_PASSWORD retrieved: XXXXXXXX')
        if not(self.cloudAccess) and not(self.localAccess):
                self.stop()

        #LOGGER.info('Connecting to Tesla Power Wall')
        # Ensure cloud will not be accessed even if keywords are defined
        if not(self.cloudAccess):
            self.cloudUserEmail = None
            self.cloudUserPassword = None

        # Ensure local will not be accesses even if keywords are defined
        if not(self.localAccess):
            self.LocalUserEmail= None
            self.LocalUserPassword = None
            self.IPAddress = None

        try:
    
            if self.access == 'BOTH':
                LOGGER.info('BOTH selected')
                #self.addCustomParam({'CAPTCHA': ''})
                #self.addNotice("Check cloud email for Captcha image - then input captcha string")

                self.TPW = tesla_info(self.cloudUserEmail, self.cloudUserPassword, self.name, self.id , self.localUserEmail, self.localUserPassword, self.IPAddress )
            elif self.access == 'CLOUD':
                LOGGER.info('CLOUD selected')          
                self.TPW = tesla_info(self.cloudUserEmail, self.cloudUserPassword, self.name, self.id ,)
            else:  # Local only 
                LOGGER.info('LOCAL selected')
                self.TPW = tesla_info(None,None, self.name, self.id , self.localUserEmail, self.localUserPassword, self.IPAddress )
            #self.TPW.createISYsetup()
            LOGGER.debug ('Install Profile')    

            self.TPW.pollSystemData('all')          
            self.poly.installprofile()
            if self.logFile:
                self.TPW.createLogFile(self.logFile)
            self.ISYparams = self.TPW.supportedParamters(self.id)
            self.ISYcriticalParams = self.TPW.criticalParamters(self.id)
            #LOGGER.debug('Controller start params: ' + str(self.ISYparams))
            #LOGGER.debug('Controller start critical params: ' + str(self.ISYcriticalParams))
            
            for key in self.ISYparams:
                info = self.ISYparams[key]
                if info != {}:
                    value = self.TPW.getISYvalue(key, self.id)
                    #LOGGER.debug('driver: ' + str(key)+ ' value:' + str(value) + ' uom:' + str(info['uom']) )
                    if not(PG_CLOUD_ONLY):
                        self.drivers.append({'driver':key, 'value':value, 'uom':info['uom'] })
                
            #if PG_CLOUD_ONLY:
            #    self.poly.installprofile()            

            LOGGER.info('Creating Setup Node')
            nodeList = self.TPW.getNodeIdList()
            LOGGER.debug("controller start" + str(nodeList))
            for node in nodeList:
                #LOGGER.debug(node)
                name = self.TPW.getNodeName(node)
                self.addNode(teslaPWSetupNode(self, self.address, node, name))
            
            #self.heartbeat()
            
            self.TPW.pollSystemData('all')
            self.updateISYdrivers('all')
            #self.reportDrivers()
            self.TPW.createLogFile(self.logFile)
            self.nodeDefineDone = True
        except Exception as e:
            LOGGER.debug('Exception Controller start: '+ str(e))
            LOGGER.info('Did not connect to power wall')

            self.stop()
    '''


    def defineLocalInputParams(self):
        LOGGER.debug('defineLocalInputParams')
        self.addNotice('Input IP address, email and password used to log in to local power wall - 192.168.x.x')  
        self.IPAddress = self.getCustomParam('IP_ADDRESS')
        if self.IPAddress is None:
            self.addNotice('Please Set IP address of Tesla Power Wall system (IP_ADDRESS) - E.g. 192.168.1.2') 
            LOGGER.info('IP address not set')
            self.addCustomParam({'IP_ADDRESS': '192.168.1.100'})

        self.LocalUserEmail = self.getCustomParam('LOCAL_USER_EMAIL)')
        if self.LocalUserEmail is None:
            self.addNotice('Please Set Tesla Power Wall (local) login email (LOCAL_USER_EMAIL) - E.g. nobody@email.com')
            LOGGER.info('check_params: local user email not specified')
            self.addCustomParam({'LOCAL_USER_EMAIL': 'nobody@email.com'})

        self.LocalUserPassword= self.getCustomParam('LOCAL_USER_PASSWORD')
        if self.LocalUserPassword is None:
            self.addNotice('Please Set Tesla Power Wall (local) password (LOCAL_USER_PASSWORD) - E.g. XXXXXXXX')
            LOGGER.info('check_params: local user password not specified')
            self.addCustomParam({'LOCAL_USER_PASSWORD': 'XXXXXXXX'})

    def defineAccessInputParam(self):
        LOGGER.debug('defineAccessInputParam')
        if PG_CLOUD_ONLY:
            self.addCustomParam({'ACCESS':'CLOUD'})
            self.addCustomParam({'LOGFILE':'DISABLED'})
            self.logFile = False
        else:
            self.access = self.getCustomParam('ACCESS')
            if self.access == None:
                self.addNotice('Data Source type : LOCAL, CLOUD, or BOTH')
                self.addNotice('Please input Access type ')
                LOGGER.info('check_params: access type not defined')
                self.addCustomParam({'ACCESS': 'LOCAL/CLOUD/BOTH'})

            self.logFileParam = self.getCustomParam('LOGFILE')
            if self.logFileParam == None:
                self.addNotice('Daily Summary Logfile ENABLED/DISABLED ')
                LOGGER.info('LOGFILE input not defind - assume diabled')
                self.addCustomParam({'LOGFILE': 'DISABLED'})    
                self.logFile = False  
            else:
                param = str(self.logFileParam).upper()
                if param == 'ENABLED' or param == 'ENABLE':
                    self.logFile = True
                    LOGGER.debug('LogFile enabled @ ./daailyData')
                else:
                    self.logFile = False 
                    LOGGER.debug('LogFile disabled')
            
    def defineCloudInputParams(self):
        LOGGER.debug('defineCloudInputParams')        
        self.addNotice('Input email and password used to log in to Tesla power wall website (www.tesla.com)')
        self.CloudUserEmail = self.getCustomParam('CLOUD_USER_EMAIL)')
        if self.CloudUserEmail is None:
            self.addNotice('Please Set Tesla Power Wall Cloud login email (CLOUD_USER_EMAIL) - E.g. nobody@email.com')
            LOGGER.debug('check_params: cloud user email not specified')
            self.addCustomParam({'CLOUD_USER_EMAIL': 'nobody@email.com'})

        self.CloudUserPassword = self.getCustomParam('CLOUD_USER_PASSWORD')
        if self.CloudUserPassword is None:
            self.addNotice('Please Set Tesla Power Wall Cloud password (CLOUD_USER_PASSWORD) - E.g. XXXXXXXX')
            LOGGER.debug('check_params: cloud user password not specified')
            self.addCustomParam({'CLOUD_USER_PASSWORD': 'XXXXXXXX'})
        self.addNotice('Please restart Node server after setting the parameters')


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
            if self.TPW.pollSystemData('critical'):
                self.updateISYdrivers('critical')
                self.reportDrivers()
            else:
                LOGGER.info ('Problem polling data from Tesla system')
        else:
            LOGGER.info('Waiting for system/nodes to get created')
        #LOGGER.debug('Nodes : ' + self.nodes)
        for node in self.nodes:
            #LOGGER.debug('Node : ' + node)
            if node != self.address and node != 'controller':
                self.nodes[node].shortPoll()
        

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
                        #LOGGER.debug('Update ISY drivers :' + str(key)+ ' ' + info['systemVar']+ ' value:' + str(value) )
        elif level == 'critical':
            params = self.ISYcriticalParams
            #LOGGER.debug ('Critial: ' + str(params) )
            if params:
                for key in params:
                    value = self.TPW.getISYvalue(key, self.id)
                    #LOGGER.debug('Update ISY drivers :' + str(key)+ '  value: ' + str(value) )
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

    def discover(self, command=None):
        #LOGGER.debug('discover zones')
        self.nodeDefineDone = True

    def ISYupdate (self, command):
        LOGGER.debug('ISY-update called')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            #self.reportDrivers()
 
    commands = { 'UPDATE': ISYupdate}

    if PG_CLOUD_ONLY:
        drivers= [{'driver': 'GV1', 'value':0, 'uom':30}
                 ,{'driver': 'GV2', 'value':0, 'uom':30}
                 ,{'driver': 'GV3', 'value':0, 'uom':30}
                 ,{'driver': 'GV4', 'value':0, 'uom':30}
                 ,{'driver': 'GV5', 'value':0, 'uom':30}
                 ,{'driver': 'GV6', 'value':0, 'uom':30}
                 ,{'driver': 'GV7', 'value':0, 'uom':30}
                 ,{'driver': 'GV8', 'value':0, 'uom':30}
                 ,{'driver': 'GV9', 'value':0, 'uom':30}
                 ,{'driver': 'GV10', 'value':0, 'uom':30}
                 ,{'driver': 'GV11', 'value':0, 'uom':30}
                 ,{'driver': 'GV12', 'value':0, 'uom':30}
                 ,{'driver': 'GV13', 'value':0, 'uom':30}
                 ,{'driver': 'GV14', 'value':0, 'uom':30}
                 ,{'driver': 'GV15', 'value':0, 'uom':51}
                 ,{'driver': 'GV16', 'value':0, 'uom':30}
                 ,{'driver': 'GV17', 'value':0, 'uom':30}   
                 ,{'driver': 'GV18', 'value':0, 'uom':25}
                 ,{'driver': 'GV19', 'value':0, 'uom':25}
                 ,{'driver': 'GV20', 'value':0, 'uom':25}
        ] 

if __name__ == "__main__":
    try:
        #LOGGER.info('Starting Tesla Power Wall Controller')
        polyglot = polyinterface.Interface('Tesla Power Wall')
        polyglot.start()
        control = TeslaPWController(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
