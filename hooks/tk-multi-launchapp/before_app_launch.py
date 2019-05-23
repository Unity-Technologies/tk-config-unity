"""
Before App Launch Hook

This hook is executed prior to application launch and is useful if you need
to set environment variables or run scripts as part of the app initialization.
"""

import tank
import sgtk

import json
import os

log = sgtk.LogManager.get_logger(__name__)

class BeforeAppLaunch(tank.Hook):
    """
    Hook to set up the system prior to app launch.
    """
    def execute(self, app_path, app_args, version, engine_name, **kwargs):
        """
        The execute functon of the hook will be called prior to starting the required application   

        :param app_path: (str) The path of the application executable
        :param app_args: (str) Any arguments the application may require
        :param version: (str) version of the application being run if set in the
            "versions" settings of the Launcher instance, otherwise None
        :param engine_name (str) The name of the engine associated with the
            software about to be launched.

        """
        if engine_name == 'tk-unity':
            """
            Try to retrieve the Unity project path from SG metadata
            """
            multi_launchapp = self.parent
            current_entity = multi_launchapp.context.entity
            
            if not current_entity:
                return
            
            metadata_json = self._get_metadata_from_entity(current_entity)
            metadata = None
            try:
                metadata = json.loads(metadata_json)
            except:
                log.warning('Ignoring invalid "sg_unity_metadata" ({}) relating to entity {}'.format(metadata, current_entity))
                
            if metadata:
                project_path = metadata.get('project_path')
                if project_path:
                    # Validate that the project exists on disk
                    if os.path.exists(project_path):
                        # Save our extra args in an environment variable as 
                        # modifying app_args will not work (it is passed by copy)
                        os.environ['SHOTGUN_EXTRA_ARGS'] = ' -projectPath "{}"'.format(project_path)
                        
                        # Keep the metadata handy for Unity
                        os.environ['SHOTGUN_UNITY_METADATA'] = metadata_json
                    else:
                        log.warning('Ignoring invalid project path associated with the entity: "{}"'.format(project_path))
        
    def _get_metadata_from_entity(self, entity):
        """
        From a given entity, find the best metadata dictionary to use
        
        If there is metadata defined directly on the entity, then return it
        Otherwise traverse the dependencies in a minimal way
        
        Metadata is stored in a string field named "sg_unity_metadata"
        
        Returne None if no metadata was found
        """
        multi_launchapp = self.parent
        sg = multi_launchapp.context.sgtk.shotgun

        metadata = None
        fields = sg.schema_field_read(entity['type'])

        if fields.get('sg_unity_metadata'):
            # The field exists on the current entity. Get its value
            found_entity = sg.find_one(entity['type'], [['id', 'is', entity['id']]], ['sg_unity_metadata'])
            metadata = found_entity['sg_unity_metadata'] 

        if metadata:
            return metadata

        # We did not find metadata on the entity. Try to look at its 
        # dependencies
        if entity['type'] == 'Note':
            # If the note is linked to a Version entity, try to get the metadata 
            # from that Version entity
            found_entity = sg.find_one(entity['type'], [['id', 'is', entity['id']]], ['note_links'])
            note_links = found_entity['note_links']
            for link in note_links:
                if link['type'] == 'Version':
                    metadata = self._get_metadata_from_entity(link)
                    if metadata:
                        # Return first metadata we find
                        return metadata
        
        return metadata
