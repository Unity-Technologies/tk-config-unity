# Shotgun
import sgtk

# Unity
import unity_connection

# misc
import json
import os
import pprint

HookBaseClass = sgtk.get_hook_baseclass()

class UnityApplyMetadata(HookBaseClass):
    def on_post_init(self, engine):
        """
        This method is invoked when tk-unity has successfully initialized
        
        In this specific hook we parse the sg_unity_metadata that is defined for 
        the entity related to the context from which we just bootstrapped and 
        we try to apply it (open scene) 
        """
        # Call the base class
        super(UnityApplyMetadata, self).on_post_init(engine)

        UnityEngine = unity_connection.get_module('UnityEngine')
        UnityEditor = unity_connection.get_module('UnityEditor')

        # get meta data from the environment variable
        unity_metadata_json = os.environ.get('SHOTGUN_UNITY_METADATA')
        if not unity_metadata_json:
            return
    
        unity_metadata = None
        try:
            unity_metadata = json.loads(unity_metadata_json)
        except Exception, e:
            engine.logger.warning('Exception while parsing the sg_unity_metadata field: {}. The JSON data is probably invalid and will be ignored'.format(e))
            return
        
        if not unity_metadata:
            return
        
        # Make sure the right project is currently loaded
        loaded_project = UnityEngine.Application.dataPath

        # Remove /Assets
        loaded_project = os.path.split(loaded_project)[0]
        loaded_project = os.path.normpath(loaded_project)

        metadata_project = unity_metadata.get('project_path')
        metadata_project = os.path.normpath(metadata_project)
        
        if metadata_project != loaded_project:
            engine.logger.warning('Not applying Shotgun metadata as it does not relate to the currently loaded project. Metadata = "{}")'.format(pprint.pformat(metadata_project)))
            
            # TODO: could we call UnityEditor.EditorApplication.OpenProject?
            #       What would be the effect on the bootstrap, domain reload, etc.?
            return
        
        # Find the scene to open
        scene_path = unity_metadata.get('scene_path')
        if not scene_path:
            return
    
        # open the correct scene in Unity
        UnityEditor.SceneManagement.EditorSceneManager.OpenScene(scene_path)
        