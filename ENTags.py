#!/usr/bin/env python
# Scott Hendrickson

import sys
import random
import re
from SpellChecker import aspell

import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors

class TagWrapper(object):
    """
    Class wraps tags object and to control representation and syncronization.
    """
    def __init__(self, _tag):
        # create with EN tag object
        self.tag = _tag
        self.clean = True
 
    def getName(self):
        return self.tag.name
        
    def setName(self, _name):
        self.tag.name = _name
        self.clean = False
    
    def getGuid(self):
        return self.tag.guid
    
    def setParentGuid(self, _parentGuid):
        self.tag.parentGuid = _parentGuid
        self.clean = False

    def getParentGuid(self):
        return self.tag.parentGuid

    def __repr__(self):
        tmp =  '**********\n'
        tmp += '       Id: %s\n'%self.tag.guid
        tmp += '     Name: %s\n'%self.tag.name
        tmp += 'Parent Id: %s\n'%self.tag.parentGuid
        tmp += '    Clean: %s\n'%self.clean
        return tmp
        
    def isDirty(self):
        return not self.clean
    
    def isClean(self):
        return self.clean
        
class TagList(object):
    """
    Local model of a list of tags on EN
    """
    def __init__(self, _ns, _auth):
        # notestore
        self.ns = _ns
        self.authToken = _auth
        # start with sychronized tag list
        self.getServerTagList()
        
    def getServerTagList(self):
        # create local list from server
        try:
            tags = self.ns.listTags(self.authToken)
        except Errors.EDAMSystemException, e:
            print "System error: exiting. (%s)"%e.message
            sys.exit(1)
        except Errors.EDAMUserException, e:
            print "User error: exiting. (%s)"%e.message
            sys.exit(1)
        # Object tags attribute is a list of TagWrappers
        self.tags = {}
        for t in tags:
            self.tags[t.guid] = TagWrapper(t)
        self.idToNameDict = {}
        self.nameToIdDict = {}
        for tid in self.tags:
            self.idToNameDict[tid] = self.tags[tid].getName()
            self.nameToIdDict[self.tags[tid].getName()] = tid
    
    def tagExists(self, _name=None, _guid=None):
        # check local taglist for tag existence by either name or guid
        if _name is not None:
            return _name in self.nameToIdDict
        elif _guid is not None:
            return _guid in self.idToNameDict
        else:
            return False
            
    def getNameByGuid(self, _guid):
        # access to id-name mapping, return None if missing
        if _guid in self.idToNameDict:
            return self.idToNameDict[_guid]
        else:
            return None
            
    def getGuidByName(self, _name):
        # access to name-id mapping, return None if missing
        if _name in self.nameToIdDict:
            return self.nameToIdDict[_name]
        else:
            return None

    def safeGetTagGuid(self, guid = None, name = None):
        # get tag by either id or name, return None if missing
        if guid is not None and self.tagExists(_guid = guid):
            return guid
        elif name is not None and self.tagExists(_name = name):
            return self.getGuidByName(name)
        else:
            return None

    def safeGetParentName(self, guid = None, name = None):
        # get tag parent by either id or name, return None if tag or parent missing
        guid = self.safeGetTagGuid(guid, name)
        if guid is None:
            return None
        parentGuid = self.safeGetTagGuid(self.tags[guid])
        if parentGuid is None:
            return None
        return self.tags[parentGuid].getName()
        
    def updateTagsOnServer(self, _msg = ''):
        msg = _msg
        for t in self.tags:
            if self.tags[t].isDirty():  
                try:
                    self.ns.updateTag(self.authToken, self.tags[t].tag)
                except Errors.EDAMUserException, e:
                    print "User error: exiting (%s)\n"%e.message
                    sys.exit(1)
                except Errors.EDAMSystemException, e:
                    print "System error: exiting (%s)\n"%e.message
                    sys.exit(1)
                except Errors.EDAMNotFoundException, e: 
                    msg += "Tag not found error (%s)\n"%e.message
                    return msg
        # refresh local taglist
        self.getServerTagList()
        return msg
    
    def addTag(self, _name, _parentGuid = None, _parentName = None):
        # create a new tag on server and refresh taglist
        msg = None
        # create a new tag type object
        newTag = Types.Tag();
        newTag.name = _name
        newTag.parentGuid = None
        parentGuid = self.safeGetTagGuid(_parentGuid, _parentName)
        if _parentName is not None and parentGuid is None:
            return "Parent tag does not exist."
        newTag.parentGuid = parentGuid
        try:
            self.ns.createTag(self.authToken, newTag)
        except Errors.EDAMUserException, e:
            print "User error: exiting (%s)\n"%e.message
            sys.exit(1)
        except Errors.EDAMSystemException, e:
            print "System error: exiting (%s)\n"%e.message
            sys.exit(1)
        except Errors.EDAMNotFoundException, e: 
            return "Item not found error (%s)\n"%e.message
        return self.updateTagsOnServer(msg)
        
    def updateParent(self, _name=None, _guid=None, _parentName=None, _parentGuid=None):
        # change a tag's parent on server
        msg = None
        guid = self.safeGetTagGuid(_guid, _name)
        if guid is None:
            return  "Tag name does not exist.\n"
        if _parentName is not None:
            if _parentName == "[[root]]":
                parentGuid = None
            else:   
                parentGuid = self.safeGetTagGuid(_parentGuid, _parentName)
                if parentGuid is None:
                    return "Parent tag does not exist.\n"
        else:
            parentGuid = self.safeGetTagGuid(_parentGuid, _parentName)
            if parentGuid is None:
                return "Parent tag does not exist.\n"
        if parentGuid == self.safeGetParentName(guid):
            return "Tag %s already is the parent.\n"%self.safeGetParentName(guid)
        if guid == parentGuid:
            return "Like people, tags cannot be their own parents.\n"
        self.tags[guid].setParentGuid(parentGuid)
        return self.updateTagsOnServer(msg) 
        
    def renameTag(self, _name=None, _guid=None, _newName=None):
        # update tag's name on server
        msg = None
        guid = self.safeGetTagGuid(_guid, _name)
        if guid is None:
            return "Tag name does not exist.\n"
        if _newName is not None:
            self.tags[guid].setName(_newName)
        else:
            return "No new name provided.\n"
        return self.updateTagsOnServer(msg) 
        
    def getLineage(self, _name=None, _guid=None, res=[]):
        # recursing traversal of ancestry
        if _name is not None:
            guid = self.nameToIdDict[_name]
            name = _name
        elif _guid is not None:
            guid = _guid
            name = self.idToNameDict[_guid]
        else:
            # this tag isn't in the list?
            print "Tag not in list. Exiting"
            sys.exit(1)
        #
        if self.tags[guid].getParentGuid() is not None:
            return [name] + self.getLineage( _guid=self.tags[guid].getParentGuid(), res=res)
        else:
            return [name]
    
    def __repr__(self):
        res = ''
        for t in self.tags:
            res += str(self.tags[t])
        return res
                        
