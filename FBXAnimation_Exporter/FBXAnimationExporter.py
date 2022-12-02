import maya.cmds as cmds
import maya.mel as mel
import string
#Export settings in maya
mel.eval("source FBXAnimationExporter_FBXOptions.mel")

###############################################################################

#                                 Export Procedures

###############################################################################

#=======================Export FBX===============================================

def ExportFBX(exportNode):
    curWorkspace = cmds.workspace(q=True, rd=True)
    fileName = cmds.getAttr(exportNode + ".exportName")
    
    if fileName:
        newFBX = curWorkspace + fileName
        cmds.file(newFBX, force = True, type = 'FBX export', pr=True, es=True)
    else:
        cmds.warning("No Valid Export Filename for Export Node " + exportNode + "\n")

#========================== ExportFBXCharacter ===================================== 
      
def ExportFBXCharacter(exportNode):
    origin = ReturnOrigin("")
    
    exportNodes = []

    if exportNode:
        exportNodes.append(exportNode)
    else:
        exportNodes = ReturnFBXExportNodes(origin)
        
    parentNode = cmds.listRelatives(origin, parent=True, fullPath = True)
    
    if parentNode:
        cmds.parent(origin, world = True)
        
    for curExportNode in exportNodes:
        if cmds.getAttr(curExportNode + ".export"):
            mel.eval("SetFBXExportOptions_model()")
            
            cmds.select(clear = True)
            
            meshes = ReturnConnectedMeshes(exportNode)
            cmds.select(origin, add = True)
            cmds.select(meshes, add = True)
            
            ExportFbx(curExportNode)
            
        if parentNode:
            cmds.parent(origin, parentNode[0])

#============================== ExportFBXAnimation ==============================
 
def ExportFBXAnimation(characterName, exportNode):

    ClearGarbage()
    characters = []
    
    if characterName:
        characters.append(characterName)
    else:
        reference = cmd.file(reference=1, query = True)
        for curRef in references:
            characters.append(cmds.file(curRef, namespace = 1, query = True))
            
    for curCharacter in characters:
        
        #get meshes with blendshapes
        meshes = FindMeshesWithBlendshapes(curCharacter)
        
        #get origin
        origin = ReturnOrigin(curCharacter)
        
        exportNodes = []
        
        if exportNode:
            exportNodes.append(exportNode)
        else:
            exportNodes = ReturnFBXExportNodes(origin)
            
        
        for curExportNode in exportNodes:
            if cmds.getAttr(curExportNode + ".export") and origin != "Error":
                exportRig = CopyAndConnectSkeleton(origin)
                
                startFrame = cmds.playbackOptions(query=True, minTime=1)
                endFrame = cmds.playbackOptions(query=True, maxTime=1)

                subAnimCheck = cmds.getAttr(curExportNode + ".useSubRange")
                
                if subAnimCheck:
                    startFrame = cmds.getAttr(curExportNode + ".startFrame")
                    endFrame = cmds.getAttr(curExportNode + ".endFrame")
                    
                if cmds.getAttr(curExportNode + ".moveToOrigin"):
                    newOrigin = cmds.listConnections(origin + ".translateX", source = False, d = True)
                    zeroOriginFlag = cmds.getAttr(curExportNode + ".zerOrigin")
                    TransformToOrigin(newOrigin[0], startFrame, endFrame, zeroOriginFlag)

                cmds.select(clear = True)
                cmds.select(exportRig, add=True)
                cmds.select(meshes, add=True)
                
                SetAnimLayersFromSettings(curExportNode)
                
                mel.eval("SetFBXExportOptions_animation(" + str(startFrame) + "," + str(endFrame) + ")")
                
                ExportFBX(curExportNode)
                
                ClearGarbage() 
                 
####################################################################################### 

#                            Basic Procedures

#######################################################################################
                          
#PURPOSE         Return the origin of the given namespace
#PROCEDURE       If ns is not empty string, list all joints with the matching namespace, else list all joints
#                for list of joints, look for origin attribute and ifit is set to true. If found, return name of joint, else
#                return "Error"
#PRESUMPTIONS    Origin attribute it on a joint
#                "Error" is not a valid joint name. namespace does not include colon
def ReturnOrigin(ns):
    
    joints = []
    
    if ns:
        joints = cmds.ls((ns + ":*"), type = "joint")
    else:
        joints = cmds.ls(type = "joint")
        
    if len(joints):
        for curJoint in joints:
            if cmds.objExists(curJoint + ".origin") and cmds.getAttr(curJoint + ".origin"):
                return curJoint
                
    return "Error"

