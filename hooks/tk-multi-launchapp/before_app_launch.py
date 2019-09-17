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
        The execute function of the hook will be called prior to starting the required application   

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
            context = multi_launchapp.context
            entity = context.entity
            
            if not entity:
                return

            sgtk = context.sgtk
            sg = sgtk.shotgun

            # Retrieve the metadata for the context entity. The Unity project
            # of interest might be in there
            metadata = unity_metadata.get_metadata_from_entity(entity, sg)
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

            # Save the entity we launched from in case we switch the context
            # entity below
            os.environ['SHOTGUN_LAUNCH_ENTITY_TYPE'] = entity['type']
            os.environ['SHOTGUN_LAUNCH_ENTITY_ID'] = str(entity['id'])

            # Toolkit does not really support launching from a Version or a Note
            # entity. We need to switch the context back to the supported entity
            # (or task) for which the Version/Note was created. This is similar 
            # to what toolkit does when launching from a published file entity.
            entity_type = entity['type']
            if entity_type in ['Note', 'Version']:
                version = entity if entity_type == 'Version' else unity_metadata.get_version_from_note(entity,sg)

                if version:
                    # Fetch the Link ('entity') and Task ('sg_task') fields 
                    found_version = sg.find_one(version['type'], [['id', 'is', version['id']]], ['entity', 'sg_task'])
                    linked_entity = found_version.get('entity')

                    if linked_entity:
                        linked_task = found_version.get('sg_task')
                        if linked_task:
                            # Work in the context of the task
                            linked_entity = linked_task

                        os.environ['SHOTGUN_ENTITY_TYPE'] = linked_entity['type']
                        os.environ['SHOTGUN_ENTITY_ID']   = str(linked_entity['id'])
                else:
                    log.warning('Could not find a Version entity linked to the Note ({}). Some toolkit features might not be available.'.format(entity))
                
