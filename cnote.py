#!/usr/bin/env python
#  Command line tag manager
#  Scott Hendrickson
import datetime
from cmd import Cmd
import optparse
import sys
from operator import itemgetter, attrgetter

import ENTags

INTRO="""Evernote Command Line structure manager. Version 0.01b"""

class cnote(Cmd):
    
    prompt = 'en> '
    intro = INTRO
    outHead = "\n"
    outTail = outHead
    
    def __init__(self):
        self.en = ENTags.ENManager()
        self.outfile = None
        Cmd.__init__(self)
    
    def getStartUpMessage(self):
        return self.en.getStartUpMessage()
    
    def precmd(self, line):
        if '>' in line:
            a,b = line.split('>')
            self.outfile = file(b.strip(),'w')
            line = a
        else:
            self.outfile = None
        return line

    def emptyline(self):
        print "Current time: <%s>\n"%str(datetime.datetime.now()).split(".")[0]
        return

    def help_file(self):
        print "Append '> filename' to any command to redirect output from that"
        print "command to file in working directory."

    def response(self,res):
        print res
        if self.outfile is not None:
            self.outfile.write(res)
            self.outfile.close()
            print '(Wrote output to file.)'
            
    def getArgList(self, argStr):
        # Item may be quoted
        res = []
        started = False
        for it in argStr.split(" "):
            item = it.strip()
            if item == '':
                break
            elif item[0] == '"':
                if item[-1] == '"' and len(item) > 1:
                    res.append(item.strip('"'))
                else:
                    started = True
                    tmpStr = item[1:]
            elif item[-1] == '"':
                if started:
                    started = False
                    res.append(tmpStr + ' ' + item[:-1])
                else:
                    print "Error, unmatched quotes in input"
            elif started:
                tmpStr += ' ' + item
            else:
                res.append(item)
        if started:
            print "Error, unmatched quotes in input"    
        #print res
        return res
    
    def help_quotes(self):
        print 'For tag names containing spaces, surround with double quotes, i.e.,  "tag name".'

