import hou
import os
import re
import string

# removes all path till the last two slashes
# C:/Model/model1/maps/aaa.jpg -> maps/aaa.jpg
def pathCorrect(path):
    path=path.replace("\\","/")
    split=path.rsplit("/",2)[-2:]
    result=split[0]
    if len(split)>1:
        result+="/"+split[1]
    return result

################################################################
# Shader definition -- Change it to match your shader
################################################################
# name of the shader
#shader='mantrasurface' 
shader='redshift_vopnet'
# parameters for diffuse color
difr='diffuse_colorr'
difg='diffuse_colorg'
difb='diffuse_colorb'
# parameters for specular color
specr='spec_colorr'
specg='spec_colorg'
specb='spec_colorb'
# parameter for opacity
opacity='opac_int'
#parameter for IOR
ior='ior_in'
# parameters for maps
use_diffmap='diff_colorUseTexture'
diff_map='diff_colorTexture'
use_specmap='refl_colorUseTexture'
spec_map='refl_colorTexture'
use_alphamap='opacity_colorUseTexture'
alpha_map='opacity_colorTexture'
use_bumpmap='enableBumpOrNormalTexture'
bump_map='normalTexture'

###############################################################

#input obj
file_name=hou.ui.selectFile(file_type=hou.fileType.Geometry)
file_old=file_name
file_name=string.replace(file_name,'$HIP',hou.expandString('$HIP'),1)
file_path=os.path.split(file_old)[0]

geo = hou.node('/obj').createNode('geo')
fl=geo.createNode('file')
fl.parm('file').set(file_old)
fl.moveToGoodPosition()
geo.moveToGoodPosition()
name=os.path.splitext(os.path.basename(file_name))[0].replace(' ','_')
if name[0].isdigit(): #Houdini does not allow to name nodes with first digit character
    name="_"+name
geo.setName(name,True) # replace space with _

mysop=geo.node('file1').createOutputNode('attribstringedit')
mysop.moveToGoodPosition()

shop=geo.createNode('shopnet')
shop.moveToGoodPosition()

# create node to relink materials to internal shopnet
mysop.parm('primattriblist').set('shop_materialpath')
mysop.parm('regex0').set(1)
mysop.parm('from0').set('/mat/')
mysop.parm('to0').set('`opfullpath("../shopnet1")+"/"`')
mysop.setDisplayFlag(True)
mysop.setRenderFlag(True)

# Create shaders

file_name=os.path.splitext(file_name)[0]+".mtl"
# if mtl file not found
if not os.path.isfile(file_name): 
    print('No mtl file, choose manually')
    file_name=hou.ui.selectFile()
error=0
last=mysop
cur_mat = None
with open(file_name, 'r') as f:
    lines = f.read().splitlines()   # Read lines
f.close()
 
for line in lines:
    line=line.lstrip()          # remove beginning spaces
    line=' '.join(line.split()) # remove double spaces
    ary = line.split(' ')
    if ary[0] == 'newmtl':
        # Grab the name of this new material
        mat_name = ary[1]   
        cur_mat = shop.createNode(shader)
        cur_mat.moveToGoodPosition()
        cur_sh = cur_mat.createNode("redshift::Material")
        cur_sh.moveToGoodPosition()
        cur_out = cur_mat.children()[0]
        cur_out.setInput(0, cur_sh)
              
        # check if first symbol of mat name is digit (prohibited in Houdini)
        if mat_name[0].isdigit():
            print('MAT NAME CHANGED!')
            # Create node to rename material
            mysop=last.createOutputNode('attribstringedit')
            mysop.moveToGoodPosition()
            mysop.parm('primattriblist').set('shop_materialpath')
            mysop.parm('regex0').set(1)
            mysop.parm('from0').set('shopnet1/'+mat_name)
            mysop.parm('to0').set('shopnet1/_'+mat_name)
            mysop.setDisplayFlag(True)
            mysop.setRenderFlag(True)
            last=mysop
            mat_name='_'+mat_name
        
        # check if mat name has prohibited characters
        if not re.match(r'[:\w-]*$', mat_name):
            print('Mat name is changed')
            mysop=last.createOutputNode('attribstringedit')
            mysop.moveToGoodPosition()
            mysop.parm('primattriblist').set('shop_materialpath')
            mysop.parm('regex0').set(1)
            mysop.parm('from0').set('shopnet1/'+mat_name)
            mysop.parm('to0').set('shopnet1/_'+'mat_changed_'+str(error))
            mysop.setDisplayFlag(True)
            mysop.setRenderFlag(True)
            last=mysop
            mat_name='_'+'mat_changed_'+str(error)
            error+=1
            
        cur_mat.setName(mat_name,True) #rename material

    if ary[0] == 'Kd':
        # Found a diffuse color.
        if len(ary) == 4:
            cur_sh.setParms({difr: float(ary[1]),difg: float(ary[2]),difb: float(ary[3])})

    # maps
    if ary[0]== 'map_Kd' and len(ary)>1:
        cur_diffmap = cur_mat.createNode("redshift::TextureSampler")
        cur_sh.setInput(0, cur_diffmap)
        cur_diffmap.setParms({"tex0":file_path+'/'+pathCorrect(ary[-1])}) # only last word in a string

    if ary[0]== 'map_d' and len(ary)>1:
        cur_omap = cur_mat.createNode("redshift::TextureSampler")
        cur_splitter = cur_mat.createNode("redshift::RSColorSplitter")
        cur_splitter.setInput(0, cur_omap)
        cur_omap.setParms({"tex0":file_path+'/'+pathCorrect(ary[-1])})
        cur_sh.setInput(47, cur_splitter, 3)

"""
    if ary[0]== 'map_Ks' and len(ary)>1:
        cur_mat.setParms({use_specmap:1})
        cur_mat.setParms({spec_map:file_path+'/'+pathCorrect(ary[-1])})


    if ary[0]== 'map_bump' and len(ary)>1:
        cur_mat.setParms({use_bumpmap:1})
        cur_mat.setParms({bump_map:file_path+'/'+pathCorrect(ary[-1])})
"""

mysop=last.createOutputNode('xform')
mysop.moveToGoodPosition()
mysop.setDisplayFlag(True)
mysop.setRenderFlag(True)