#PURPOSE      Removes all nodes taged as garbage
#PROCEDURE    List all transforms in the scene. Itterate through list, anything with "deleteMe" attribute will be deleted
#PRESUMPTIONS The deleteMe attribute is name of the attribute signifying garbage

def ClearGarbage():
    list = cmds.ls(tr=True)
    
    for cur in list:
        if cmds.objExists(cur + ".deleteMe"):
            cmds.delete(cur)
            
#PURPOSE        Tag object for being garbage
#PROCEDURE      If node is valid object and attribute does not exists, add deleteMe attribute
#PRESUMPTIONS   None
            
def TagForGarbage(node):    
    if cmds.objExists(node)and not cmds.objExists(node + ".deleteMe"):
        cmds.addAttr(node, shortName = "del", longName = "deleteMe", at = "bool")
        cmds.setAttr(node + ".deleteMe", True)    

def TagForMeshExport(mesh):
    if cmds.objExists(mesh) and not cmds.objExists(mesh + ".exportMeshes"):
        cmds.addAttr(mesh, shortName = "xms", longName = "exportMeshes", at = "message")
        
def TagForExportNode(node):
    if cmds.objExists(node) and not cmds.objExists(node + ".exportNode"):
        cmds.addAttr(node, shortName = "xnd", longName = "exportNode", at = "message")
        
#PURPOSE          Return the meshes connected to blendshape nodes
#PROCEDURE        Get a list of blendshape nodes Follow those connections to the mesh shape node Traverse up the hierarchy to find parent transform node
#PRESUMPTIONS     character has a valid namespace, namespace does not have colon only exporting polygonal meshes

def FindMeshesWithBlendshapes(ns):
    
    returnArray = []
    
    blendshapes = cmds.ls((ns + ":*" ), type = "blendShape")
    
    for curBlendShape in blendshapes:
        downstreamNodes = cmds.listHistory(curBlendShape, future = True)
        for curNode in downstreamNodes:
            if cmds.objectType(curNode, isType = "mesh"):
                parents = cmds.listRelatives(curNode, parent = True)
                returnArray.append(parents[0])
    
    return returnArray
    
#PURPOSE        Return all export nodes connected to given origin
#PROCEDURE      if origin is valid and has the exportNode attribute, return list of export nodes connected to it  
#PRESUMPTIONS   Only export nodes are connected to exportNode attribute

def ReturnFBXExportNodes(origin):
    exportNodeList=[]
    
    if cmds.objExists(origin + ".exportNode"):
        exportNodeList = cmds.listConnections(origin + ".exportNode")
        
    return exportNodeList

#PURPOSE        to add the attribute to the export node to store our export settings
#PROCEDURE       for each attribute we want to add, check if it existsif it doesn't exist, add
#PRESUMPTIONS    assume fbxExportNode is a valid object

def AddFBXNodeAttrs(fbxExportNode):
	
	if not cmds.attributeQuery("export", node=fbxExportNode, exists=True):
		cmds.addAttr(fbxExportNode, longName='export', at="bool")
	
	if not cmds.attributeQuery("moveToOrigin", node=fbxExportNode, exists=True):
		cmds.addAttr(fbxExportNode, longName='moveToOrigin', at="bool")
		
	if not cmds.attributeQuery("zeroOrigin", node=fbxExportNode, exists=True):
		cmds.addAttr(fbxExportNode, longName='zeroOrigin', at="bool")

	if not cmds.attributeQuery("exportName", node=fbxExportNode, exists=True):					   
		cmds.addAttr(fbxExportNode, longName='exportName', dt="string")
	
	if not cmds.attributeQuery("useSubRange", node=fbxExportNode, exists=True):		
		cmds.addAttr(fbxExportNode, longName='useSubRange', at="bool")
	
	if not cmds.attributeQuery("startFrame", node=fbxExportNode, exists=True):	  
		cmds.addAttr(fbxExportNode, longName='startFrame', at="float")
	
	if not cmds.attributeQuery("endFrame", node=fbxExportNode, exists=True):			  
		cmds.addAttr(fbxExportNode, longName='endFrame', at="float")
		
	if not cmds.attributeQuery("exportMeshes", node=fbxExportNode, exists=True):	
		cmds.addAttr(fbxExportNode, longName='exportMeshes', at="message")
		
	if not cmds.attributeQuery("exportNode", node=fbxExportNode, exists=True):		  
		cmds.addAttr(fbxExportNode, shortName = "xnd", longName='exportNode', at="message")	
		
	if not cmds.attributeQuery("animLayers", node=fbxExportNode, exists=True):					   
		cmds.addAttr(fbxExportNode, longName='animLayers', dt="string")
		

