import os
import maya.cmds as cmds
import maya.mel as mel
import sgtk
from sgtk.util.filesystem import ensure_folder_exists

HookBaseClass = sgtk.get_hook_baseclass()


class MayaSessionFBXPublishPlugin(HookBaseClass):
    """
    Plugin for publishing the side-car FBX file    
    """

    # NOTE: The plugin icon and name are defined by the base file plugin.

    @property
    def description(self):
        return 'Generates (exports) and publishes the FBX side-car file'
    
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
        base_settings = super(MayaSessionFBXPublishPlugin, self).settings or {}

        # settings specific to this class
        fbx_publish_settings = {
            "FBX Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            }
        }

        # update the base settings
        base_settings.update(fbx_publish_settings)
        return base_settings

    @property
    def item_filters(self):
        # name set by the collector
        return ["maya.fbx"]

    def accept(self, settings, item):
        template_name_setting = settings.get("FBX Publish Template")
        
        if not template_name_setting:
            self.logger.debug('Missing "FBX Publish Template" setting.Not accepting the item.')
            return { "accepted": False }
            
        publisher = self.parent
        
        template_name = template_name_setting.value
        publish_template = publisher.get_template_by_name(template_name)
        if not publish_template:
            self.logger.debug('Could not find a template matching the FBX Publish Template setting ({})'.format(template_name))
            return { "accepted": False }
        
        # If a publish template is configured, disable context change. This
        # is a temporary measure until the publisher handles context switching
        # natively.
        item.context_change_allowed = False

        # We've validated the publish template. add it to the item properties
        # for use in subsequent methods
        item.properties["publish_template"] = publish_template

        # Check that fbxmaya is loaded and if not load it.  
        if not cmds.pluginInfo( 'fbxmaya.py', loaded=True, query=True ):
            cmds.loadPlugin('fbxmaya.py')
        
        # If fbxmaya is still not loaded, fail accept
        if not cmds.pluginInfo( 'fbxmaya.py', loaded=True, query=True ):
            self.logger.debug(
                "Item not accepted because fbx export command 'fbxmaya' "
                "is not available. Perhaps the plugin is not enabled?"
            )
            return { "accepted": False }

        return { "accepted": True }

    def validate(self, settings, item):
        path = _session_path()

        # Ensure the session has been saved
        if not path:
            # The session still requires saving. 
            self.logger.error('The Maya session has not been saved.')
            return False

        # Get the normalized path
        path = sgtk.util.ShotgunPath.normalize(path)

        # Get the configured work file template
        work_template = item.parent.properties.get("work_template")
        if not work_template:
            self.logger.error('Missing "Work Template" setting in the collector')
            return False
        
        publish_template = item.properties.get("publish_template")

        # Get the current scene path and extract fields from it using the work
        # template:
        work_fields = work_template.get_fields(path)

        # Ensure the fields work for the publish template
        missing_keys = publish_template.missing_keys(work_fields)
        if missing_keys:
            self.logger.error("Work file '{}' missing keys required for the " \
                              "publish template: {}".format(path, missing_keys))
            return False

        # Create the publish path by applying the fields. store it in the item's
        # properties. This is the path we'll create and then publish in the base
        # publish plugin.
        item.properties["path"] = publish_template.apply_fields(work_fields)

        # use the work file's version number when publishing
        if "version" in work_fields:
            item.properties["publish_version"] = work_fields["version"]

        # run the base class validation
        return super(MayaSessionFBXPublishPlugin, self).validate(settings, item)

    def publish(self, settings, item):
        publisher = self.parent

        # Get the path to create and publish
        publish_path = item.properties["path"]

        # Ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        self.parent.ensure_folder_exists(publish_folder)

        # Execute it:
        try:
            self.parent.log_debug("Exporting Maya scene as FBX: {}".format(publish_path))
            cmds.file(publish_path, force=True, options="v=0;", typ="FBX export", pr=True,  ea=True)
        except Exception, e:
            self.logger.error("Failed to export FBX: {}".format(e))
            return

        # Now that the path has been generated, hand it off to the
        # parent hook
        super(MayaSessionFBXPublishPlugin, self).publish(settings, item)

def _session_path():
    """
    Return the path to the current session
    :return:
    """
    path = cmds.file(query=True, sn=True)

    if isinstance(path, unicode):
        path = path.encode("utf-8")

    return path