##################
import ConfigParser

class ENManager(object):
    
    DEFAULT_FILE_NAME = "ENTags.cfg"
    
    def __init__(self):
        config = ConfigParser.ConfigParser()
        config.read(self.DEFAULT_FILE_NAME)
        self.consumerKey = config.get("appcreds", "consumerKey")
        self.consumerSecret = config.get("appcreds", "consumerSecret")
        devToken = config.get("appcreds", "devToken")
        evernoteHost = config.get("server","evernoteHost")
        un = config.get('creds', 'un')
        pwd = config.get('creds', 'pwd')

        # Indicates when the latest list of tags needs to be pulled down
        # from the Evernote server.
        self.notebooksClean = False
        
        self.startUpMessage = []
        self.startUpMessage.append('*'*80 + '\n')
        
        self.startUpMessage.append('evernote host: %s\n'%evernoteHost)
        
        userStoreUri = "https://" + evernoteHost + "/edam/user"
        noteStoreUriBase = "http://" + evernoteHost + "/edam/note/"

        userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
        userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
        userStore = UserStore.Client(userStoreProtocol)

        versionOK = userStore.checkVersion("Python EDAMTest",
            UserStoreConstants.EDAM_VERSION_MAJOR,
            UserStoreConstants.EDAM_VERSION_MINOR)
        
        self.startUpMessage.append('EDAM protocol version up to date: %s\n'%str(versionOK))
        
        if not versionOK:
            print 'Protocol is not up to date. Exiting.'
            exit(1)

        if devToken is None:
            # Authenticate the user
            try :
                authResult = userStore.authenticate(un, pwd,
                                 self.consumerKey, self.consumerSecret)
            except Errors.EDAMUserException as e:
                # See http://www.evernote.com/about/developer/api/ref/UserStore.html#Fn_UserStore_authenticate
                parameter = e.parameter
                errorCode = e.errorCode
                errorText = Errors.EDAMErrorCode._VALUES_TO_NAMES[errorCode]
                #
                self.startUpMessage.append( "Authentication failed (parameter: " + 
                    parameter + " errorCode: " + errorText + ")\n")
        
                if errorCode == Errors.EDAMErrorCode.INVALID_AUTH:
                    if parameter == "consumerKey":
                        if self.consumerKey == "en-edamtest":
                            self.startUpMessage.append("Check consumerKey")
                        else:
                            self.startUpMessage.append("Consumer key was not accepted by %s\n"%evernoteHost)
                    elif parameter == "username":
                        self.startUpMessage.append("Authenticate with username/password from %s\n"%evernoteHost)
                        if evernoteHost != "www.evernote.com":
                            self.startUpMessage.append("Sandbox account! Correct username/password?")
                    elif parameter == "password":
                        self.startUpMessage.append( "Incorrect password. Exiting.\n")
                print "".join(self.startUpMessage)
                exit(1)
            self.authToken = authResult.authenticationToken
            user = authResult.user
            self.startUpMessage.append( "Authentication was successful for user: %s\n"%user.username)
            self.startUpMessage.append( "Authentication token:\n  %s\n"%self.authToken)
            noteStoreUri =  noteStoreUriBase + user.shardId
        else:
            noteStoreUri = userStore.getNoteStoreUrl(devToken)
            self.authToken = devToken
        noteStoreHttpClient = THttpClient.THttpClient(noteStoreUri)
        noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
        self.noteStore = NoteStore.Client(noteStoreProtocol)
        #
        self.startUpMessage.append('*'*80 + '\n')
        self.tl = TagList(self.noteStore, self.authToken)
    
    def getStartUpMessage(self):
        return ''.join( self.startUpMessage )
    
    def getNotebooks(self):
        # get a the of notebooks from server
        if not self.notebooksClean:
            self.notebooks = self.noteStore.listNotebooks(self.authToken)
            self.notebooksClean = True
        return self.notebooks
        
    def getNotesWithTags(self, _guidList):
        filtr = NoteStore.NoteFilter()
        filtr.tagGuids=_guidList
        noteList = self.noteStore.findNotes(self.authToken, filtr, 0, 100)
        for n in noteList.notes:
            print n.title, str(n.tagGuids)

    def listNotebookNames(self):
        # return a list of notebook names
        return [notebook.name for notebook in self.getNotebooks()]
            
    def getTagNamesList(self):
        return self.tl.nameToIdDict.keys()
        
    def renameTag(self, name, newName):
        return self.tl.renameTag(_name=name, _newName=newName)

    def updateParent(self, name, newParentName):
        return self.tl.updateParent(_name=name, _parentName=newParentName)
            
    def listTagLineages(self, pattern=None):
        # Return a list of tag lineages as lists
        res = []
        if pattern is not None:
            patternRE = re.compile(pattern, re.IGNORECASE)      
        for name in self.getTagNamesList():
            if pattern is not None:
                if patternRE.search(name) is None:
                    continue
            tmp = self.tl.getLineage(name)
            tmp.reverse()
            res.append(tmp)
        return res

    def createTag(self, tagName, parentName=None, parentGuid=None):
        if not self.tl.tagExists(tagName):
            return self.tl.addTag(tagName, _parentName=parentName, _parentGuid=parentGuid)
        else:
            return "Tag already esists"

    def deleteTag(self, tagname):
        if self.tl.tagExists(tagname):
            trashName = "_trash_cnote_"
            if not self.tl.tagExists(trashName):
                self.createTag(trashName)
            res = self.updateParent(tagname, trashName)
        else:
            res = "Tag not found"
        return res

    def getNoteCountbyTag(self, name = None, nameList = None):
        res = {}
        if name is not None:
            guidList = [self.tl.getGuidByName(name)]
        elif nameList is not None:
            if nameList == []:
                guidList = self.tl.idToNameDict.keys()
            else:
                guidList = []
                for x in nameList:
                    tmp = self.tl.getGuidByName(x)
                    if tmp is not None:
                        guidList.append(tmp)
        for guid in guidList:
            filter = NoteStore.NoteFilter(None, True, None, None, 
                    [guid], None, False)
            noteCounts = self.noteStore.findNoteCounts(self.authToken, filter, False)
            if noteCounts.tagCounts is not None:
                if guid in noteCounts.tagCounts:
                    res[guid] = noteCounts.tagCounts[guid]
                else:
                    res[guid] = -1
            else:
                res[guid] = -1
        return res
    
    def checkTagSpelling(self, wordList = []):
        sc = aspell()
        res = []
        if wordList == []:
            wordList = self.tl.nameToIdDict.keys()
        for term in wordList:
            sugWordDict = sc(term)
            sugList = []
            for w in sugWordDict:
                if sugWordDict[w] is not None:
                    sugList += sugWordDict[w].values()
            if len(sugList) > 0:
                res.append([term] +  sugList)
        return res

