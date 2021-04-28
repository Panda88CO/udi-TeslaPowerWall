#!/usr/bin/env python3
import requests
#from subprocess import call
import json
import os 
import polyinterface
LOGGER = polyinterface.LOGGER


class TeslaInfo:
    def __init__ (self, mIPaddress, mAPIkey, mISYcontrollerName):
        # Note all xxIDs must be lower case without special characters (ISY requirement)
        self.systemID = mISYcontrollerName
  
        self.sData = {     self.systemID: {  'ISYnode':{ 'nlsICON' :'Electricity'
                                                ,'sends'   :  ['DON', 'DOF']
                                                ,'accepts' : {'UPDATE'          : {   'ISYtext' :'Update System Data'
                                                                                    ,'ISYeditor' : None} 
                                                             } 
                                                }
                                    ,'KeyInfo' : {
                                         'sChargeLevel':{
                                             'GETstr': None
                                            ,'PUTstr': None
                                            ,'Active': None 
                                            ,'ISYeditor':{   
                                                     'ISYuom':None
                                                    ,'ISYmin':None
                                                    ,'ISYmax':None
                                                    ,'ISYsubset':None
                                                    ,'ISYstep':None
                                                    ,'ISYprec':None }
                                            , 'ISYnls': {    
                                                     'nlsTEXT' : 'Zone Name' 
                                                    ,'nlsValues' : None 
                                                        }  
                                                }  
                                        ,'sGridStatus' :{
                                             'GETstr': '/api/zone/setpoint/'
                                            ,'PUTstr': '/api/zone/setpoint/'
                                            ,'Active': None 
                                            ,'ISYeditor':{   
                                                     'ISYuom':17
                                                    ,'ISYmin':60
                                                    ,'ISYmax':90
                                                    ,'ISYsubset':None
                                                    ,'ISYstep':0.5
                                                    ,'ISYprec':1 }
                                            , 'ISYnls': {    
                                                     'nlsTEXT' : 'Set Temp' 
                                                    ,'nlsValues' : None
                                                        }
                                                    }
                                        ,'mStatus':{ 
                                             'GETstr': '/api/zone/status/'
                                            ,'PUTstr': '/api/zone/status/'
                                            ,'Active': None 
                                            ,'ISYeditor':{   
                                                     'ISYuom': 25
                                                    ,'ISYmin':None
                                                    ,'ISYmax':None
                                                    ,'ISYsubset': '0-1'
                                                    ,'ISYstep':None
                                                    ,'ISYprec':None }
                                            ,'ISYnls': {    
                                                     'nlsTEXT' : 'Zone state'
                                                    ,'nlsValues' : {0:'Off', 1:'On' }
                                                        }
                                                    }
           
                                    }
                                    ,'data' :{}
                                    ,'SensorCapability' : {}
                                    ,'GETkeysList' :{}
                                    ,'PUTkeysList' :{}
                        }
                    }
                
        
        #self.setupStruct = {'nodeDef': nodeNbr: { 'nodeDef':{}
        ##                                    ,'sts':{}
        #                                  ,'cmds':{
        #                                            'sends':{}
        #                                            ,'accepts':{}
        #                                            } 
        #                                    }
        #                        }
        #            ,'editors':{id:Name, range:{}}
        #            ,'nls':{}
        #                }
        
        self.nodeCount = 0
        self.setupFile = { 'nodeDef':{}
                            ,'editors':{}
                            ,'nls':{}}

        
        self.APIKey = 'apikey'
        self.APIStr = self.APIKey + '=' + mAPIkey

        self.IP ='http://'+ mIPaddress

        self.RESPONSE_OK = '<Response [200]>'
        self.RESPONSE_NO_SUPPORT = '<Response [400]>'
        self.RESPONSE_NO_RESPONSE = '<Response [404]>'
        self.NaNlist= [-32768 , -3276.8 ]
        


        #Dummy check to see if there is connection to Messana system)
        if not(self.checkMessanaConnection()):
            LOGGER.debug('Error Connecting to MessanaSystem')
        else:  
            LOGGER.info('Extracting Information about Messana System')
            self. setMessanaCredentials (mIPaddress, mAPIkey) 
            # Need SystemCapability function               
            self.getSystemCapability()
            self.updatesData('all')
            LOGGER.debug(self.systemID + ' added')
 
            self.addSystemDefStruct(self.systemID)

 

            LOGGER.info ('Creating Setup file')
            self.createSetupFiles('./profile/nodedef/nodedefs.xml','./profile/editor/editors.xml', './profile/nls/en_us.txt')
            self.ISYmap = self.createISYmapping()


    def createISYmapping(self):
        temp = {}
        for nodes in self.setupFile['nodeDef']:
            temp[nodes]= {}
            for mKeys in self.setupFile['nodeDef'][nodes]['sts']:
                for ISYkey in self.setupFile['nodeDef'][nodes]['sts'][mKeys]:
                    if ISYkey != 'ISYInfo':
                        temp[nodes][ISYkey] = {}
                        temp[nodes][ISYkey].update({'messana': mKeys})
                        temp[nodes][ISYkey].update({'editor': self.setupFile['nodeDef'][nodes]['sts'][mKeys][ISYkey]})
        #LOGGER.debug(temp) 
        return (temp)

    def setMessanaCredentials (self, mIPaddress, APIkey):
        self.mIPaddress = mIPaddress
        self.APIKeyVal = APIkey



    def getnodeISYdriverInfo(self, node, nodeNbr, mKey):
        info = {}
        if mKey in self.setupFile['nodeDef'][ self.systemID]['sts']:
            keys = list(self.setupFile['nodeDef'][ self.systemID]['sts'][mKey].keys())
            info['driver'] = keys[0]
            tempData =  self.GETsData(mKey)
            if tempData['statusOK']:
                val = tempData['data']        
                if val in  ['Celcius', 'Fahrenheit']:
                    if val == 'Celcius':
                        val = 0
                    else:  
                        val = 1 
                info['value'] = val
            else:
                info['value'] = ''
            editor = self.setupFile['nodeDef'][ self.systemID]['sts'][mKey][keys[0]]

            info['uom'] = self.setupFile['editors'][editor]['ISYuom']
        return(info)

    def checkValidNodeCommand(self, key, node, nodeNbr):
        exists = True
        mCmd = self.sData[node]['ISYnode']['accepts'][key]['ISYeditor']
        if mCmd != None:
            if not(mCmd in self.sData[node]['PUTkeysList'][nodeNbr]):
                exists = False
        return(exists)



    def addNodeDefStruct(self, nodeNbr, nodeName, nodeId):
        self.keyCount = 0
        nodeId.lower()
        LOGGER.debug('addNodeDefStruct: ' + nodeName+ ' ' + str(nodeNbr) + ' '+nodeId)
        self.name = nodeName+str(nodeNbr)
        self.nlsKey = 'nls' + self.name
        self.nlsKey.lower()
        #editorName = nodeName+'_'+str(keyCount)
        self.setupFile['nodeDef'][self.name]={}
        self.setupFile['nodeDef'][self.name]['CodeId'] = nodeId
        self.setupFile['nodeDef'][self.name]['nlsId'] = self.nlsKey
        self.setupFile['nodeDef'][self.name]['nlsNAME']=self.sData[nodeName]['data'][nodeNbr]['mName']
        self.setupFile['nodeDef'][self.name]['nlsICON']=self.sData[nodeName]['ISYnode']['nlsICON']
        self.setupFile['nodeDef'][self.name]['sts']={}

        #for mKey in self.sData[nodeName]['data'][nodeNbr]: 
        for mKey in self.sData[nodeName]['GETkeysList'][nodeNbr]:             
            #make check if system has unit installed
            if self.sData[nodeName]['KeyInfo'][mKey]['ISYeditor']['ISYuom']:
                self.keyCount = self.keyCount + 1
                editorName = nodeName.upper()+str(nodeNbr)+'_'+str(self.keyCount)
                nlsName = editorName
                ISYvar = 'GV'+str(self.keyCount)
                self.setupFile['nodeDef'][self.name]['sts'][mKey]={ISYvar:editorName}
                self.setupFile['editors'][editorName]={}
                #self.setupFile['nls'][editorName][ISYparam]
                for ISYparam in self.sData[nodeName]['KeyInfo'][mKey]['ISYeditor']:
                    if self.sData[nodeName]['KeyInfo'][mKey]['ISYeditor'][ISYparam]!= None:
                        self.setupFile['editors'][editorName][ISYparam]=self.sData[nodeName]['KeyInfo'][mKey]['ISYeditor'][ISYparam]

                if self.sData[nodeName]['KeyInfo'][mKey]['ISYnls']:
                    self.setupFile['nls'][nlsName]={}
                for ISYnls in self.sData[nodeName]['KeyInfo'][mKey]['ISYnls']:
                    #LOGGER.debug( mKey + ' ' + ISYnls)
                    if  self.sData[nodeName]['KeyInfo'][mKey]['ISYnls'][ISYnls]:      
                        self.setupFile['nls'][nlsName][ISYnls] = self.sData[nodeName]['KeyInfo'][mKey]['ISYnls'][ISYnls]
                        if ISYnls == 'nlsValues':
                            self.setupFile['editors'][editorName]['nlsKey'] = nlsName 

        self.setupFile['nodeDef'][self.name]['cmds']= {}
        if 'accepts' in self.sData[nodeName]['ISYnode']:
            self.setupFile['nodeDef'][self.name]['cmds']['accepts']={}
            for key in  self.sData[nodeName]['ISYnode']['accepts']:
                if self.checkValidNodeCommand(key, nodeName, nodeNbr ):
                    if self.sData[nodeName]['ISYnode']['accepts'][key]['ISYeditor'] in self.setupFile['nodeDef'][self.name]['sts']:
                        self.setupFile['nodeDef'][self.name]['cmds']['accepts'][key]= self.setupFile['nodeDef'][self.name]['sts'][self.sData[nodeName]['ISYnode']['accepts'][key]['ISYeditor']]
                        self.setupFile['nodeDef'][self.name]['cmds']['accepts'][key]['ISYInfo']=self.sData[nodeName]['ISYnode']['accepts'][key]
                    else:
                        self.setupFile['nodeDef'][self.name]['cmds']['accepts'][key]={}
                        self.setupFile['nodeDef'][self.name]['cmds']['accepts'][key]['ISYInfo']= self.sData[nodeName]['ISYnode']['accepts'][key]
                else:
                    LOGGER.debug('Removed "accepts" for : ' + key + ' not supported')
                    
        if 'sends' in self.sData[nodeName]['ISYnode']:         
            self.setupFile['nodeDef'][self.name]['cmds']['sends'] = self.sData[nodeName]['ISYnode']['sends']                                 
        return()

    def addSystemDefStruct(self, nodeId):
        self.keyCount = 0
        nodeId.lower()
        self.nlsKey= 'nls' + nodeId
        self.nlsKey.lower()
        #LOGGER.debug('addSystemDefStruct: ' + nodeId)
        self.setupFile['nodeDef'][ self.systemID]={}
        self.setupFile['nodeDef'][ self.systemID]['CodeId'] = nodeId
        self.setupFile['nodeDef'][ self.systemID]['nlsId'] = self.nlsKey
        self.setupFile['nodeDef'][ self.systemID]['nlsNAME']=self.sData[ self.systemID]['data']['mName']
        self.setupFile['nodeDef'][ self.systemID]['nlsICON']=self.sData[ self.systemID]['ISYnode']['nlsICON']
        self.setupFile['nodeDef'][ self.systemID]['sts']={}

        #for mKey in self.sData[ self.systemID]['data']: 
        for mKey in self.sData[ self.systemID]['GETkeysList']:    
            #make check if system has unit installed
            if self.sData[ self.systemID]['KeyInfo'][mKey]['ISYeditor']['ISYuom']:
                if ((self.sData[ self.systemID]['KeyInfo'][mKey]['ISYeditor']['ISYuom'] == 112
                   and self.sData[ self.systemID]['data'][mKey] != 0)
                   or self.sData[ self.systemID]['KeyInfo'][mKey]['ISYeditor']['ISYuom'] != 112):
                    self.keyCount = self.keyCount + 1
                    editorName = 'SYSTEM_'+str(self.keyCount)
                    nlsName = editorName
                    ISYvar = 'GV'+str(self.keyCount)
                    self.setupFile['nodeDef'][ self.systemID]['sts'][mKey]={ISYvar:editorName}
                    self.setupFile['editors'][editorName]={}
                    #self.setupFile['nls'][editorName][ISYparam]
                    for ISYparam in self.sData[ self.systemID]['KeyInfo'][mKey]['ISYeditor']:
                        if self.sData[ self.systemID]['KeyInfo'][mKey]['ISYeditor'][ISYparam]!= None:
                            self.setupFile['editors'][editorName][ISYparam]=self.sData[ self.systemID]['KeyInfo'][mKey]['ISYeditor'][ISYparam]

                    if self.sData[ self.systemID]['KeyInfo'][mKey]['ISYnls']:
                        self.setupFile['nls'][nlsName]={}
                    for ISYnls in self.sData[ self.systemID]['KeyInfo'][mKey]['ISYnls']:
                        #LOGGER.debug( mKey + ' ' + ISYnls)
                        if  self.sData[ self.systemID]['KeyInfo'][mKey]['ISYnls'][ISYnls]:      
                            self.setupFile['nls'][nlsName][ISYnls] = self.sData[ self.systemID]['KeyInfo'][mKey]['ISYnls'][ISYnls]
                            if ISYnls == 'nlsValues':
                                self.setupFile['editors'][editorName]['nlsKey'] = nlsName
        
        self.setupFile['nodeDef'][ self.systemID]['cmds']={}
        if 'accepts' in self.sData[ self.systemID]['ISYnode']:
            self.setupFile['nodeDef'][ self.systemID]['cmds']['accepts'] = {}
            for key in  self.sData[ self.systemID]['ISYnode']['accepts']:     
                if self.sData[ self.systemID]['ISYnode']['accepts'][key]['ISYeditor'] in self.setupFile['nodeDef'][ self.systemID]['sts']:
                    mVal = self.sData[ self.systemID]['ISYnode']['accepts'][key]['ISYeditor']
                    self.setupFile['nodeDef'][ self.systemID]['cmds']['accepts'][key]= self.setupFile['nodeDef'][ self.systemID]['sts'][mVal]
                    self.setupFile['nodeDef'][ self.systemID]['cmds']['accepts'][key]['ISYInfo']=self.sData[ self.systemID]['ISYnode']['accepts'][key]
                else:
                    self.setupFile['nodeDef'][ self.systemID]['cmds']['accepts'][key]= {}
                    self.setupFile['nodeDef'][ self.systemID]['cmds']['accepts'][key]['ISYInfo']= self.sData[ self.systemID]['ISYnode']['accepts'][key]   
        if 'sends' in self.sData[ self.systemID]['ISYnode']:
            self.setupFile['nodeDef'][ self.systemID]['cmds']['sends']=self.sData[ self.systemID]['ISYnode']['sends']                              
        return()



   
    
    def GETsData(self, mKey):
        LOGGER.debug('GETsData')

    def PUTsData(self, mKey, value):
            LOGGER.debug('PUTsData')     
  
    def GETNodeData(self, mNodeKey, nodeNbr, mKey):
        LOGGER.debug('GETNodeData')       
 
    # New Functions Need to be tested
    def getNodeKeys (self, nodeNbr, nodeKey, cmdKey):
        keys = []
        if len(self.sData[nodeKey]['GETkeysList'][nodeNbr]) == 0:
            LOGGER.debug('NodeCapability must be run first')
        else:
            if cmdKey == 'PUTstr':
                for mKey in self.sData[nodeKey]['PUTkeysList'][nodeNbr]:
                    if self.sData[nodeKey]['KeyInfo'][mKey][cmdKey] != None:
                        keys.append(mKey)
            else:
                for mKey in self.sData[nodeKey]['GETkeysList'][nodeNbr]:
                    if self.sData[nodeKey]['KeyInfo'][mKey][cmdKey] != None:
                        keys.append(mKey)             
        return(keys)

    def updateNodeData(self, nodeNbr, nodeKey):
        LOGGER.info('updatNodeData: ' + str(nodeNbr) + ' ' + nodeKey)

    
    def pullNodeDataIndividual(self, nodeNbr, nodeKey, mKey): 
        Data = self.GETNodeData(nodeKey, nodeNbr, mKey)
        return(Data)
    
    def checkGETNode(self,  nodeKey, nodeNbr, mKey): 
        LOGGER.debug ('checkGETNode')

    def pushNodeDataIndividual(self, NodeNbr, NodeKey, mKey, value):
        LOGGER.debug ('pushNodeDataIndividual')

    #Setup file generation 
    def createSetupFiles(self, nodeDefFileName, editorFileName, nlsFileName):
        #LOGGER.debug ('Create Setup Files')
        status = True
        try:
            LOGGER.debug('opening files')
            if not(os.path.exists('./profile')):
                os.mkdir('./profile')       
            if not(os.path.exists('./profile/editor')):
                os.mkdir('./profile/editor')
            if not(os.path.exists('./profile/nls')):
                os.mkdir('./profile/nls')           
            if not(os.path.exists('./profile/nodedef')):
                os.mkdir('./profile/nodedef')
            nodeFile = open(nodeDefFileName, 'w+')
            editorFile = open(editorFileName, 'w+')
            nlsFile = open(nlsFileName, 'w+')
            #LOGGER.debug('Opening Files OK')

            editorFile.write('<editors> \n')
            nodeFile.write('<nodeDefs> \n')
            for node in self.setupFile['nodeDef']:
                nodeDefStr ='   <nodeDef id="' + self.setupFile['nodeDef'][node]['CodeId']+'" '+ 'nls="'+self.setupFile['nodeDef'][node]['nlsId']+'">\n'
                #LOGGER.debug(nodeDefStr)
                nodeFile.write(nodeDefStr)
                nodeFile.write('      <editors />\n')
                nodeFile.write('      <sts>\n')
                #nlsStr = 'ND-'+self.setupFile['nodeDef'][node]['nlsId']+'-NAME = '+self.setupFile['nodeDef'][node]['nlsNAME']+ '\n'
                nlsStr = 'ND-'+self.setupFile['nodeDef'][node]['CodeId']+'-NAME = '+self.setupFile['nodeDef'][node]['nlsNAME']+ '\n'
                nlsFile.write(nlsStr)
                #nlsStr = 'ND-'+self.setupFile['nodeDef'][node]['nlsId']+'-ICON = '+self.setupFile['nodeDef'][node]['nlsICON']+ '\n'
                nlsStr = 'ND-'+self.setupFile['nodeDef'][node]['CodeId']+'-ICON = '+self.setupFile['nodeDef'][node]['nlsICON']+ '\n'
                nlsFile.write(nlsStr)
                for acceptCmd in self.setupFile['nodeDef'][node]['cmds']['accepts']:
                    cmdName =  self.setupFile['nodeDef'][node]['cmds']['accepts'][acceptCmd]['ISYInfo']['ISYtext']
                    nlsStr = 'CMD-' + self.setupFile['nodeDef'][node]['nlsId']+'-'+acceptCmd+'-NAME = ' + cmdName +'\n'
                    nlsFile.write(nlsStr)
                    #LOGGER.debug(nlsStr)

                for status in self.setupFile['nodeDef'][node]['sts']:
                    for statusId in self.setupFile['nodeDef'][node]['sts'][status]:
                        if statusId != 'ISYInfo':
                            nodeName = self.setupFile['nodeDef'][node]['sts'][status][statusId]
                            nodeDefStr =  '         <st id="' + statusId+'" editor="'+nodeName+'" />\n'
                            #LOGGER.debug(nodeDefStr)
                            nodeFile.write(nodeDefStr)
                            editorFile.write( '  <editor id = '+'"'+nodeName+'" > \n')
                            editorStr = '     <range '
                            for key in self.setupFile['editors'][nodeName]:
                                if key == 'ISYsubset':
                                    editorStr = editorStr + ' subset="'+ str(self.setupFile['editors'][nodeName][key])+'"'
                                elif key == 'ISYuom':
                                    editorStr = editorStr + ' uom="'+ str(self.setupFile['editors'][nodeName][key])+'"'
                                elif key == 'ISYmax':
                                    editorStr = editorStr + ' max="'+ str(self.setupFile['editors'][nodeName][key])+'"'
                                elif key == 'ISYmin': 
                                    editorStr = editorStr + ' min="'+ str(self.setupFile['editors'][nodeName][key])+'"'
                                elif key == 'ISYstep':
                                    editorStr = editorStr + ' step="'+ str(self.setupFile['editors'][nodeName][key])+'"'                  
                                elif key == 'ISYprec': 
                                    editorStr = editorStr + ' prec="'+ str(self.setupFile['editors'][nodeName][key])+'"'
                                elif key == 'ISYsubset': 
                                    editorStr = editorStr + ' subset="'+ str(self.setupFile['editors'][nodeName][key])+'"'
                                elif key == 'nlsKey': 
                                    nlsEditorKey = str(self.setupFile['editors'][nodeName][key])
                                    editorStr = editorStr + ' nls="'+ nlsEditorKey+'"'
                                else:
                                    LOGGER.debug('unknown editor keyword: ' + str(key))
                            editorStr = editorStr + ' />\n'
                            #LOGGER.debug(editorStr)
                            editorFile.write(editorStr)
                            editorFile.write('</editor>\n')

                        for nlsInfo in self.setupFile['nls'][nodeName]:
                            if statusId != 'ISYInfo':
                                if nlsInfo == 'nlsTEXT':
                                    nlsStr = 'ST-' + self.setupFile['nodeDef'][node]['nlsId']+'-'+statusId+'-NAME = '
                                    nlsStr = nlsStr + self.setupFile['nls'][nodeName][nlsInfo] + '\n'
                                    nlsFile.write(nlsStr)
                                elif nlsInfo == 'nlsValues':
                                    nlsValues = 0
                                    for key in self.setupFile['nls'][nodeName][nlsInfo]:
                                        nlsStr = nlsEditorKey+'-'+str(nlsValues)+' = '+self.setupFile['nls'][nodeName][nlsInfo][key]+'\n'
                                        nlsFile.write(nlsStr)
                                        nlsValues = nlsValues + 1
                                #LOGGER.debug(nlsStr)

                nodeFile.write('      </sts>\n')
                nodeFile.write('      <cmds>\n')                
                nodeFile.write('         <sends>\n')            
                if self.setupFile['nodeDef'][node]['cmds']:
                    if len(self.setupFile['nodeDef'][node]['cmds']['sends']) != 0:
                        for sendCmd in self.setupFile['nodeDef'][node]['cmds']['sends']:
                            cmdStr = '            <cmd id="' +sendCmd +'" /> \n'
                            #LOGGER.debug(cmdStr)
                            nodeFile.write(cmdStr)
                nodeFile.write('         </sends>\n')               
                nodeFile.write('         <accepts>\n')      
                if self.setupFile['nodeDef'][node]['cmds']:
                    if 'accepts' in self.setupFile['nodeDef'][node]['cmds']:
                        for acceptCmd in self.setupFile['nodeDef'][node]['cmds']['accepts']:
                            
                            if len(self.setupFile['nodeDef'][node]['cmds']['accepts'][acceptCmd]) != 1:
                                for key in self.setupFile['nodeDef'][node]['cmds']['accepts'][acceptCmd]:
                                    if key != 'ISYInfo':
                                        cmdStr = '            <cmd id="' +acceptCmd+'" > \n'     
                                        nodeFile.write(cmdStr)  
                                        cmdStr = '               <p id="" editor="'
                                        cmdStr = cmdStr + self.setupFile['nodeDef'][node]['cmds']['accepts'][acceptCmd][key]+ '" init="' + key +'" /> \n' 
                                        #LOGGER.debug(cmdStr)                              
                                        nodeFile.write(cmdStr)
                                        nodeFile.write('            </cmd> \n')
                            else:
                                cmdStr = '            <cmd id="' +acceptCmd+'" /> \n' 
                                #LOGGER.debug(cmdStr)
                                nodeFile.write(cmdStr)  
                nodeFile.write('         </accepts>\n')                   

                nodeFile.write('      </cmds>\n')                
                                    
                nodeFile.write('   </nodeDef> \n')

            nodeFile.write('</nodeDefs> \n' )
            nodeFile.close()
            editorFile.write('</editors> \n')
            editorFile.close()
            nlsFile.close()
        
        except:
            LOGGER.debug('something went wrong in creating setup files')
            status = False
            nodeFile.close()
            editorFile.close()
            nlsFile.close()
        return(status)



    #System
    def updatesData(self, level):
        LOGGER.debug('Update Messana Sytem Data')
        sysData = {}
        DataOK = True
       
        if level == 'active':
            for mKey in self.systemActiveKeys():
                sysData= self.pullsDataIndividual(mKey)
                if not(sysData['statusOK']):
                    LOGGER.debug('Error System Active GET: ' + mKey)
                    DataOK = False  
        elif level == 'all':
            for mKey in self.systemPullKeys():
                sysData= self.pullsDataIndividual(mKey)
                if not(sysData['statusOK']):
                    LOGGER.debug('Error System Active GET: ' + mKey)
                    DataOK = False 
        else:
            LOGGER.debug('Unknown level: ' + level)
            DataOK = False               
        return(DataOK)



    def pullsDataIndividual(self, mKey):
        #LOGGER.debug('MessanaInfo pull System Data: ' + mKey)
        return(self.GETsData(mKey) )
                 

    def pushsDataIndividual(self, mKey, value):
        sysData={}
        #LOGGER.debug('MessanaInfo push System Data: ' + mKey)       
        sysData = self.PUTsData(mKey, value)
        if sysData['statusOK']:
            return(True)
        else:
            LOGGER.debug(sysData['error'])
            return(False) 

     
    def getSystemCapability(self):
        LOGGER.debug('getSystemCapability')     
        

    def systemPullKeys(self):
        #LOGGER.debug('systemPullKeys')
        return(self.sData[self.systemID]['GETkeysList'])

    def systemPushKeys(self):
        #LOGGER.debug('systemPushKeys')
        return(self.sData[self.systemID]['PUTkeysList'])  
            
    def systemActiveKeys(self):
        #LOGGER.debug('systemActiveKeys')
        keys=[]
        for mKey in self.sData[self.systemID]['GETkeysList']:
            if self.sData[self.systemID]['KeyInfo'][mKey]['Active'] != None:
                keys.append(mKey)
        return(keys)  
            
    def getSystemISYValue(self, ISYkey):
        messanaKey = self.ISYmap[ self.systemID][ISYkey]['messana']
        systemPullKeys = self.systemPullKeys()
        if messanaKey in systemPullKeys:
            data = self.pullsDataIndividual(messanaKey)
            if data['statusOK']:
                val = data['data']        
                if val in  ['Celcius', 'Fahrenheit']:
                    if val == 'Celcius':
                        val = 0
                    else:  
                        val = 1 
                systemValue = val
                status = True
            else:
                systemValue = None
                status = False
        else:
            status = False
            systemValue = None
        return (status, systemValue)

    def PUTSystemISYValue(self, ISYkey, systemValue):
        messanaKey = self.ISYmap[ self.systemID][ISYkey]['messana']
        systemPushKeys = self.systemPushKeys()
        status = False
        if messanaKey in systemPushKeys:
            status = self.pushsDataIndividual(messanaKey, systemValue)
        return(status)
    
    def getMessanaSystemKey(self, ISYkey):
        return(self.ISYmap[ self.systemID][ISYkey]['messana'])

    def getSystemISYdriverInfo(self, mKey):
        info = {}
        if mKey in self.setupFile['nodeDef'][ self.systemID]['sts']:
            keys = list(self.setupFile['nodeDef'][ self.systemID]['sts'][mKey].keys())
            info['driver'] = keys[0]
            tempData =  self.GETsData(mKey)
            if tempData['statusOK']:
                val = tempData['data']        
                if val in  ['Celcius', 'Fahrenheit']:
                    if val == 'Celcius':
                        val = 0
                    else:  
                        val = 1 
                info['value'] = val
            else:
                info['value'] = ''
            editor = self.setupFile['nodeDef'][ self.systemID]['sts'][mKey][keys[0]]

            info['uom'] = self.setupFile['editors'][editor]['ISYuom']
        return(info)

 