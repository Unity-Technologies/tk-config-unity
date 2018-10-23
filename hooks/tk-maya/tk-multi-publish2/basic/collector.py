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
    
    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """

        # inherit the settings from the base publish plugin
        base_settings = super(MayaSessionCollectorExt, self).settings or {}

        # settings specific to this class
        maya_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            }
        }

        # update the base settings
        base_settings.update(maya_publish_settings)

        return base_settings


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
            self.collect_fbx_files(parent_item.children[0], parent_item.children[0].properties["project_root"], settings)
                                         
    def collect_fbx_files(self, parent_item, project_root, settings):
        """
        Creates items for FBX versions
        Looks for a 'project_root' property on the parent item, and if such
        exists, look for FBX files in a 'scenes' subfolder.
        :param parent_item: Parent Item instance
        :param str project_root: The maya project root to search for FBX files
        """

        # ensure the dir exists
        fbx_dir = project_root
        if not os.path.exists(fbx_dir):
            return

        self.logger.info("Processing FBX files: %s" % (fbx_dir,))
        
        # build FBX filename using Maya Session name which is also the 
        # publishing filename e.g. Rock.mb
        # This will be the fallback path if no publish or work template exist
        candidate_item = os.path.splitext(parent_item.name)[0]
        candidate_filename = candidate_item + ".fbx"
        fbx_path = os.path.join(fbx_dir, candidate_filename)
        
        # Get the publish and work templates, to use for determining the fbx file name
        publish_template_setting = settings.get("Publish Template")
        publish_template = self.parent.engine.get_template_by_name(
            publish_template_setting.value)
            
        work_template_setting = settings.get("Work Template")
        work_template = self.parent.engine.get_template_by_name(
            work_template_setting.value)
        
        if work_template:
            # get the work template fields from the Maya file
            maya_path = cmds.file(query=True, sn=True)
            if isinstance(maya_path, unicode):
                maya_path = maya_path.encode("utf-8")
            maya_path = sgtk.util.ShotgunPath.normalize(maya_path)
            maya_path = "{0}.fbx".format(os.path.splitext(maya_path)[0])
            
            fields = work_template.get_fields(maya_path)
            if publish_template:
                # get the publish path by applying the work template fields to the publish template
                # TODO: find a more reliable way to do this as the fields might not always match up
                publish_path = publish_template.apply_fields(fields)
                publish_path = os.path.dirname(publish_path)
                
                # get maximum version of fbx that has been published
                # if none just use the Maya filename without the version
                max_version = 0
                for file in os.listdir(publish_path):
                    if not file.endswith(".fbx"):
                        continue
                    file_path = os.path.join(publish_path, file)
                    publish_fields = publish_template.get_fields(file_path)
                    version = publish_fields.get("version")
                    if version and version > max_version:
                        max_version = version
                
                fields["version"] = max_version + 1
                
                # set the path
                fbx_path = work_template.apply_fields(fields)
        
        if os.path.exists(fbx_path):
            self.logger.debug("overwriting existing FBX file: %s" % (fbx_path,))
        
        self.logger.info("Exporting Maya scene as FBX: %s" % (fbx_path,))
        cmds.file(fbx_path, force=True, options="v=0;", typ="FBX export", pr=True,  ea=True)
            
        # allow the base class to collect and create the item. it knows how
        # to handle FBX files
        item = super(MayaSessionCollectorExt, self)._collect_file(
            parent_item,
            fbx_path
        )
        
        if publish_template:
            item.properties["publish_template"] = publish_template
            
        if work_template:
            item.properties["work_template"] = work_template