###################
if __name__ == "__main__":
    import random
    from pprint import pprint

    print "Creating tag manager object..."
    en = ENManager()
    print en.getStartUpMessage()
    pprint(en.getNotebooks())
    pprint(en.listNotebookNames())
    pprint(en.getTagNamesList())
    print
    print en.getNotesWithTags(["e47f3ecb-e198-43a2-8556-f3d63c0e5ae0"])
    print
    newName  = "temp_%d"%random.randint(1324134,99999999)
    newName1 = "temp_%d"%random.randint(1324134,99999999)
    newName2 = "temp_%d"%random.randint(1324134,99999999)
    newName3 = "temp_%d"%random.randint(1324134,99999999)
    print newName, newName1, newName2, newName3
    en.createTag(newName)
    en.createTag(newName1, newName)
    en.createTag(newName3)
    #
    en.renameTag(newName1, newName2)
    en.updateParent(newName2, newName3)
    print
    pprint(en.getTagNamesList())
    print
    for id in en.tl.tags:
        print en.tl.tags[id].getName(),"\t",  en.getNoteCountbyTag(en.tl.tags[id].getName())
    print
    pprint(en.listTagLineages())
    print
    pprint(en.listTagLineages("temp_.*"))
    print 
    print str(en.tl)
    print 
