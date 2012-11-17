#!/usr/bin/env python

import popen2
import re

numPuncRE = re.compile("[0-9]+")
 
class aspell:
    def __init__(self):
        self._f = popen2.Popen3("aspell -a")
        self._f.fromchild.readline() #skip the credit line
    
    def __call__(self, words):
        words = re.split('\W+',words)
	output = {}
        for word in words:
	    word = word.strip()
	    if numPuncRE.search(word) is not None or word == '':
		continue
            self._f.tochild.write(word+'\n')
            self._f.tochild.flush()
            s = self._f.fromchild.readline().strip()
	    while s.strip() <> '':
		if s.startswith("*"):
		    # seems correct
                    output[word] = None
            	elif s.startswith('#'):
		    # unknown, but no suggestions
                    output[word] = None
	    	elif s.startswith("&"):
                    tmp = s.split(':')[1].strip().split(', ')
		    tmpMap = {}
		    cnt = 0
		    for suggestion in tmp:
			tmpMap[cnt] = suggestion
			cnt += 1
		    output[word] = tmpMap
		else:
		    output[word] = "Error, something went wrong!"
                s = self._f.fromchild.readline() #skip the blank line
        return output

if __name__ == "__main__":
	chkr = aspell()
	print "helo", chkr("helo")
	print "hello", chkr("hello")
	print "academec", chkr("academec")
	print "academic", chkr("academic")
	print "academic helo hendrickson", chkr("academic helo hendrickson")
	print "academec helo", chkr("academec helo")
	print "academec (123)", chkr("academec (123)")
	print "academec-doggie", chkr("academec-doggie")
