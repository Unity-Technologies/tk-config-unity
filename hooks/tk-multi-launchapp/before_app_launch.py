"""
Before App Launch Hook

This hook is executed prior to application launch and is useful if you need
to set environment variables or run scripts as part of the app initialization.
"""

import tank
import sgtk

import os
import sys

# Fix-up sys.path so we can access our utils
utils_path = os.path.split(__file__)[0]
utils_path = os.path.join(utils_path, os.pardir, 'utils')
utils_path = os.path.normpath(utils_path)
if utils_path not in sys.path:
    sys.path.append(utils_path)

import unity_metadata

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
            
            sg = multi_launchapp.context.sgtk.shotgun
            metadata = unity_metadata.get_metadata_from_entity(current_entity, sg)
            if metadata:
                project_path = metadata.get('project_path')
                if project_path:
                    # Validate that the project exists on disk
                    if os.path.exists(project_path):
                        # Save our extra args in an environment variable as 
                        # modifying app_args will not work (it is passed by copy)
                        os.environ['SHOTGUN_EXTRA_ARGS'] = ' -projectPath "{}"'.format(project_path)
                    else:
                        log.warning('Ignoring invalid project path associated with the entity: "{}"'.format(project_path))
        
