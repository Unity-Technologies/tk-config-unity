import os
import maya.cmds as cmds
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
        
        # The parent hook creates the session item
        super(MayaSessionCollectorExt, self).process_current_session(
            settings,
            parent_item
        )
        
        # The parent (root) item is expected to have 1 child, the maya session 
        # item
        session_item = next(parent_item.children)
        if not session_item:
            self.logger.debug("No session item, cannot add fbx publish item.")
            return
        
        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plug-ins
        publisher = self.parent
        work_template_setting = settings.get("Work Template")
        if work_template_setting:
            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value)

            # store the template on the item for use by publish plug-ins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plug-ins will need to resolve the fields at
            # execution time.
            session_item.properties["work_template"] = work_template
            self.logger.debug("Work template defined for Maya collection.")

        fbx_item = session_item.create_item(
            "maya.fbx",
            "Asset - FBX Export",
            "Asset FBX"
        )

        icon_path = os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "fbx.png"
        )

        fbx_item.set_icon_from_path(icon_path)