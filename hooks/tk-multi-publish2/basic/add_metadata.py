from sg_client import GetUnityEngine

import json
import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

############# METADATA VERSION ################
# In case we need to write backward-compatible code, we store the metadata
# version number along with the metadata
_metadata_version = '1.0'


class UnitySessionAddMetadataPlugin(HookBaseClass):
    """
    Plug-in for adding metadata to the Version entity published by the base class
    """
    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once all the publish
        tasks have completed, and can for example be used to version up files.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        # Call the base hook
        super(UnitySessionAddMetadataPlugin, self).finalize(settings, item)
        
        version = item.properties.get('sg_version_data')
        if not version or version.get('type') != 'Version':
            # Not a version entity, we do not add metadata
            return
        
        # Set the Unity Metadata if possible
        engine = sgtk.platform.current_engine()
        if engine:
            # Make sure the 'sg_unity_metadata' field exists on Version entities
            version_fields = engine.shotgun.schema_field_read('Version')
            if version_fields.get('sg_unity_metadata'):
                UnityEngine = GetUnityEngine()
                data_path = UnityEngine.Application.dataPath
                project_path = os.path.dirname(data_path)
                
                # Get the currently open scene
                scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene()
                scene_path = None
                if scene:
                    scene_path = scene.path
        
                # get the tk-unity engine version            
                engine_version = engine.version
                
                metadata_json = json.dumps(
                    { 'project_path'    : project_path, 
                      'scene_path'      : scene_path,
                      'metadata_version': _metadata_version } )

                # Update the version entity with new metadata                
                engine.shotgun.update('Version', version['id'], { 'sg_unity_metadata' : metadata_json } )
        
