# Shotgun
import sgtk
from sg_client import GetUnityEditor

# misc
import json
import os
import pprint
import sys

# Fix-up sys.path so we can access our utils
utils_path = os.path.split(__file__)[0]
utils_path = os.path.join(utils_path, os.pardir, os.pardir, 'utils')
utils_path = os.path.normpath(utils_path)
if utils_path not in sys.path:
    sys.path.append(utils_path)

HookBaseClass = sgtk.get_hook_baseclass()

class UnityApplyMetadata(HookBaseClass):
    def on_post_init(self):
        """
        This method is invoked when tk-unity has successfully initialized
        
        In this specific hook we parse the sg_unity_metadata that is defined for 
        the entity related to the context from which we just bootstrapped and 
        we try to apply it (open scene) 
        """
        import unity_metadata
        engine = self.parent
        
        # Call the base class
        super(UnityApplyMetadata, self).on_post_init()

        # Get metadata from the entity we launched from
        launch_entity_type = os.environ.get('SHOTGUN_LAUNCH_ENTITY_TYPE')
        launch_entity_id = os.environ.get('SHOTGUN_LAUNCH_ENTITY_ID')
        if launch_entity_id:
            launch_entity_id = int(launch_entity_id)

        launch_entity = { 'type':launch_entity_type, 'id':launch_entity_id }
        metadata = unity_metadata.get_metadata_from_entity(launch_entity, engine.sgtk.shotgun)
        if not metadata:
            return

        # Make sure the right project is currently loaded
        if not unity_metadata.relates_to_current_project(metadata):
            self.logger.warning('Not applying Shotgun metadata as it does not relate to the currently loaded project. Metadata = "{}")'.format(pprint.pformat(metadata)))
            
            # TODO: could we call GetUnityEditor().EditorApplication.OpenProject?
            #       What would be the effect on the bootstrap, domain reload, etc.?
            return
        
        # Find the scene to open
        if not unity_metadata.relates_to_existing_scene(metadata):
            return
        
        # open the correct scene in Unity
        GetUnityEditor().SceneManagement.EditorSceneManager.OpenScene(metadata.get('scene_path'))
        