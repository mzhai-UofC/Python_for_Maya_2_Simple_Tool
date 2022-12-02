#Create GUI
def Rename_Tool():
    windowName='RenameScriptWindow'
    windowTitle='Rename Tool 1.0'
    
    try:
        cmds.deleteUI(windowName)
    except:
        pass
    cmds.window(windowName,title=windowTitle)
    cmds.columnLayout(adj=True)
   
    cmds.rowLayout(numberOfColumns=2,columnWidth2=(75,150),adj=2)
    cmds.text(l='name:')
    cmds.textField('renameTF')
    cmds.setParent('..')
   
    cmds.rowLayout(numberOfColumns=3,columnWidth3=(75,100,100))
    cmds.text(l='S&P:')
    cmds.textField('paddingTF',tx='1,3')
    cmds.checkBox(l='remove suffix')
    cmds.setParent('..')
   
    cmds.button(l='Rename',h=50,c='renewName()')   
    
    cmds.window(windowName,e=True,w=300,h=1)
    cmds.showWindow(windowName)
   
def renewName():
    list_sel=cmds.ls(sl=True)
    str_input=cmds.textField('renameTF',q=True,tx=True)
    
    str_padding=cmds.textField('paddingTF',q=True,tx=True)
    str_starting,str_padding=str_padding.split(',')
    
    str_number=str_starting.zfill(int(str_padding))
    
    for name_1 in list_sel:
        cmds.rename(name_1,str_input+str_number)
        str_number=str(int(str_number)+1).zfill(int(str_padding))