#PURPOSE          create the export node to store our export settings
#PROCEDURE        create an empty transform node we will send it to AddFBXNodeAttrs to add the needed attribute
		
def CreateFBXExportNode(characterName):
    fbxExportNode = cmds.group(em = True, name = characterName + "FBXExportNode#")
    AddFBXNodeAttrs(fbxExportNode)
    cmds.setAttr(fbxExportNode + ".export", 1)
    return fbxExportNode
    
#PURPOSE        return a list of all meshes connected to the export node
#PROCEDURE      listConnections to exportMeshes attribute
#PRESUMPTION    exportMeshes attribute is used to connect to export meshes, exportMeshes is valid

def ReturnConnectedMeshes(exportNode):
    meshes = cmds.listConnections((exportNode + ".exportMeshes"), source = False, destination = True)
    return meshes   
         
#PURPOSE        To copy the bind skeleton and connect the copy to the original bind
#PROCEDURE      duplicate hierarchy delete everything that is not a joint unlock all the joints connect the translates, rotates, and scales
#               parent copy to the world add deleteMe attr 
#PRESUMPTIONS   No joints are children of anything but other joints

def CopyAndConnectSkeleton(origin):
    newHierarchy=[]
    
    if origin != "Error" and cmds.objExists(origin):
        dupHierarchy = cmds.duplicate(origin)
        tempHierarchy = cmds.listRelatives(dupHierarchy[0], allDescendents=True, f=True)

        for cur in tempHierarchy:
            if cmds.objExists(cur):
                if cmds.objectType(cur) != "joint":
                    cmds.delete(cur)

        UnlockJointTransforms(dupHierarchy[0])
  
       
        origHierarchy = cmds.listRelatives(origin, ad=True, type = "joint")
        newHierarchy = cmds.listRelatives(dupHierarchy[0], ad=True, type = "joint")

        
        origHierarchy.append(origin)
        newHierarchy.append(dupHierarchy[0])
        

        
        for index in range(len(origHierarchy)):
        	ConnectAttrs(origHierarchy[index], newHierarchy[index], "translate")
        	ConnectAttrs(origHierarchy[index], newHierarchy[index], "rotate")
        	ConnectAttrs(origHierarchy[index], newHierarchy[index], "scale")
        	
        cmds.parent(dupHierarchy[0], world = True)
        TagForGarbage(dupHierarchy[0])
        
    return newHierarchy
    
    
def UnlockJointTransforms(root):
    hierarchy = cmds.listRelatives(root, ad=True, f=True)
    
    hierarchy.append(root)
    
    for cur in hierarchy:
		cmds.setAttr( (cur + '.translateX'), lock=False )
		cmds.setAttr( (cur + '.translateY'), lock=False )
		cmds.setAttr( (cur + '.translateZ'), lock=False )
		cmds.setAttr( (cur + '.rotateX'), lock=False )
		cmds.setAttr( (cur + '.rotateY'), lock=False )
		cmds.setAttr( (cur + '.rotateZ'), lock=False )
		cmds.setAttr( (cur + '.scaleX'), lock=False )
		cmds.setAttr( (cur + '.scaleY'), lock=False )
		cmds.setAttr( (cur + '.scaleZ'), lock=False )


#PURPOSE        Translate export skeleton to origin. May or may not kill origin animation depending on input
#PROCEDURE      bake the animation onto our origin create an animLayer
#               animLayer will either be additive or overrride depending on parameter we pass add deleteMe attr to animLayer move to origin
#PRESUMPTIONS   origin is valid, end frame is greater than start frame, zeroOrigin is boolean

def TransformToOrigin(origin, startFrame, endFrame, zeroOrigin):
    cmds.bakeResults(origin, t = (startFrame, endFrame), at= ["rx","ry","rz","tx","ty","tz","sx","sy","sz"], hi="none")
    
    cmds.select(clear = True)
    cmds.select(origin)
    
    newNaimLayer = ""
    
    if zeroOrigin:
        #kills origin animation 
        newAnimLayer = cmds.animLayer(aso=True, mute = False, solo = False, override = True, passthrough = True, lock = False)
        cmds.setAttr (newAnimLayer + ".rotationAccumulationMode", 0)
        cmds.setAttr (newAnimLayer + ".scaleAccumulationMode", 1)
    else:
        #shifts origin animation 
        newAnimLayer = cmds.animLayer(aso=True, mute = False, solo = False, override = False, passthrough = False, lock = False)
        
    TagForGarbage(newAnimLayer)
    
    #turn anim layer on
    cmds.animLayer(newAnimLayer, edit = True, weight = 1)
    cmds.setKeyframe(newAnimLayer + ".weight")
    
    #move origin animation to world origin
    cmds.setAttr(origin + ".translate", 0,0,0)
    cmds.setAttr(origin + ".rotate", 0,0,0)
    cmds.setKeyframe(origin, al=newAnimLayer, t=startFrame)

    
