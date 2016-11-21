#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import math
import re
from os import path
from scipy import spatial
import numpy as np

sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from pythonlib import semantic as sm
from pythonlib import sysf

inputform = "topic-folder,cl-file,cl-floder,zipf,type[0(tfidf)/1(tfidf2)/2(lsa)/3(lda)],output-floder"

if len(sys.argv) != 7:
    print "input:" + inputform
    sys.exit(1)

outf = sys.argv[6]+'/uqc-'+'-'.join(map(lambda x:x.strip('/').split('/')[-1],sys.argv[2:-1]))
fout = sysf.logger(outf,inputform)

def vecof(lines,a,wtol,kk):
    vec = np.zeros(kk)
    for line in lines:
        line = line.strip('\n')
        vec = vec + a[:,wtol[line]]
    return vec

type = int(sys.argv[5])
zipf = float(sys.argv[4])
wtola = sm.readwl("/home/ec2-user/git/statresult/wordslist_dsw.txt")
if type == 3:
    wtolu = sm.readwl("/home/ec2-user/git/statresult/wordslist_top1000_dsw.txt")
else:
    wtolu = wtola
a = np.load('/home/ec2-user/data/classinfo/vt.npy')#lsa result
b = a
ukk = a.shape[0]
s = None
akk = ukk
if type == 3:
#    b = np.load('/home/ec2-user/git/statresult/lda-30-2000-phi.npy')
#    s = np.load('/home/ec2-user/git/statresult/lda-30-2000-pz.npy')
    b = np.load('/home/ec2-user/git/statresult/lda-32-1000-top1000-phi.npy')
    s = np.load('/home/ec2-user/git/statresult/lda-32-1000-top1000-pz.npy')
    ukk = b.shape[0]
    if zipf < 0:
        fldawl = open('/home/ec2-user/git/statresult/wordslist_top1000_dsw.txt','r')#wordlist for lda
        i = 0
        ltow = {}
        for line in fldawl:
            line = line.strip('\n')
            ltow[i] = line
            i = i + 1
        fldawl.close()
        p = []
        p.append(b[:,0])
        for i in range(1,b.shape[1]):
            p.append(b[:,i]+p[i-1])
        p = np.array(p)
        p = p.transpose()


root = sys.argv[1]

if sys.argv[2] == 'rand':
    cll = {}
    for i in range(0,ukk):
	cll[i] = np.random.randint(ukk,size=3)

else:
    fcl = open(sys.argv[2],'r')
    cll = {}
    for line in fcl:
	line = line.strip(' \n')
	line = line.split(' ')
	for w in line:
	    ww = int(w)
	    cll[ww] = list(line)
	    cll[ww].remove(w)
    fcl.close()

u = {}

for root, dirs, files in os.walk(root):
    for name in files:
        filename = root + '/' + name
        if name.isdigit():
            fin = open(filename,'r')
            temp = fin.read()
            fin.close()
            cl = re.search(r'【出願人】.【識別番号】.*?【氏名又は名称】(.*?)【',temp,re.DOTALL)
            user = cl.group(1)
            if user not in u:
                u[user] = set()
            u[user].add(name)


total = 0
hit = 0
mthit = 0
mtls = 0
usernum = 0
for user in u:
    if len(u[user]) > 5:
        print user
        usernum = usernum + 1
        count = 0
        vec = [np.zeros(akk) for i in range(0,4)]
        vect = [np.zeros(akk) for i in range(0,4)]
        vecu = [np.zeros(ukk) for i in range(0,4)]
        vecut = [np.zeros(ukk) for i in range(0,4)]
        for name in u[user]:
	    print '@'+root+name
            count = count + 1
            fin = open(root+name,'r')
            line = fin.read()
            title = re.search(r'【発明の名称】(.*?)\(',line,re.DOTALL)
            cl = re.search(r'(【国際特許分類第.*版】.*?)([A-H][0-9]+?[A-Z])',line,re.DOTALL)
            #print title.group(1)
            #print cl.group(2)
            if count == 1 or zipf < 0:
                if type == 3 and zipf < 0:
                    result = sm.dg3(root+name,cll,b,s,p,wtolu,ltow,ukk)
                else:
                    result = sm.dg(root+name,cll,sys.argv[3],b,s,wtolu,ukk,zipf,type)
            else:
                if type == 3 and zipf < 0:
                    result = sm.dg4(root+name,cll,b,s,p,wtolu,ltow,ukk,vecu)
                else:
                    result = sm.dg2(root+name,cll,sys.argv[3],b,s,wtolu,ukk,zipf,vecu,type)
            #print result[-1]
                
            dl = np.array([10.0 for i in range(0,len(result)-1)])
            dlu = np.array([10.0 for i in range(0,len(result)-1)])
            mt = []
	    for i in range(0,len(result)-1):
                if count == 1:
                    vect[i] = sm.vecof(result[i],a,wtola,akk)
                    mt.append(vect[i].max())
                    vecut[i] = sm.vecof0(result[i],b,s,wtolu,ukk)
		else:
                    vecr = sm.vecof(result[i],a,wtola,akk)
                    mt.append(vecr.max())
                    vecur = sm.vecof0(result[i],b,s,wtolu,ukk)
                    for j in range(0,len(result)-1):
                        dlt = spatial.distance.cosine(vecr,vec[j])
                        #print i,j,vecr.argmax(),dlt
                        if(dlt<dl[i]):
                            dl[i] = dlt
                            vect[i] = vec[j]
                        dlt = spatial.distance.cosine(vecur,vecu[j])
                        #print vecur,vecu[j]
                        #print i,j,vecur.argmax(),dlt
                        if(dlt<dlu[i]):
                            dlu[i] = dlt
                            vecut[i] = vecu[j]
                    vecut[i] = (vecur + vecut[i] * count)/(count+1)
                    vect[i] = (vecr + vect[i] * count)/(count+1)
            
            for i in range(0,len(result)-1):
                vec[i] = vect[i]        
                vecu[i] = vecut[i]
            if count > 1:
                total = total +1
                if dl.argmin() == int(result[-1]):
                    hit = hit + 1
            if np.array(mt).argmax() == int(result[-1]):
                mthit = mthit + 1
            if np.array(mt).argmin() == int(result[-1]):
                mtls = mtls + 1

            #print dl.argmin(),hit,result[-1],np.array(mt).argmax()


print 'usernum:',usernum
print 'hit:',hit
print 'mthit:',mthit
print 'mthls:',mtls
print 'total:',total
print 'hit/total:',hit*1.0/total
print 'mthit/total:',mthit*1.0/total
print 'mthls/total:',mtls*1.0/total
