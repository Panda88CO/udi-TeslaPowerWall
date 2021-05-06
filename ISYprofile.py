#!/usr/bin/env python3
import requests
import json
import os 
from tesla_powerwall import GridStatus, OperationMode
import polyinterface
LOGGER = polyinterface.LOGGER


class isyHandling:
    def __init__ (self):
        # Note all xxIDs must be lower case without special characters (ISY requirement)
        #self.systemID = ISYcontrollerName
        #self.systemName = systemName
        LOGGER.info('isyProfile - init')
        self.sData  = {}
        self.ISYunit = {'boolean':2, 'list':25, 'kw':30, 'percent':51}  #need to increase to cover more cases  
        self.nodeCount = 0
        self.setupFile = { 'nodeDef':{}
                            ,'editors':{}
                            ,'nls':{}}

        

    def getISYunit(self, name):
        if name.lower() in self.ISYunit:
            return(self.ISYunit[name.lower()])
        else:
            LOGGER.error('unknown unit : '+str(name))
            return(None)



    def createISYmapping(self):
        temp = {}
        for nodes in self.setupFile['nodeDef']:
            temp[nodes]= {}
            for mKeys in self.setupFile['nodeDef'][nodes]['sts']:
                for ISYkey in self.setupFile['nodeDef'][nodes]['sts'][mKeys]:
                    if ISYkey != 'ISYInfo':
                        temp[nodes][ISYkey] = {}
                        temp[nodes][ISYkey].update({'systemVar': mKeys})
                        editorName = self.setupFile['nodeDef'][nodes]['sts'][mKeys][ISYkey]
                        temp[nodes][ISYkey].update({'editor': editorName})
                        temp[nodes][ISYkey].update({'uom': self.setupFile['editors'][editorName]['ISYuom']})
        #LOGGER.debug(temp) 
        return (temp)



    def addISYnode(self,  nodeId, name, icon ):
        tempDict = {'nlsICON':icon, 'nlsName': name }
        if not(nodeId in self.sData):
            self.sData[nodeId]={}
            self.sData[nodeId]['ISYnode'] = {'sends':[], 'accepts':{}}
            self.sData[nodeId]['ISYnode'].update(tempDict)
        else:
            LOGGER.error('node '+ str(nodeId) + ' already exists')
            
    def addISYcommandSend(self, nodeId,  sendCmd):
        if nodeId in self.sData:
            self.sData[nodeId]['ISYnode']['sends'].append(sendCmd)
        else:
            LOGGER.error('must create node first')
            

    def getISYSendCommands(self, nodeId):
        return(self.sData[nodeId]['ISYnode']['sends'])



    def addISYcommandReceive(self, nodeId, cmdName, cmdText, cmdVariable):
        if nodeId in self.sData:
            tempDict = {'ISYtext':cmdText, 'ISYeditor':cmdVariable}
            self.sData[nodeId]['ISYnode']['accepts'][cmdName] = tempDict
        else:
            LOGGER.error('must create node first')
            

    def getISYReceiveCommands(self, nodeId): 
        tempList = []
        for key in self.sData[nodeId]['ISYnode']['accepts']:
            tempList.append({key:self.sData[nodeId]['ISYnode']['accepts'][key]['ISYeditor']} )
        return(tempList)

    def addIsyVaraiable (self, name, nodeId,  ISYuom, ISYmin, ISYmax, ISYsubset,ISYstep,ISYprecision, nlsText, nlsValues):
        
        uom = self.getISYunit(ISYuom)
        tempDict = { 'ISYeditor':
                            {'ISYuom':uom, 'ISYmin':ISYmin, 'ISYmax':ISYmax, 'ISYsubset':ISYsubset, 'ISYstep':ISYstep, 'ISYprec':ISYprecision}
                            ,'ISYnls' : {'nlsTEXT' : nlsText, 'nlsValues' : nlsValues} 
        }
        if not(nodeId in self.sData):
            LOGGER.error('Must create node '+str(nodeId)+' first.' )
            
        elif not('KeyInfo' in self.sData[nodeId]):
            self.sData[nodeId]['KeyInfo'] = {}
            self.sData[nodeId]['KeyInfo'][name] = tempDict
        elif not(name in self.sData[nodeId]['KeyInfo']):
            self.sData[nodeId]['KeyInfo'][name] = tempDict
        else:
            LOGGER.error('Error: valiable '+ str(name) + ' already exists:' )
            
    def removeISYvariable(self, nodeId, cmdName):
        if cmdName in self.sData[nodeId]['KeyInfo']:
             self.sData[nodeId]['KeyInfo'].pop(cmdName)

    def addNodeDefStruct(self, nodeNbr, nodeName, nodeId):
        self.keyCount = 0
        nodeId.lower()
        LOGGER.debug('addNodeDefStruct: ' + nodeName+ ' ' + str(nodeNbr) + ' '+nodeId)
        self.name = nodeId+str(nodeNbr)
        self.nlsKey = 'nls' + self.name
        self.nlsKey.lower()

        self.setupFile['nodeDef'][self.name]={}
        self.setupFile['nodeDef'][self.name]['CodeId'] = nodeId
        self.setupFile['nodeDef'][self.name]['nlsId'] = self.nlsKey
        self.setupFile['nodeDef'][self.name]['nlsNAME']=self.sData[nodeName]['ISYnode']['nlsName']
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

    def addControllerDefStruct(self, controllerName, controllerId):
        self.keyCount = 0
        controllerId.lower()
        self.nlsKey= 'nls' + controllerId
        self.nlsKey.lower()
        self.setupFile['nodeDef'][ controllerId]={}
        self.setupFile['nodeDef'][ controllerId]['CodeId'] = controllerId
        self.setupFile['nodeDef'][ controllerId]['nlsId'] = self.nlsKey
        self.setupFile['nodeDef'][ controllerId]['nlsNAME']=self.sData[controllerId]['ISYnode']['nlsName']
        self.setupFile['nodeDef'][ controllerId]['nlsICON']=self.sData[controllerId]['ISYnode']['nlsICON']
        self.setupFile['nodeDef'][ controllerId]['sts']={}

        #for mKey in self.sData[ controllerId]['data']: 
        for mKey in self.sData[ controllerId]['KeyInfo']:    
            #make check if controller has unit installed
            if self.sData[ controllerId]['KeyInfo'][mKey]['ISYeditor']['ISYuom']:
                if ((self.sData[ controllerId]['KeyInfo'][mKey]['ISYeditor']['ISYuom'] == 112
                   and self.sData[ controllerId]['data'][mKey] != 0)
                   or self.sData[ controllerId]['KeyInfo'][mKey]['ISYeditor']['ISYuom'] != 112):
                    self.keyCount = self.keyCount + 1
                    editorName = 'CTRL_'+str(self.keyCount)
                    nlsName = editorName
                    ISYvar = 'GV'+str(self.keyCount)
                    self.setupFile['nodeDef'][ controllerId]['sts'][mKey]={ISYvar:editorName}
                    self.setupFile['editors'][editorName]={}
                    #self.setupFile['nls'][editorName][ISYparam]
                    for ISYparam in self.sData[ controllerId]['KeyInfo'][mKey]['ISYeditor']:
                        if self.sData[ controllerId]['KeyInfo'][mKey]['ISYeditor'][ISYparam]!= None:
                            self.setupFile['editors'][editorName][ISYparam]=self.sData[ controllerId]['KeyInfo'][mKey]['ISYeditor'][ISYparam]

                    if self.sData[ controllerId]['KeyInfo'][mKey]['ISYnls']:
                        self.setupFile['nls'][nlsName]={}
                    for ISYnls in self.sData[ controllerId]['KeyInfo'][mKey]['ISYnls']:
                        #LOGGER.debug( mKey + ' ' + ISYnls)
                        if  self.sData[ controllerId]['KeyInfo'][mKey]['ISYnls'][ISYnls]:      
                            self.setupFile['nls'][nlsName][ISYnls] = self.sData[ controllerId]['KeyInfo'][mKey]['ISYnls'][ISYnls]
                            if ISYnls == 'nlsValues':
                                self.setupFile['editors'][editorName]['nlsKey'] = nlsName
        
        self.setupFile['nodeDef'][ controllerId]['cmds']={}
        if 'accepts' in self.sData[ controllerId]['ISYnode']:
            self.setupFile['nodeDef'][ controllerId]['cmds']['accepts'] = {}
            for key in  self.sData[ controllerId]['ISYnode']['accepts']:     
                if self.sData[ controllerId]['ISYnode']['accepts'][key]['ISYeditor'] in self.setupFile['nodeDef'][ controllerId]['sts']:
                    mVal = self.sData[ controllerId]['ISYnode']['accepts'][key]['ISYeditor']
                    self.setupFile['nodeDef'][ controllerId]['cmds']['accepts'][key]= self.setupFile['nodeDef'][ controllerId]['sts'][mVal]
                    self.setupFile['nodeDef'][ controllerId]['cmds']['accepts'][key]['ISYInfo']=self.sData[ controllerId]['ISYnode']['accepts'][key]
                else:
                    self.setupFile['nodeDef'][ controllerId]['cmds']['accepts'][key]= {}
                    self.setupFile['nodeDef'][ controllerId]['cmds']['accepts'][key]['ISYInfo']= self.sData[ controllerId]['ISYnode']['accepts'][key]   
        if 'sends' in self.sData[ controllerId]['ISYnode']:
            self.setupFile['nodeDef'][ controllerId]['cmds']['sends']=self.sData[ controllerId]['ISYnode']['sends']                              
        return()
  
    #Setup file generation 
    def createSetupFiles(self, nodeDefFileName, editorFileName, nlsFileName):
        #LOGGER.debug ('Create Setup Files')
        status = True
        try:
            #LOGGER.debug('opening files')
            if not(os.path.exists('./profile')):
                os.mkdir('./profile')       
            if not(os.path.exists('./profile/editor')):
                os.mkdir('./profile/editor')
            if not(os.path.exists('./profile/nls')):
                os.mkdir('./profile/nls')           
            if not(os.path.exists('./profile/nodedef')):
                os.mkdir('./profile/nodedef')
            nodeFile = open('./profile/nodedef/'+nodeDefFileName, 'w+')
            editorFile = open('./profile/editor/'+editorFileName, 'w+')
            nlsFile = open('./profile/nls/'+nlsFileName, 'w+')
            #LOGGER.debug('Opening Files OK')

            editorFile.write('<editors> \n')
            nodeFile.write('<nodeDefs> \n')
            for node in self.setupFile['nodeDef']:
                nodeDefStr ='   <nodeDef id="' + self.setupFile['nodeDef'][node]['CodeId']+'" '+ 'nls="'+self.setupFile['nodeDef'][node]['nlsId']+'">\n'
                #LOGGER.debug(nodeDefStr)
                nodeFile.write(nodeDefStr)
                nodeFile.write('      <editors />\n')
                nodeFile.write('      <sts>\n')
                nlsStr = 'ND-'+self.setupFile['nodeDef'][node]['CodeId']+'-NAME = '+self.setupFile['nodeDef'][node]['nlsNAME']+ '\n'
                nlsFile.write(nlsStr)
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
    