#PURPOSE        Connect the fbx export node to the origin
#PROCEDURE      check if attribute exist and nodes are valid if they are, connect attributes
#PRESUMPTIONS   none
def ConnectFBXExportNodeToOrigin(exportNode, origin):

    if cmds.objExists(origin) and cmds.objExists(exportNode):
        
        if not cmds.objExists(origin + ".exportNode"):
            TagForExportNode(origin)
            
        if not cmds.objExists(exportNode + ".exportNode"):
            AddFBXNodeAttrs(fbxExportNode)
            
        cmds.connectAttr(origin + ".exportNode", exportNode + ".exportNode")
        
def SIP_TagForExportNode(node):
    if cmds.objExists(node) and not cmds.objExists(node + ".exportNode"):
        cmds.addAttr(node, shortName = "xnd", longName = "exportNode", at = "message")

#PURPOSE        to connect given node to other given node via specified transform
#PROCEDURE      call connectAttr
#PRESUMPTIONS   assume two nodes exist and transform type is valid
def ConnectAttrs(sourceNode, destNode, transform):
    cmds.connectAttr(sourceNode + "." + transform + "X", destNode + "." + transform + "X")
    cmds.connectAttr(sourceNode + "." + transform + "Y", destNode + "." + transform + "Y")
    cmds.connectAttr(sourceNode + "." + transform + "Z", destNode + "." + transform + "Z")

            

############################################################################################       
		
#                                   Anim Layer Procedures 

###############################################################################################

#PURPOSE        Record the animLayer settings used in animation and store in the exportNode as a string
#PROCEDURE      List all the animLayers. Query their mute and solo attributes.
#               List them in one single string Uses ; as sentinal value to split seperate animLayers
#               Uses , as sentinal value to split seperate fields for animLayer Uses = as sentinal value to split seperate attrs from thier values in field
#PRESUMPTION    None
def SetAnimLayerSettings(exportNode):
 
    if not cmds.attributeQuery("animLayers", node=exportNode, exists=True):					   
        AddFBXNodeAttrs(exportNode)	
    
    animLayers = cmds.ls(type = "animLayer")
    
    animLayerCommandStr = ""
    
    for curLayer in animLayer:
        mute = cmds.animLayer(curLayer, query = True, mute = True)
        solo = cmds.animLayer(curLayer, query = True, solo = True)
        animLayerCommandStr += (curLayer + ", mute = " + str(mute) + ", solo = " + str(solo) + ";")
        
    cmds.setAttr(exportNode + ".animLayers", animLayerCommandStr, type = "string")    

#PURPOSE        Set the animLayers based on the string value in the exportNode
#PROCEDURE      Use pre-defined sentinal values to split the string for seperate animLayers And parse out the attributes and their values, then set
#PRESUMPTION    Uses ; as sentinal value to split seperate animLayers Uses , as sentinal value to split seperate fields for animLayer
#               Uses = as sentinal value to split seperate attrs from thier values in field order is Layer, mute, solo
def SetAnimLayersFromSettings(exportNode):
    
    if cmds.objExists(exportNode)and cmds.objExists(exportNode + ".animLayers"):
        animLayersRootString = cmds.getAttr(exportNode + ".animLayers", asString = True)
        
        if animLayersRootString:
            animLayerEntries = animLayersRootString.split(";")
            
            for curEntry in animLayerEntries:
                if curEntry:
                    fields = curEntry.split(",")
                    
                    animLayerField = fields[0]
                    curMuteField = fields[1]
                    curSoloField = fields[2]
                    
                    muteFieldStr = curMuteField.split(" = ")
                    soloFieldStr = curMuteField.split(" = ")
                    
                    #convert strings to bool values
                    muteFieldBool = True
                    soloFieldBool = True
                    
                    if muteFieldStr[1] != "True":
                        muteFieldBool = False                                        
    
                    if soloFieldStr[1] != "True":
                        soloFieldBool = False
                        
                    cmds.animLayer(animLayerField, edit = True, mute = muteFieldBool, solo = soloFieldBool)      
       
def ClearAnimLayerSettings(exportNode):
    cmds.setAttr(exportNode + ".animLayers", "", type = "string")



    






    







