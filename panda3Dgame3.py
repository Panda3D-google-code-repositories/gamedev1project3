from pandac.PandaModules import loadPrcFileData
from pandac.PandaModules import OdeWorld, OdeBody, OdeMass, Quat
loadPrcFileData('', 'win-size 800 640')
loadPrcFileData('', 'win-fixed-size #t')
from direct.directbase import DirectStart
from pandac.PandaModules import *    #basic Panda modules
from direct.showbase.DirectObject import DirectObject  #for event handling
from direct.actor.Actor import Actor #for animated models
from direct.interval.IntervalGlobal import *  #for compound intervals
from direct.task import Task         #for update fuctions
import sys, math, random
from decimal import Decimal,ROUND_DOWN
from direct.gui.OnscreenText import OnscreenText
from Plane import *
from Environment import *
from Bullet import *
from collections import deque

class World(DirectObject): #subclassing here is necessary to accept events
    def __init__(self):
        #turn off mouse control, otherwise camera is not repositionable
        base.disableMouse()
        
        #set up for split screen
        wp = WindowProperties()
        wp.setTitle('player 1')
        base.win.requestProperties(wp)
        #second window
        w2 = base.openWindow()
        wp.setTitle('player 2')
        w2.requestProperties(wp)
        # self.dr = w2.makeDisplayRegion()
        # self.dr.setSort(20)
        # self.myCamera2d = NodePath(Camera('myCam2d'))
        # self.dr.setCamera(self.myCamera2d)
        # lens = OrthographicLens()
        # lens.setFilmSize(2,2)
        # lens.setNearFar(-1000,1000)
        # self.myCamera2d.node().setLens(lens)
        
        # self.myRender2d = NodePath('myRender2d')
        # self.myRender2d.setDepthTest(False)
        # self.myRender2d.setDepthWrite(False)
        # self.myCamera2d.reparentTo(self.myRender2d)
        
        
        #set camera 1
        base.camList[0].setPosHpr(0,-15,7,0,-15,0)
        #set camera 2
        base.camList[1].setPosHpr(0,-15,7,0,-15,0)

        self.loadModels()
        self.setupLights()
        self.setupSounds()
        render.setShaderAuto() #you probably want to use this
        
        #input
        self.accept("escape", sys.exit)
        
        self.plane1.mapKeys("r", "f", "throttle")
        self.plane1.mapKeys("w", "s", "pitch") #inverted
        self.plane1.mapKeys("a", "d", "yaw")
        self.plane1.mapKeys("q", "e", "roll")
        
        self.plane2.mapKeys("o", "l", "throttle")
        self.plane2.mapKeys("u", "j", "pitch") #inverted
        self.plane2.mapKeys("h", "k", "yaw")
        self.plane2.mapKeys("y", "i", "roll")
        
        #collision stuff
        self.accept("collide-tail_plane1", self.planeCollisions)
        self.accept("collide-bodyfront_plane1", self.planeCollisions)
        self.accept("collide-bodymid_plane1", self.planeCollisions)
        self.accept("collide-bodyrear_plane1", self.planeCollisions)
        self.accept("collide-lwouter_plane1", self.planeCollisions)
        self.accept("collide-rwouter_plane1", self.planeCollisions)
        self.accept("collide-lwinner_plane1", self.planeCollisions)
        self.accept("collide-rwinner_plane1", self.planeCollisions)
        self.accept("collide-tail_plane2", self.planeCollisions)
        self.accept("collide-bodyfront_plane2", self.planeCollisions)
        self.accept("collide-bodymid_plane2", self.planeCollisions)
        self.accept("collide-bodyrear_plane2", self.planeCollisions)
        self.accept("collide-lwouter_plane2", self.planeCollisions)
        self.accept("collide-rwouter_plane2", self.planeCollisions)
        self.accept("collide-lwinner_plane2", self.planeCollisions)
        self.accept("collide-rwinner_plane2", self.planeCollisions)
        
        
        #projectile/guns stuff
        self.accept("space",self.shootprep1)
        self.accept("alt", self.shootprep2)
        
        #bullet collisions
        self.accept("collide-bullet", self.bulletCollision)
        
        #ui task
        # self.textObject = OnscreenText(text=str(self.plane1.throttle), pos = (-.5,.02), scale=.07)
        # self.textObject2 = OnscreenText(text = str(self.plane2.throttle),pos=(0,0),scale=1)
        # self.textObject.reparentTo(render2d)
        # self.textObject2.reparentTo(self.myRender2d)
        # taskMgr.add(self.uiText, "uiTask")
        
        #bullet list
        self.bullets = set()
        
        
    def loadModels(self): #collision detection also here (keep with models for organization's sake)
        """loads models into the world and set's their collision bodies"""
        
        #basic collision setup
        base.cTrav = CollisionTraverser()
        base.cTrav.setRespectPrevTransform(True) #rapidly moving objects collision - for bullets
        self.cHandler = PhysicsCollisionHandler()
        self.cHandler.setInPattern("collide-%in")
        
        #environment
        # self.env = loader.loadModel("models/environment")
        # self.env.reparentTo(render)
        # self.env.setScale(.25)
        # self.env.setPos(-8, 42, 0)
        self.env = Environment()
        #base.cTrav.addCollider(self.env.envNode,self.cHandler)
        #self.cHandler.addCollider(self.env.envNode,self.env.dome)
        #for x in range(self.env.colDome.getNumChildren()):
            #for y in range(self.env.colDome.getChild(x).getNumNodes()):
                #print self.env.colDome.getChild(x).getNode(y)
        
        #player 1 plane
        self.plane1 = MyPlane(base.camList[0],"plane1")
        self.plane1.plane.setPos(100,20,200)
        #add pieces for collisions
        #tail
        print(self.plane1.tail_cNodePath)
        base.cTrav.addCollider(self.plane1.tail_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane1.tail_cNodePath, self.plane1.plane)
        #outer wing left
        base.cTrav.addCollider(self.plane1.lwouter_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane1.lwouter_cNodePath, self.plane1.plane)
        #outer wing right
        base.cTrav.addCollider(self.plane1.rwouter_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane1.rwouter_cNodePath, self.plane1.plane)
        #inner wing left
        base.cTrav.addCollider(self.plane1.lwinner_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane1.lwinner_cNodePath, self.plane1.plane)
        #inner wing right
        base.cTrav.addCollider(self.plane1.rwinner_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane1.rwinner_cNodePath, self.plane1.plane)
        #body three pieces
        base.cTrav.addCollider(self.plane1.bodyfront_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane1.bodyfront_cNodePath, self.plane1.plane)
        base.cTrav.addCollider(self.plane1.bodymid_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane1.bodymid_cNodePath, self.plane1.plane)
        base.cTrav.addCollider(self.plane1.bodyrear_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane1.bodyrear_cNodePath, self.plane1.plane)
        
        #player 2 plane
        self.plane2 = MyPlane(base.camList[1], "plane2")
        self.plane2.plane.setPos(100,0,200)
        #add pieces for collisions
        #tail
        base.cTrav.addCollider(self.plane2.tail_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane2.tail_cNodePath, self.plane2.plane)
         #outer wing left
        base.cTrav.addCollider(self.plane2.lwouter_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane2.lwouter_cNodePath, self.plane2.plane)
        #outer wing right
        base.cTrav.addCollider(self.plane2.rwouter_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane2.rwouter_cNodePath, self.plane2.plane)
        #inner wing left
        base.cTrav.addCollider(self.plane2.lwinner_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane2.lwinner_cNodePath, self.plane2.plane)
        #inner wing right
        base.cTrav.addCollider(self.plane2.rwinner_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane2.rwinner_cNodePath, self.plane2.plane)
        #body three pieces
        base.cTrav.addCollider(self.plane2.bodyfront_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane2.bodyfront_cNodePath, self.plane2.plane)
        base.cTrav.addCollider(self.plane2.bodymid_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane2.bodymid_cNodePath, self.plane2.plane)
        base.cTrav.addCollider(self.plane2.bodyrear_cNodePath, self.cHandler)
        self.cHandler.addCollider(self.plane2.bodyrear_cNodePath, self.plane2.plane)
        

        
        
        
    def setupLights(self):
        #ambient light
        #self.ambientLight = AmbientLight("ambientLight")
        #four values, RGBA (alpha is largely irrelevent), value range is 0:1
        #self.ambientLight.setColor((.25, .25, .25, 1))
        #self.ambientLightNP = render.attachNewNode(self.ambientLight)
        #the nodepath that calls setLight is what gets illuminated by the light
        #render.setLight(self.ambientLightNP)
        #call clearLight() to turn it off
        
        render.setShaderAuto()
        
        
        ##################################################
        ## Class code - example
        # self.keyLight = DirectionalLight("keyLight")
        # self.keyLight.setColor((.6,.6,.6, 1))
        # self.keyLightNP = render.attachNewNode(self.keyLight)
        # self.keyLightNP.setHpr(0, -26, 0)
        # render.setLight(self.keyLightNP)
        # self.fillLight = DirectionalLight("fillLight")
        # self.fillLight.setColor((.4,.4,.4, 1))
        # self.fillLightNP = render.attachNewNode(self.fillLight)
        # self.fillLightNP.setHpr(30, 0, 0)
        # render.setLight(self.fillLightNP)
        ######################################################
    
    def planeCollisions(self, cEntry):
        if cEntry.getIntoNodePath().getParent() != cEntry.getFromNodePath().getParent():
            #print(str(cEntry.getIntoNodePath()) + " " + str(cEntry.getFromNodePath()))
            
            #plane 1 body
            if str(cEntry.getIntoNodePath())=="render/plane1/bodyfront_plane1" or str(cEntry.getIntoNodePath())=="render/plane1/bodymid_plane1" or str(cEntry.getIntoNodePath())=="render/plane1/bodyrear_plane1":
                self.plane1.body_hp-=1
                print("plane1 body hp = " + str(self.plane1.body_hp))
                if(self.plane1.body_hp < 16):
                    self.engine1.stop()
                    self.engine_damaged1.setLoopCount(0)
                    self.engine_damaged1.play()
                #check for game over
                if(self.plane1.body_hp<=0):
                    print("plane1 dead!")
                    #remove whole plane
                    cEntry.getIntoNodePath().getParent().remove()
                    self.explosion.play()
                
            #plane 2 body
            elif str(cEntry.getIntoNodePath()) == "render/plane2/bodyfront_plane2" or str(cEntry.getIntoNodePath())== "render/plane2/bodymid_plane2" or str(cEntry.getIntoNodePath())== "render/plane2/bodyrear_plane2":
                self.plane2.body_hp-=1
                print("plane2 body hp = " + str(self.plane2.body_hp))
                if(self.plane2.body_hp < 16):
                    self.engine2.stop()
                    self.engine_damaged2.setLoopCount(0)
                    self.engine_damaged2.play()
                #check for game over
                if(self.plane2.body_hp<=0):
                    print("plane2 dead!")
                    #remove whole plane
                    cEntry.getIntoNodePath().getParent().remove()
                    self.explosion.play()
                
            #plane 1 tail
            elif str(cEntry.getIntoNodePath()) == "render/plane1/tail_plane1":
                self.plane1.tail_hp-=1
                print("plane1 tail hp = " + str(self.plane1.tail_hp))
                if(self.plane1.tail_hp<=0):
                    print("plane1 lost tail!")
                    cEntry.getIntoNodePath().remove() #remove cnode
                    self.plane1.model_tail.remove() #remove model
                    self.plane1.has_tail=False
                    self.plane1.controlLimits["yaw"] = 0
                    self.plane1.controlLimits["pitch"] = 10
                    self.plane1.controlFactors["pitch"] = 10
                    
            #plane2 tail
            elif str(cEntry.getIntoNodePath()) =="render/plane2/tail_plane2":
                self.plane2.tail_hp-=1
                print("plane2 tail hp = " + str(self.plane2.tail_hp))
                if(self.plane2.tail_hp<=0):
                    print("plane2 lost tail!")
                    cEntry.getIntoNodePath().remove() # remove cnode
                    self.plane2.model_tail.remove() #remove model
                    self.plane2.has_tail = False
                    self.plane2.controlLimits["yaw"] = 0
                    self.plane2.controlLimits["pitch"] = 10
                    self.plane2.controlFactors["pitch"] = 10
                    
            #plane1 left outer wing
            elif str(cEntry.getIntoNodePath()) == "render/plane1/lwouter_plane1":
                self.plane1.lwo_hp-=1
                print("plane1 left outer wing hp = " + str(self.plane1.lwo_hp))
                if(self.plane1.lwo_hp<=0):
                    print("plane1 lost lwo!")
                    cEntry.getIntoNodePath().remove() #remove cnode
                    self.plane1.model_lwo.remove() #remove model
                    self.plane1.has_lwo= False 
                    render.clearLight(self.plane1.spotlightNP2)
                    
            #plane2 left outer wing
            elif str(cEntry.getIntoNodePath()) =="render/plane2/lwouter_plane2":
                self.plane2.lwo_hp-=1
                print("plane2 left outer wing hp = " + str(self.plane2.lwo_hp))
                if(self.plane2.lwo_hp<=0):
                    print("plane2 lost lwo!")
                    cEntry.getIntoNodePath().remove() #remove cnode
                    self.plane2.model_lwo.remove() #remove model
                    self.plane2.has_lwo = False
                    render.clearLight(self.plane2.spotlightNP2)
                      
            #plane1 right outer wing
            elif str(cEntry.getIntoNodePath()) =="render/plane1/rwouter_plane1":
                self.plane1.rwo_hp-=1
                print("plane1 right outer wing hp = " + str(self.plane1.rwo_hp))
                if(self.plane1.rwo_hp<=0):
                    print("plane1 lost rwo!")
                    cEntry.getIntoNodePath().remove() #remove cnode
                    self.plane1.model_rwo.remove() #remove model
                    self.plane1.has_rwo = False
                    render.clearLight(self.plane1.spotlightNP1)
                    
            #plane2 right outer wing
            elif str(cEntry.getIntoNodePath()) == "render/plane2/rwouter_plane2":
                self.plane2.rwo_hp-=1
                print("plane2 right outer wing hp = " + str(self.plane2.rwo_hp))
                if(self.plane2.rwo_hp<=0):
                    print("plane2 lost rwo!")
                    cEntry.getIntoNodePath().remove() #remove cnode
                    self.plane2.model_rwo.remove() #remove model
                    self.plane2.has_rwo=False
                    render.clearLight(self.plane2.spotlightNP1)
                    
            #plane1 left inner wing
            elif str(cEntry.getIntoNodePath()) == "render/plane1/lwinner_plane1":
                self.plane1.lwi_hp -=1
                print("plane1 left inner wing hp = " + str(self.plane1.lwi_hp))
                if(self.plane1.lwi_hp<=0):
                    print("plane1 lost lwi!")
                    self.plane1.canFireLeft=False
                    cEntry.getIntoNodePath().remove() #remove cnode
                    self.plane1.model_lwi.remove() #remove model
                    self.plane1.has_lwi=False
                    #remove lwo too if it still exists
                    if(self.plane1.has_lwo):
                        self.plane1.lwouter_cNodePath.remove()
                        self.plane1.model_lwo.remove()
                        self.plane1.has_lwo=False
                        print("and lwo!")
                        render.clearLight(self.plane1.spotlightNP2)
                    
            #plane 2 left inner wing
            elif str(cEntry.getIntoNodePath()) == "render/plane2/lwinner_plane2":
                self.plane2.lwi_hp-=1
                print("plane2 left inner wing hp = " + str(self.plane1.lwi_hp))
                if(self.plane2.lwi_hp<=0):
                    print("plane2 lost lwi!")
                    self.plane2.canFireLeft = False
                    cEntry.getIntoNodePath().remove() #remove cnode
                    self.plane2.model_lwi.remove() #remove model
                    self.plane2.has_lwi=False
                    #remove lwo too if it still exists
                    if(self.plane2.has_lwo):
                        self.plane2.lwouter_cNodePath.remove()
                        self.plane2.model_lwo.remove()
                        self.plane2.has_lwo=False
                        print("and lwo!")
                        render.clearLight(self.plane2.spotlightNP2)
                    
            #plane 1 right inner wing
            elif str(cEntry.getIntoNodePath()) == "render/plane1/rwinner_plane1":
                self.plane1.rwi_hp-=1
                print("plane1 right inner wing hp = " + str(self.plane1.rwi_hp))
                if(self.plane1.rwi_hp<=0):
                    print("plane1 lost rwi!")
                    self.plane1.canFireRight=False
                    cEntry.getIntoNodePath().remove() #remove cnode
                    self.plane1.model_rwi.remove() #remove model
                    self.plane1.has_rwi=False
                    #remove rwo too if it still exists
                    if(self.plane1.has_rwo):
                        self.plane1.rwouter_cNodePath.remove()
                        self.plane1.model_rwo.remove()
                        self.plane1.has_rwo=False
                        print("and rwo!")
                        render.clearLight(self.plane1.spotlightNP1)
                    
            #plane 2 right inner wing
            elif str(cEntry.getIntoNodePath()) == "render/plane2/rwinner_plane2":
                self.plane2.rwi_hp-=1
                print("plane2 right inner wing hp = " + str(self.plane2.rwi_hp))
                if(self.plane2.rwi_hp<=0):
                    print("plane2 lost rwi!")
                    self.plane2.canFireRight = False
                    cEntry.getIntoNodePath().remove() #remove cnode
                    self.plane2.model_rwi.remove() #remove model
                    self.plane2.has_rwi=False
                    #remove rwo too if it still exists
                    if(self.plane2.has_rwo):
                        self.plane2.rwouter_cNodePath.remove()
                        self.plane2.model_rwo.remove()
                        self.plane2.has_rwo=False
                        print("and rwo!")
                        render.clearLight(self.plane2.spotlightNP1)
            else:
                "what the f$%k did I hit!?!"
                
    def bulletCollision(self,cEntry):
        #plane 1 body
        if str(cEntry.getFromNodePath())=="render/plane1/bodyfront_plane1" or str(cEntry.getFromNodePath())=="render/plane1/bodymid_plane1" or str(cEntry.getFromNodePath())=="render/plane1/bodyrear_plane1":
            self.plane1.body_hp-=1
            print("plane1 body hp = " + str(self.plane1.body_hp))
            self.bullet_hit.play()
            if(self.plane1.body_hp < 16):
                self.engine1.stop()
                self.engine_damaged1.setLoopCount(0)
                self.engine_damaged1.play()
            #check for game over
            if(self.plane1.body_hp<=0):
                print("plane1 dead!")
                #remove whole plane
                cEntry.getFromNodePath().getParent().remove()
            
        #plane 2 body
        elif str(cEntry.getFromNodePath()) == "render/plane2/bodyfront_plane2" or str(cEntry.getFromNodePath())== "render/plane2/bodymid_plane2" or str(cEntry.getFromNodePath())== "render/plane2/bodyrear_plane2":
            self.plane2.body_hp-=1
            self.bullet_hit.play()
            print("plane2 body hp = " + str(self.plane2.body_hp))
            if(self.plane2.body_hp < 16):
                self.engine2.stop()
                self.engine_damaged2.setLoopCount(0)
                self.engine_damaged2.play()
            #check for game over
            if(self.plane2.body_hp<=0):
                print("plane2 dead!")
                #remove whole plane
                cEntry.getFromNodePath().getParent().remove()
            
        #plane 1 tail
        elif str(cEntry.getFromNodePath()) == "render/plane1/tail_plane1":
            self.plane1.tail_hp-=1
            self.bullet_hit.play()
            print("plane1 tail hp = " + str(self.plane1.tail_hp))
            if(self.plane1.tail_hp<=0):
                print("plane1 lost tail!")
                cEntry.getFromNodePath().remove() #remove cnode
                self.plane1.model_tail.remove() #remove model
                self.plane1.has_tail=False
                self.plane1.controlLimits["yaw"] = 0
                self.plane1.controlLimits["pitch"] = 10
                self.plane1.controlFactors["pitch"] = 10
                
        #plane2 tail
        elif str(cEntry.getFromNodePath()) =="render/plane2/tail_plane2":
            self.plane2.tail_hp-=1
            self.bullet_hit.play()
            print("plane2 tail hp = " + str(self.plane2.tail_hp))
            if(self.plane2.tail_hp<=0):
                print("plane2 lost tail!")
                cEntry.getFromNodePath().remove() # remove cnode
                self.plane2.model_tail.remove() #remove model
                self.plane2.has_tail = False
                self.plane2.controlLimits["yaw"] = 0
                self.plane2.controlLimits["pitch"] = 10
                self.plane2.controlFactors["pitch"] = 10
                
        #plane1 left outer wing
        elif str(cEntry.getFromNodePath()) == "render/plane1/lwouter_plane1":
            self.plane1.lwo_hp-=1
            self.bullet_hit.play()
            print("plane1 left outer wing hp = " + str(self.plane1.lwo_hp))
            if(self.plane1.lwo_hp<=0):
                print("plane1 lost lwo!")
                cEntry.getFromNodePath().remove() #remove cnode
                self.plane1.model_lwo.remove() #remove model
                self.plane1.has_lwo= False 
                render.clearLight(self.plane1.spotlightNP2)
                
        #plane2 left outer wing
        elif str(cEntry.getFromNodePath()) =="render/plane2/lwouter_plane2":
            self.plane2.lwo_hp-=1
            self.bullet_hit.play()
            print("plane2 left outer wing hp = " + str(self.plane2.lwo_hp))
            if(self.plane2.lwo_hp<=0):
                print("plane2 lost lwo!")
                cEntry.getFromNodePath().remove() #remove cnode
                self.plane2.model_lwo.remove() #remove model
                self.plane2.has_lwo = False
                render.clearLight(self.plane2.spotlightNP2)
                  
        #plane1 right outer wing
        elif str(cEntry.getFromNodePath()) =="render/plane1/rwouter_plane1":
            self.plane1.rwo_hp-=1
            self.bullet_hit.play()
            print("plane1 right outer wing hp = " + str(self.plane1.rwo_hp))
            if(self.plane1.rwo_hp<=0):
                print("plane1 lost rwo!")
                cEntry.getFromNodePath().remove() #remove cnode
                self.plane1.model_rwo.remove() #remove model
                self.plane1.has_rwo = False
                render.clearLight(self.plane1.spotlightNP1)
                
        #plane2 right outer wing
        elif str(cEntry.getFromNodePath()) == "render/plane2/rwouter_plane2":
            self.plane2.rwo_hp-=1
            self.bullet_hit.play()
            print("plane2 right outer wing hp = " + str(self.plane2.rwo_hp))
            if(self.plane2.rwo_hp<=0):
                print("plane2 lost rwo!")
                cEntry.getFromNodePath().remove() #remove cnode
                self.plane2.model_rwo.remove() #remove model
                self.plane2.has_rwo=False
                render.clearLight(self.plane2.spotlightNP1)
                
        #plane1 left inner wing
        elif str(cEntry.getFromNodePath()) == "render/plane1/lwinner_plane1":
            self.plane1.lwi_hp -=1
            self.bullet_hit.play()
            print("plane1 left inner wing hp = " + str(self.plane1.lwi_hp))
            if(self.plane1.lwi_hp<=0):
                print("plane1 lost lwi!")
                self.plane1.canFireLeft = False
                cEntry.getFromNodePath().remove() #remove cnode
                self.plane1.model_lwi.remove() #remove model
                self.plane1.has_lwi=False
                #remove lwo too if it still exists
                if(self.plane1.has_lwo):
                    self.plane1.lwouter_cNodePath.remove()
                    self.plane1.model_lwo.remove()
                    self.plane1.has_lwo=False
                    print("and lwo!")
                    render.clearLight(self.plane1.spotlightNP2)
                
        #plane 2 left inner wing
        elif str(cEntry.getFromNodePath()) == "render/plane2/lwinner_plane2":
            self.plane2.lwi_hp-=1
            self.bullet_hit.play()
            print("plane2 left inner wing hp = " + str(self.plane1.lwi_hp))
            if(self.plane2.lwi_hp<=0):
                print("plane2 lost lwi!")
                self.plane2.canFireLeft=False
                cEntry.getFromNodePath().remove() #remove cnode
                self.plane2.model_lwi.remove() #remove model
                self.plane2.has_lwi=False
                #remove lwo too if it still exists
                if(self.plane2.has_lwo):
                    self.plane2.lwouter_cNodePath.remove()
                    self.plane2.model_lwo.remove()
                    self.plane2.has_lwo=False
                    print("and lwo!")
                    render.clearLight(self.plane2.spotlightNP2)
                
        #plane 1 right inner wing
        elif str(cEntry.getFromNodePath()) == "render/plane1/rwinner_plane1":
            self.plane1.rwi_hp-=1
            self.bullet_hit.play()
            print("plane1 right inner wing hp = " + str(self.plane1.rwi_hp))
            if(self.plane1.rwi_hp<=0):
                print("plane1 lost rwi!")
                self.plane1.canFireRight=False
                cEntry.getFromNodePath().remove() #remove cnode
                self.plane1.model_rwi.remove() #remove model
                self.plane1.has_rwi=False
                #remove rwo too if it still exists
                if(self.plane1.has_rwo):
                    self.plane1.rwouter_cNodePath.remove()
                    self.plane1.model_rwo.remove()
                    self.plane1.has_rwo=False
                    print("and rwo!")
                    render.clearLight(self.plane1.spotlightNP1)
                
        #plane 2 right inner wing
        elif str(cEntry.getFromNodePath()) == "render/plane2/rwinner_plane2":
            self.plane2.rwi_hp-=1
            self.bullet_hit.play()
            print("plane2 right inner wing hp = " + str(self.plane2.rwi_hp))
            if(self.plane2.rwi_hp<=0):
                print("plane2 lost rwi!")
                self.plane2.canFireRight=False
                cEntry.getFromNodePath().remove() #remove cnode
                self.plane2.model_rwi.remove() #remove model
                self.plane2.has_rwi=False
                #remove rwo too if it still exists
                if(self.plane2.has_rwo):
                    self.plane2.rwouter_cNodePath.remove()
                    self.plane2.model_rwo.remove()
                    self.plane2.has_rwo=False
                    print("and rwo!")
                    render.clearLight(self.plane2.spotlightNP1)
        else:
            "what the f$%k did I hit!?!"
    
    def clearBullet(self, bullet):
        base.cTrav.removeCollider(bullet.cNodePath)
        self.cHandler.removeCollider(bullet.cNodePath)
        bullet.trajectory.finish()
        bullet.bullet.removeNode()
        print "removed"
        return Task.done
        
    def shootprep1(self):
        if self.plane1.fireRight: #right guns turn
            if self.plane1.canFireRight: #right gun still exists
                pos = self.plane1.right_gun.getPos(render)
                #print(pos)
                self.plane1.fireRight = False
            elif self.plane1.canFireLeft:#no right gun, but left one
                self.plane1.fireRight = False 
                pos = self.plane1.left_gun.getPos(render)
            else:
                pass
        else: #left gun turn
            if self.plane1.canFireLeft: #left gun still exists
                pos = self.plane1.left_gun.getPos(render)
                self.plane1.fireRight = True
            elif self.plane1.canFireRight: #no left gun, but right one
                self.plane1.fireRight = True
                pos = self.plane1.right_gun.getPos(render)
            else:
                pass
                
        bullet = Bullet(pos)        
        vel= self.plane1.velocity + self.plane1.plane.getQuat().getForward() * -1 * 100
        base.cTrav.addCollider(bullet.cNodePath, self.cHandler)
        self.cHandler.addCollider(bullet.cNodePath, bullet.bullet)
        #self.bullets.append(bullet)
        #print(pos)
        bullet.fire(vel,self.plane1.plane.getHpr())
        self.machinegun.play()
        taskMgr.doMethodLater(bullet.trajectory.getDuration(), self.clearBullet, 'clear_bullet', extraArgs=[bullet])
    
    def shootprep2(self):
        if self.plane2.fireRight: #right guns turn
            if self.plane2.canFireRight: #right gun still exists
                pos = self.plane2.right_gun.getPos(render)
                #print(pos)
                self.plane2.fireRight = False
            elif self.plane2.canFireLeft:#no right gun, but left one
                self.plane2.fireRight = False 
                pos = self.plane2.left_gun.getPos(render)
            else:
                pass
        else: #left gun turn
            if self.plane2.canFireLeft: #left gun still exists
                pos = self.plane2.left_gun.getPos(render)
                self.plane2.fireRight = True
            elif self.plane2.canFireRight: #no left gun, but right one
                self.plane2.fireRight = True
                pos = self.plane2.right_gun.getPos(render)
            else:
                pass
                
        bullet = Bullet(pos)        
        vel= self.plane2.velocity + self.plane2.plane.getQuat().getForward() * -1 * 100
        base.cTrav.addCollider(bullet.cNodePath, self.cHandler)
        self.cHandler.addCollider(bullet.cNodePath, bullet.bullet)
        #self.bullets.append(bullet)
        #print(pos)
        bullet.fire(vel,self.plane2.plane.getHpr())
        self.machinegun.play()
        taskMgr.doMethodLater(bullet.trajectory.getDuration(), self.clearBullet, 'clear_bullet', extraArgs=[bullet])
        
    # def uiText(self,task):
        # self.textObject.remove()
        # self.textObject2.remove()
        # throttle = Decimal(str(self.plane1.throttle)).quantize(Decimal('.01'),rounding=ROUND_DOWN)
        # throttle2 = Decimal(str(self.plane2.throttle)).quantize(Decimal('.01'),rounding=ROUND_DOWN)
        # self.textObject = OnscreenText(text=str(throttle), pos = (-.5,.02), scale=.07)
        # self.textObject2 = OnscreenText(text=str(throttle2),pos = (-.5,.02), scale = .07)
        # return task.cont 
        
        
    def setupSounds(self):
        self.explosion = base.loader.loadSfx("sounds/explosion1.wav")
        
        self.engine1 = base.loader.loadSfx("sounds/engine.wav")
        self.engine2 = base.loader.loadSfx("sounds/engine.wav")
        self.engine1.setVolume(0.7)
        self.engine2.setVolume(0.7)
        
        self.engine_damaged1 = base.loader.loadSfx("sounds/engine_damaged.wav")
        self.engine_damaged2 = base.loader.loadSfx("sounds/engine_damaged.wav")
        self.engine_damaged1.setVolume(0.4)
        self.engine_damaged2.setVolume(0.4)
        
        self.machinegun = base.loader.loadSfx("sounds/machinegun2.wav")
        self.machinegun.setPlayRate(1.2)
        self.machinegun.setVolume(0.3)
        
        self.bullet_hit = base.loader.loadSfx("sounds/bullets_hitting.wav")       
        self.bullet_hit.setVolume(0.3)        
        
        self.engine1.setLoopCount(0)
        self.engine2.setLoopCount(0)
        self.engine1.play()
        self.engine2.play()
        
w = World()
run()

