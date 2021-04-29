#!/usr/bin/env python3
import requests
#from subprocess import call
import json
import os 
from tesla_powerwall import GridStatus, OperationMode
#import polyinterface
#LOGGER = polyinterface.LOGGER


class isyProfile:
    def __init__ (self,  ISYcontrollerName, systemName):
        # Note all xxIDs must be lower case without special characters (ISY requirement)
        self.systemID = ISYcontrollerName
        self.systemName = systemName
        self.sData  = {}
        '''
        'ISYnode' : {}

                        ,'KeyInfo' :{}
                        ,'data' : {}
                    }
        '''
        '''
        self.sData = {  self.systemID: {  'ISYnode':{ 'nlsICON' :'Electricity'
                                                ,'sends'   :  ['DON', 'DOF']
                                                ,'accepts' : {'UPDATE' : {   'ISYtext' :'Update System Data'
                                                                            ,'ISYeditor' : None} 
                                                             } 
                                                }
                                    ,'KeyInfo' : {
                                         'sChargeLevel':{
                                            'ISYeditor':{   
                                                     'ISYuom':51
                                                    ,'ISYmin':0
                                                    ,'ISYmax':100
                                                    ,'ISYsubset':None
                                                    ,'ISYstep':None
                                                    ,'ISYprec':1 }
                                            , 'ISYnls': {    
                                                     'nlsTEXT' : 'Battery Charge Level' 
                                                    ,'nlsValues' : None 
                                                        }  
                                                }  
                                         ,'sBackupLevel':{
                                            'ISYeditor':{   
                                                     'ISYuom':51
                                                    ,'ISYmin':0
                                                    ,'ISYmax':100
                                                    ,'ISYsubset':None
                                                    ,'ISYstep':None
                                                    ,'ISYprec':1 }
                                            , 'ISYnls': {    
                                                     'nlsTEXT' : 'Battery Backup Holdoff' 
                                                    ,'nlsValues' : None 
                                                        }  
                                                }  
                                        ,'sGridStatus' :{
                                            'ISYeditor':{   
                                                     'ISYuom':25
                                                    ,'ISYmin':None
                                                    ,'ISYmax':None
                                                    ,'ISYsubset':'0-3'
                                                    ,'ISYstep':None
                                                    ,'ISYprec':None }
                                            , 'ISYnls': {    
                                                     'nlsTEXT' : 'Grid Status' 
                                                    ,'nlsValues' : {0:GridStatus.CONNECTED.value
                                                                    ,1:GridStatus.ISLANEDED_READY.value
                                                                    ,2:GridStatus.ISLANEDED.value
                                                                    ,3:GridStatus.TRANSITION_TO_GRID.value }
                                                        }
                                                    }
                                        ,'sSolarSupply':{ 
                                            'ISYeditor':{   
                                                     'ISYuom': 30 #Kwatt
                                                    ,'ISYmin':0
                                                    ,'ISYmax':10
                                                    ,'ISYsubset': None
                                                    ,'ISYstep':None
                                                    ,'ISYprec':2}
                                            ,'ISYnls': {    
                                                     'nlsTEXT' : 'Solar Supply '
                                                    ,'nlsValues' : None
                                                        }
                                                    }
                                        ,'sBatterySupply':{ 
                                            'ISYeditor':{   
                                                     'ISYuom': 30 #Kwatt
                                                    ,'ISYmin':0
                                                    ,'ISYmax':10
                                                    ,'ISYsubset': None
                                                    ,'ISYstep':None
                                                    ,'ISYprec':2}
                                            ,'ISYnls': {    
                                                     'nlsTEXT' : 'Batter Supply '
                                                    ,'nlsValues' : None
                                                        }
                                                    }
                                        ,'sGridSupply':{ 
                                            'ISYeditor':{   
                                                     'ISYuom': 30 #Kwatt
                                                    ,'ISYmin':0
                                                    ,'ISYmax':10
                                                    ,'ISYsubset': None
                                                    ,'ISYstep':None
                                                    ,'ISYprec':2}
                                            ,'ISYnls': {    
                                                     'nlsTEXT' : 'Grid/Site Supply '
                                                    ,'nlsValues' : None
                                                        }
                                                    }         
                                        ,'sLoad':{ 
                                            'ISYeditor':{   
                                                     'ISYuom': 30 #Kwatt
                                                    ,'ISYmin':0
                                                    ,'ISYmax':10
                                                    ,'ISYsubset': None
                                                    ,'ISYstep':None
                                                    ,'ISYprec':2}
                                            ,'ISYnls': {    
                                                     'nlsTEXT' : 'Home/load Supply '
                                                    ,'nlsValues' : None
                                                        }
                                                    }                                            
        
                                        ,'sDailySolar':{ 
                                            'ISYeditor':{   
                                                     'ISYuom': 30 #Kwatt
                                                    ,'ISYmin':0
                                                    ,'ISYmax':2400
                                                    ,'ISYsubset': None
                                                    ,'ISYstep':None
                                                    ,'ISYprec':2}
                                            ,'ISYnls': {    
                                                     'nlsTEXT' : 'Daily Solar Generation'
                                                    ,'nlsValues' : None
                                                        }
                                                    }
                                        ,'sDailyPower':{ 
                                            'ISYeditor':{   
                                                     'ISYuom': 30 #Kwatt
                                                    ,'ISYmin':0
                                                    ,'ISYmax':10000
                                                    ,'ISYsubset': None
                                                    ,'ISYstep':None
                                                    ,'ISYprec':2}
                                            ,'ISYnls': {    
                                                     'nlsTEXT' : 'Daily Consumption'
                                                    ,'nlsValues' : None
                                                        }
                                                    }
                                         ,'sDailyGeneration':{ 
                                            'ISYeditor':{   
                                                     'ISYuom': 30 #Kwatt
                                                    ,'ISYmin':0
                                                    ,'ISYmax':10000
                                                    ,'ISYsubset': None
                                                    ,'ISYstep':None
                                                    ,'ISYprec':2}
                                            ,'ISYnls': {    
                                                     'nlsTEXT' : 'Daily Net Power'
                                                    ,'nlsValues' : None
                                                        }
                                                    }                                                   
                                        ,'sOperationMode':{ 
                                            'ISYeditor':{   
                                                     'ISYuom':25
                                                    ,'ISYmin':None
                                                    ,'ISYmax':None
                                                    ,'ISYsubset':'0-3'
                                                    ,'ISYstep':None
                                                    ,'ISYprec':None }
                                            , 'ISYnls': {    
                                                     'nlsTEXT' : 'Operation Mode' 
                                                    ,'nlsValues' : { 0:OperationMode.BACKUP.value
                                                                    ,1:OperationMode.SELF_CONSUMPTION.value
                                                                    ,2:OperationMode.AUTONOMOUS.value
                                                                    ,3:OperationMode.SITE_CONTROL.value }
                                                        }
                                                    } 
                                        ,'sConnectTesla':{ 
                                            'ISYeditor':{   
                                                     'ISYuom':25
                                                    ,'ISYmin':None
                                                    ,'ISYmax':None
                                                    ,'ISYsubset':'0-1'
                                                    ,'ISYstep':None
                                                    ,'ISYprec':None }
                                            , 'ISYnls': {    
                                                     'nlsTEXT' : 'Connected to Tesla' 
                                                    ,'nlsValues' : {0: 'False', 1: 'True'}
                                                        }                                                        
                                                    }                                                      
                                        ,'sRunning':{ 
                                            'ISYeditor':{   
                                                     'ISYuom':25
                                                    ,'ISYmin':None
                                                    ,'ISYmax':None
                                                    ,'ISYsubset':'0-1'
                                                    ,'ISYstep':None
                                                    ,'ISYprec':None }
                                            , 'ISYnls': {    
                                                     'nlsTEXT' : 'System Runing' 
                                                    ,'nlsValues' : {0: 'False', 1: 'True'}
                                                        }
                                                        
                                                    } 
                                        ,'sPowerSupplyMode':{ 
                                            'ISYeditor':{   
                                                     'ISYuom':25
                                                    ,'ISYmin':None
                                                    ,'ISYmax':None
                                                    ,'ISYsubset':'0-1'
                                                    ,'ISYstep':None
                                                    ,'ISYprec':None }
                                            , 'ISYnls': {    
                                                     'nlsTEXT' : 'In Power Supply Mode' 
                                                    ,'nlsValues' : {0: 'False', 1: 'True'}
                                                        }
                                                        
                                                    } 
                                        }
                                    ,'data' :{'name' :self.systemName}
                        }
                    }
    '''
        
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

        
        
        #Dummy check to see if there is connection to Messana system)


        print('Setting up ISY profile structure')
        self.addSystemDefStruct(self.systemID)
        print(self.systemID + ' added')
        print ('Creating Setup file')
        self.createSetupFiles('./profile/nodedef/nodedefs.xml','./profile/editor/editors.xml', './profile/nls/en_us.txt')
        self.ISYmap = self.createISYmapping()

    def ISYunit(self, name):
        if name.lower() in ISYunit:
            return(self. ISYunit[name.lower()])
        else:
            print('unknown unit : '+str(name))
            return(None)



    def createISYmapping(self):
        temp = {}
        for nodes in self.setupFile['nodeDef']:
            temp[nodes]= {}
            for mKeys in self.setupFile['nodeDef'][nodes]['sts']:
                for ISYkey in self.setupFile['nodeDef'][nodes]['sts'][mKeys]:
                    if ISYkey != 'ISYInfo':
                        temp[nodes][ISYkey] = {}
                        temp[nodes][ISYkey].update({'system': mKeys})
                        temp[nodes][ISYkey].update({'editor': self.setupFile['nodeDef'][nodes]['sts'][mKeys][ISYkey]})
        #print(temp) 
        return (temp)



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

   
                                                    

    def addIsyVaraiable (name, node,  ISYuom, ISYmin, ISYmax, ISYsubset,ISYstep,ISYprecision, nlsText, nlsValues):
        tempDict = {name:{ 'ISYeditor':
                            {'ISYuom':ISYuom, 'ISYmin':ISYmin, 'ISYmax':ISYmax, 'ISYsubset':ISYsubset, 'ISYstep':ISYstep, 'ISYprec':ISYprecision}
                            ,'ISYnls' : {'nlsTEXT' : nlsText, 'nlsValues' : nlsValues} }   
        }
        if self.sData[node] in None:
            self.sData[node] =   {  'ISYnode' : {}
                                    ,'KeyInfo' :{}
                                    ,'data' : {}
                                  }
        elif self.sData[node]['KeyInfo'][name] in None:
            self.sData[node]['KeyInfo'] = tempDict
        else:
            print('Error: valiable '+ str(name) + ' already exists: )

        

    def addNodeDefStruct(self, nodeNbr, nodeName, nodeId):
        self.keyCount = 0
        nodeId.lower()
        print('addNodeDefStruct: ' + nodeName+ ' ' + str(nodeNbr) + ' '+nodeId)
        self.name = nodeName+str(nodeNbr)
        self.nlsKey = 'nls' + self.name
        self.nlsKey.lower()
        #editorName = nodeName+'_'+str(keyCount)
        self.setupFile['nodeDef'][self.name]={}
        self.setupFile['nodeDef'][self.name]['CodeId'] = nodeId
        self.setupFile['nodeDef'][self.name]['nlsId'] = self.nlsKey
        self.setupFile['nodeDef'][self.name]['nlsNAME']=self.sData[nodeName]['data'][nodeNbr]['name']
        self.setupFile['nodeDef'][self.name]['nlsICON']=self.sData[nodeName]['ISYnode']['nlsICON']
        self.setupFile['nodeDef'][self.name]['sts']={}

        #for mKey in self.sData[nodeName]['data'][nodeNbr]: 
        for mKey in self.sData[nodeName]['KeyInfo'][nodeNbr]:             
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
                    #print( mKey + ' ' + ISYnls)
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
                    print('Removed "accepts" for : ' + key + ' not supported')
                    
        if 'sends' in self.sData[nodeName]['ISYnode']:         
            self.setupFile['nodeDef'][self.name]['cmds']['sends'] = self.sData[nodeName]['ISYnode']['sends']                                 
        return()

    def addSystemDefStruct(self, nodeId):
        self.keyCount = 0
        nodeId.lower()
        self.nlsKey= 'nls' + nodeId
        self.nlsKey.lower()
        #print('addSystemDefStruct: ' + nodeId)
        self.setupFile['nodeDef'][ self.systemID]={}
        self.setupFile['nodeDef'][ self.systemID]['CodeId'] = nodeId
        self.setupFile['nodeDef'][ self.systemID]['nlsId'] = self.nlsKey
        self.setupFile['nodeDef'][ self.systemID]['nlsNAME']=self.sData[ self.systemID]['data']['name']
        self.setupFile['nodeDef'][ self.systemID]['nlsICON']=self.sData[ self.systemID]['ISYnode']['nlsICON']
        self.setupFile['nodeDef'][ self.systemID]['sts']={}

        #for mKey in self.sData[ self.systemID]['data']: 
        for mKey in self.sData[ self.systemID]['KeyInfo']:    
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
                        #print( mKey + ' ' + ISYnls)
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



   
    
  
    #Setup file generation 
    def createSetupFiles(self, nodeDefFileName, editorFileName, nlsFileName):
        #print ('Create Setup Files')
        status = True
        try:
            print('opening files')
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
            #print('Opening Files OK')

            editorFile.write('<editors> \n')
            nodeFile.write('<nodeDefs> \n')
            for node in self.setupFile['nodeDef']:
                nodeDefStr ='   <nodeDef id="' + self.setupFile['nodeDef'][node]['CodeId']+'" '+ 'nls="'+self.setupFile['nodeDef'][node]['nlsId']+'">\n'
                #print(nodeDefStr)
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
                    #print(nlsStr)

                for status in self.setupFile['nodeDef'][node]['sts']:
                    for statusId in self.setupFile['nodeDef'][node]['sts'][status]:
                        if statusId != 'ISYInfo':
                            nodeName = self.setupFile['nodeDef'][node]['sts'][status][statusId]
                            nodeDefStr =  '         <st id="' + statusId+'" editor="'+nodeName+'" />\n'
                            #print(nodeDefStr)
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
                                    print('unknown editor keyword: ' + str(key))
                            editorStr = editorStr + ' />\n'
                            #print(editorStr)
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
                                #print(nlsStr)

                nodeFile.write('      </sts>\n')
                nodeFile.write('      <cmds>\n')                
                nodeFile.write('         <sends>\n')            
                if self.setupFile['nodeDef'][node]['cmds']:
                    if len(self.setupFile['nodeDef'][node]['cmds']['sends']) != 0:
                        for sendCmd in self.setupFile['nodeDef'][node]['cmds']['sends']:
                            cmdStr = '            <cmd id="' +sendCmd +'" /> \n'
                            #print(cmdStr)
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
                                        #print(cmdStr)                              
                                        nodeFile.write(cmdStr)
                                        nodeFile.write('            </cmd> \n')
                            else:
                                cmdStr = '            <cmd id="' +acceptCmd+'" /> \n' 
                                #print(cmdStr)
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
            print('something went wrong in creating setup files')
            status = False
            nodeFile.close()
            editorFile.close()
            nlsFile.close()
        return(status)

    def getMessanaSystemKey(self, ISYkey):
        return(self.ISYmap[ self.systemID][ISYkey]['system'])

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

 