###########################             
#  commands

    def do_ln(self, args):
        self.do_listNotebooks(args)
    
    def help_ln(self):
        self.help_listNotebooks()

    def do_listNotebooks(self, args):
        res = self.en.listNotebookNames()
        n = len(res)
        outString = self.outHead
        outString += "(results: %d)\n"%n
        for name in res:
            outString += "  %s\n"%name
        self.response(outString)
        
    def help_listNotebooks(self):
        print 'listNotebooks (ln) - List all the Notebooks associated with this Evernote account.'
    
    ## 
    def do_lt(self, args):
        self.do_listTags(args)

    def help_lt(self):
        self.help_listTags()

    def do_listTags(self, args):
        argl = self.getArgList(args)
        if len(argl) == 1:
            pattern = argl[0]
        else:
            pattern = None
        res = sorted(self.en.listTagLineages(pattern), key=itemgetter(0))
        n = len(res)
        outString = self.outHead
        outString += "(results: %d)\n"%n
        for x in res:
            outString += ' : '.join(x)
            outString += '\n'
        self.response(outString)
    
    def help_listTags(self):
        print 'listTags (lt) - List all tags from this Evernote account.  Optional argument is a Python regular expression.'

    ##
    def do_ct(self, args):
        self.do_createTag(args)

    def help_ct(self):
        self.help_createTag()

    def do_createTag(self, args):
        res = self.outHead
        alist = self.getArgList(args)
        if len(alist) > 0:
            tagName = alist[0].strip()
            res += 'Creating tag: %s '%tagName
            parentTagName = None
            if len(alist) > 1:
                parentTagName = alist[1].strip()
                res += 'with parent tag: %s '%parentTagName
            self.en.createTag(tagName, parentTagName)
        else:
            res += 'Wrong number arguments to create a tag (name required).'
        res += '\n'
        self.response(res)
    
    def help_createTag(self):
        print 'createTag (ct) - Create a new tag. First argument is tag name, second argument is tag parent name (optional).'
    
    ##
    def do_mt(self, args):
        self.do_mergeTags(args)

    def help_mt(self):
        self.help_mergeTags()

    def do_mergeTags(self, args):
        res = self.outHead
        alist = self.getArgList(args)
        if len(alist) == 2:
            oldTagName = alist[0].strip()
            newTagName = alist[1].strip()
            doList = self.en.mergeTags(oldTagName, newTagName)
            res += '\n'.join([x for x in doList if x is not None])
        else:
            res += 'Wrong number of arguments, two tag names required.'
        res +='\n'
        self.response(res)

    def help_mergeTags(self):
        print 'mergeTags (mt) - Arguments OldTagName NewTagName. Updates all notes with oldTagName --> newTagName and deletes OldTagName.'
    ##
    def do_rt(self, args):
        self.do_renameTag(args)

    def help_rt(self):
        self.help_renameTag()

    def do_renameTag(self, args):
        res = self.outHead
        alist = self.getArgList(args)
        if len(alist) == 2:
            tagName = alist[0].strip()
            newTagName = alist[1].strip()
            if self.en.renameTag( tagName, newTagName) is None:
                res += 'Tag: %s successfully renamed to: %s'%(tagName, newTagName)
            else:
                res += 'Rename failed'
        else:
            res += 'Wrong number of arguments to rename a tag (2 required)'
        res += '\n'
        self.response(res)
    
    def help_renameTag(self):
        print 'renameTag (rt) - Rename tag name1 to name2'

    ##
    def do_up(self, args):
        self.do_updateParent(args)

    def help_up(self):
        self.help_updateParent()

    def do_updateParent(self, args):
        res = self.outHead
        alist = self.getArgList(args)
        if len(alist) == 2:
            tagName = alist[0].strip()
            newTagName = alist[1].strip()
            if self.en.updateParent( tagName, newTagName) is None:
                res += 'Tag: %s successfully updated with parent: %s'%(tagName, newTagName)
            else:
                res += 'Update failed'
        else:
            res += 'Wrong number of arguments to rename a tag (2 required)'
        res += '\n'
        self.response(res)
    
    def help_updateParent(self):
        print 'updateParent (up) - Change parent of tag name1 to name2. Use [[root]] for no parent.'
      
    ##                  
    def do_sync(self, args):
        self.en.tl.getServerTagList()
        
    def help_sync(self):
        print 'sync - Resync with Evernote servers.'
    
    ##
    def do_nc(self, args):
        self.do_noteCounts(args)
    
    def help_nc(self):
        self.help_noteCounts()

    def do_noteCounts(self, args):
        res = self.outHead
        alist = self.getArgList(args)
        if alist is None:
            alist = []
        tmp = self.en.getNoteCountbyTag(nameList = alist)
        for guid in tmp:
            tn = self.en.tl.getNameByGuid(guid)
            ltn = len(tn)
            res += '%s %s %4d\n'% (tn,'.'*(30-ltn), tmp[guid])
        self.response(res)
        
    def help_noteCounts(self):
        print 'noteCounts (nc) - Get the note count for tag with tagName.'
    
    ##
    def do_dtc(self, args):
        self.do_deleteTagsByCount(args)

    def help_dtc(self):
        self.help_deleteTagsByCount()

    def do_deleteTagsByCount(self, args):
        res = self.outHead
        alist = self.getArgList(args)
        try:
            nlimit = int(alist.pop(0))
            res += "Deleting tags with fewer than %d notes (this may take time)...\n"%nlimit
        except ValueError:
            res += "Please enter a number in the first position. No tags deleted.\n"
            self.response(res)
            return
        except IndexError:
            res += "Please enter a number. No tags deleted.\n"
            self.response(res)
            return
        tmp = self.en.getNoteCountbyTag(nameList = alist)
        for guid in tmp:
            tn = self.en.tl.getNameByGuid(guid)
            try:
                nnotes = int(tmp[guid])
                hc = self.en.tl.hasChild(guid)
                # don't delete tags with children, even if notecount is low
                if nnotes < nlimit and not hc:
                    tmpres = self.en.deleteTag(tn)
                    if tmpres is not None:
                        res += tmpres
                    res += '%s deleted (%d notes)\n'% (tn, nnotes)
                else:
                    if hc:
                        res += '%s not deleted (%d notes, has at least 1 child)\n'% (tn, nnotes)
                    else:
                        res += '%s not deleted (%d notes)\n'% (tn, nnotes)
            except ValueError:
                pass
        self.response(res)

    def help_deleteTagsByCount(self):
        print "deleteTagsCount (dtc) - deletes tags with note count less than the argument"
    
    ##
    def do_dt(self, args):
        self.do_deleteTag(args)

    def help_dt(self):
        self.help_deleteTag()

    def do_deleteTag(self, args):
        res = self.outHead
        alist = self.getArgList(args)
        for a in alist:
            resp = self.en.deleteTag(a)
            if resp is None:
                res += 'Deleted: %s'%a
            else:
                res += '%s: %s'%(a,resp)
            res += '\n'
        self.response(res)
        
    def help_deleteTag(self):
        print 'deleteTag (dt) - deletes tag by name.'
   
    ##
    def do_sc(self, args):
        self.do_spellCheck(args)

    def help_sc(self):
        self.help_spellCheck()

    def do_spellCheck(self, args):
        argl = self.getArgList(args)
        splist = self.en.checkTagSpelling(argl)
        n = len(splist)
        res = self.outHead
        res += "(results: %d)\n"%n
        for x in splist:
            tagName = x[0]
            sugList = x[1:]
            res += '%s %s Suggestions: %s\n'%(tagName,'.'*(30-len(tagName)), ', '.join(sugList))
        self.response(res)

    def help_spellCheck(self):
        print "spellCheck (sc) Check spelling of Tag Names."
 
    ##    
    def do_quit(self, args):
        self.do_exit(args)
        
    def help_quit(self):
        print "quit - Exit cnote."
    
    def do_exit(self, args):
        sys.exit(1)
        
    def help_exit(self):
        print "exit - Exit cnote."
  
###########################             

if __name__ == "__main__":
    p = optparse.OptionParser()
    p.add_option('-v','--verbose',dest='verbose',action='store_true', default=False, help='Run in verbose mode.')
    options, args = p.parse_args()
    cn = cnote()
    if options.verbose:
        print cn.getStartUpMessage()
    cn.cmdloop()
