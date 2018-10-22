# Copyright (c) 2017 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import glob
import os
import maya.cmds as cmds
import maya.mel as mel
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class MayaSessionCollectorExt(HookBaseClass):
    """
    Collector that operates on the maya session. Should inherit from the basic
    collector hook.
    """

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session open in Maya and parents a subtree of
        items under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance

        """
        
        super(MayaSessionCollectorExt, self).process_current_session(
            settings,
            parent_item
        )
        
        self.logger.info("Augmenenting Maya session")
        
        if parent_item.children:                    
            self.collect_fbx_files(parent_item.children[0], parent_item.children[0].properties["project_root"])
                                         
    def collect_fbx_files(self, parent_item, project_root):
        """
        Creates items for FBX versions
        Looks for a 'project_root' property on the parent item, and if such
        exists, look for FBX files in a 'scenes' subfolder.
        :param parent_item: Parent Item instance
        :param str project_root: The maya project root to search for FBX files
        """

        # ensure the dir exists
        fbx_dir = os.path.join(project_root, "scenes")
        if not os.path.exists(fbx_dir):
            return

        self.logger.info("Processing FBX files: %s" % (fbx_dir,))
        
        # build FBX filename using Maya Session name which is also the 
        # publishing filename e.g. Rock.mb
        candidate_item = os.path.splitext(parent_item.name)[0]
        candidate_filename = candidate_item + ".fbx"
        
        fbx_path = os.path.join(fbx_dir, candidate_filename)
        
        if os.path.exists(fbx_path):
            self.logger.debug("overwriting existing FBX file: %s" % (fbx_path,))
        
        self.logger.info("Exporting Maya scene as FBX: %s" % (fbx_path,))
        cmds.file(fbx_path, force=True, options="v=0;", typ="FBX export", pr=True,  ea=True)
            
        # allow the base class to collect and create the item. it knows how
        # to handle FBX files
        super(MayaSessionCollectorExt, self)._collect_file(
            parent_item,
            fbx_path
        )

