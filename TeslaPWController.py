#!/usr/bin/env python3
PG_CLOUD_ONLY = False

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface

    PG_CLOUD_ONLY = True

#from os import truncate
import sys
from  TeslaInfo import tesla_info
#import ISYprofile 
from TeslaPWSetupNode import teslaPWSetupNode

import polyinterface
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
        self.drivers = []
        self.nodeDefineDone = False
        self.TPW = None



    def defineLocalInputParams(self):
        LOGGER.debug('defineLocalInputParams')
        self.addNotice('Input IP address, email and password used to log in to local power wall - 192.168.x.x')  
        self.IPAddress = self.getCustomParam('LOCAL IP_ADDRESS - Leave ')
        if self.IPAddress is None:
            self.addNotice('Please Set IP address of Tesla Power Wall system (IP_ADDRESS) - E.g. 192.168.1.2') 
            LOGGER.info('IP address not set')
            self.addCustomParam({'IP_ADDRESS': '192.168.1.100'})

        self.LocalUserEmail = self.getCustomParam('LOCAL USER EMAIL)')
        if self.LocalUserEmail is None:
            self.addNotice('Please Set Tesla Power Wall (local) login email (LOCAL_USER_EMAIL) - E.g. nobody@email.com')
            LOGGER.info('check_params: local user email not specified')
            self.addCustomParam({'LOCAL_USER_EMAIL': 'nobody@email.com'})

        self.LocalUserPassword= self.getCustomParam('USER_PASSWORD')
        if self.LocalUserPassword is None:
            self.addNotice('Please Set Tesla Power Wall (local) password (USER_PASSWORD) - E.g. XXXXXXXX')
            LOGGER.info('check_params: local user password not specified')
            self.addCustomParam({'LOCAL_USER_PASSWORD': 'XXXXXXXX'})

    def defineAccessInputParam(self):
        LOGGER.debug('defineAccessInputParam')
        if PG_CLOUD_ONLY:
            self.addCustomParam({'ACCESS':'CLOUD'})
            self.addCustomParam({'LOGFILE':'DISABLED'})
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
        self.CloudUserEmail = self.getCustomParam('CLOUD USER EMAIL)')
        if self.CloudUserEmail is None:
            self.addNotice('Please Set Tesla Power Wall Cloud login email (CLOUD_USER_EMAIL) - E.g. nobody@email.com')
            LOGGER.debug('check_params: cloud user email not specified')
            self.addCustomParam({'CLOUD_USER_EMAIL': 'nobody@email.com'})

        self.CloudUserPassword = self.getCustomParam('CLOUD USER_PASSWORD')
        if self.CloudUserPassword is None:
            self.addNotice('Please Set Tesla Power Wall Cloud password (_CLOUD_USER_PASSWORD) - E.g. XXXXXXXX')
            LOGGER.debug('check_params: cloud user password not specified')
            self.addCustomParam({'CLOUD_USER_PASSWORD': 'XXXXXXXX'})
        self.addNotice('Please restart Node server after setting the parameters')


    def start(self):
        self.removeNoticesAll()
        self.access = ''
        #LOGGER.info('Start Tesla Power Wall Main New')
        self.localAccess= False # Assume no local access initially
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
                    LOGGER.info('LogFile enabled @ ./daailyData')
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
                    LOGGER.info('No Local USER_EMAIL retrieved:')
                    self.localAccess = False
                else:
                    LOGGER.info('Local USER_EMAIL retrieved: '+ self.localUserEmail)
                self.localUserPassword =self.getCustomParam('LOCAL_USER_PASSWORD')
                if self.localUserPassword == None:
                    LOGGER.info('No USER_PASSWORD:')
                    self.LocalAccess = False
                else:
                    LOGGER.debug('LOCAL USER_PASSWORD retrieved: XXXXXXXX')
                
                if not(self.localAccess):
                    self.defineLocalInputParams()                              
            if self.access.upper() == 'CLOUD' or self.access.upper() == 'BOTH':
                self.cloudAccess= True
                self.cloudUserEmail = self.getCustomParam('CLOUD_USER_EMAIL')
                if self.cloudUserEmail == None:
                    LOGGER.info('No cloud USER_EMAIL retrieved:')
                    self.cloudAccess = False
                else:
                    LOGGER.debug('Cloud USER_EMAIL retrieved: '+ self.cloudUserEmail)
                self.cloudUserPassword =self.getCustomParam('CLOUD_USER_PASSWORD')
                if self.cloudUserPassword == None:
                    LOGGER.info('No cloud USER_PASSWORD:')
                    self.cloudAccess = False
                else:
                    LOGGER.debug('CLOUD_USER_PASSWORD retrieved: XXXXXXXX')
                if not(self.cloudAccess):
                    self.defineCloudInputParams()
        else:
            if self.access.upper() == 'CLOUD':
                self.cloudAccess = True
                self.cloudUserEmail = self.getCustomParam('CLOUD_USER_EMAIL')
                if self.cloudUserEmail == None:
                    LOGGER.info('No cloud USER_EMAIL retrieved:')
                    self.cloudAccess = False
                else:
                    LOGGER.info('Cloud USER_EMAIL retrieved: '+ self.cloudUserEmail)
                self.cloudUserPassword =self.getCustomParam('CLOUD_USER_PASSWORD')
                if self.cloudUserPassword == None:
                    LOGGER.info('No cloud USER_PASSWORD:')
                    self.cloudAccess = False
                else:
                    LOGGER.debug('CLOUD_USER_PASSWORD retrieved: XXXXXXXX')
            if (self.cloudUserEmail == None) or (self.cloudUserPassword == None):
                self.defineCloudInputParams()
        if not(self.cloudAccess) or not(self.localAccess):
                self.stop()

        #LOGGER.info('Connecting to Tesla Power Wall')
        try:
    
            if self.access == 'BOTH':
                LOGGER.info('BOTH selected')
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
            self.TPW.createLogFile(self.logFile)
            self.ISYparams = self.TPW.supportedParamters(self.id)
            self.ISYcriticalParams = self.TPW.criticalParamters(self.id)

            for key in self.ISYparams:
                info = self.ISYparams[key]
                if info != {}:
                    value = self.TPW.getISYvalue(key, self.id)
                    self.drivers.append({'driver':key, 'value':value, 'uom':info['uom'] })
                    LOGGER.debug('driver' + str(key)+ ' value:' + str(value) + ' uom:' + str(info['uom']) )
            
            LOGGER.info('Creating Setup Node')
            nodeList = self.TPW.getNodeIdList()
            LOGGER.debug(nodeList)
            for node in nodeList:
                LOGGER.debug(node)
                name = self.TPW.getNodeName(node)
                self.addNode(teslaPWSetupNode(self, self.address, node, name))
            
            #self.heartbeat()
            
            self.TPW.pollSystemData('all')
            self.updateISYdrivers('all')
            self.reportDrivers()
            self.nodeDefineDone = True
        except:
            LOGGER.debug('did not connect to power wall')

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
            if self.TPW.pollSystemData('critical'):
                self.updateISYdrivers('critical')
            else:
                LOGGER.debug ('Problem polling data from Tesla system')
        else:
            LOGGER.debug('waiting for system/nodes to get created')
        #LOGGER.debug('Nodes : ' + self.nodes)
        for node in self.nodes:
            LOGGER.debug('Node : ' + node)
            if node != self.address and node != 'controller':
                self.nodes[node].shortPoll()
        

    def longPoll(self):
        LOGGER.info('Tesla Power Wall  Controller longPoll')
        self.heartbeat()
        if self.nodeDefineDone:
            if self.TPW.pollSystemData('all'):
                self.updateISYdrivers('all')
            #self.reportDrivers() 
        else:
            LOGGER.debug('waiting for system/nodes to get created')
        for node in self.nodes:
            LOGGER.debug('Node : ' + node)
            if node != self.address and node != 'controller':
                self.nodes[node].longPoll()
        
    def updateISYdrivers(self, level):
        LOGGER.debug('System updateISYdrivers')
        params = []
        #LOGGER.debug(self.id)
        #LOGGER.debug(self.ISYparams)
        if level == 'all':
            params = self.ISYparams
        elif level == 'critical':
            params = self.ISYparams
        else:
            LOGGER.debug('Wrong parameter passed: ' + str(level))
        #LOGGER.debug(params)
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



    def ISYupdate (self, command):
        LOGGER.info('ISY-update called')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            self.reportDrivers()
 

    commands = { 'UPDATE': ISYupdate}

  
if __name__ == "__main__":
    try:
        #LOGGER.info('Starting Tesla Power Wall Controller')
        polyglot = polyinterface.Interface('Tesla Power Wall')
        polyglot.start()
        control = TeslaPWController(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
