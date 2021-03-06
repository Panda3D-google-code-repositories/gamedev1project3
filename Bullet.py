from direct.showbase.DirectObject import DirectObject  #for event handling
from direct.actor.Actor import Actor #for animated models
from direct.task import Task
import sys, math, random
from direct.interval.IntervalGlobal import * #for compound intervals
from pandac.PandaModules import * #basic Panda modules
from direct.interval.IntervalGlobal import *

class Bullet(DirectObject):
    def __init__(self,startPos):
        self.bullet = render.attachNewNode(ActorNode("bullet"))
        self.model = loader.loadModel("models/bullet")
        self.model.reparentTo(self.bullet)
        self.bullet.setScale(.08)
        self.startPos = startPos
       
        self.cNode = CollisionNode("bullet")
        self.cTube = CollisionTube(0,-1,0,0,1,0, 5)
        self.cNode.addSolid(self.cTube)
        self.cNodePath = self.bullet.attachNewNode(self.cNode)
        #self.cNodePath.show()
        
    
    def fire(self, velocity,hpr):
    #############################################################
    ## ATTENTION: if you get the error "global name 'Parabolaf' is
    ##not defined either a) pick up the latest release for fix or b)
    ##hand edit <panda location>/direct/interval/ProjectileInterval.py 
    ##and rename Parabolaf with LParabola
    #############################################################
    ############################################################
        #print(" SHOOT")
        self.bullet.wrtReparentTo(render)
        self.bullet.setHpr(hpr)
        self.trajectory = ProjectileInterval(self.bullet,startPos=self.startPos,startVel=velocity, duration=5, gravityMult = .1)
        self.trajectory.start()