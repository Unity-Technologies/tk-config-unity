import sgtk

import json
import os

log = sgtk.LogManager.get_logger(__name__)

def _get_frame_from_note(note_entity, sg):
    #   'attachments': [{'type': 'Attachment', 'id': 1668, 'name': 'annot_version_7199.107.png'}], 
    entity = sg.find_one(note_entity["type"], [["id", "is", note_entity["id"]]], ["attachments"])
    
    attachments = entity.get("attachments", None)
    if not attachments:
        return None
        
    name = attachments[0]["name"]
    tokens = name.split(".")
    if len(tokens) < 3:
        return None
    return tokens[1] # frame number

def get_metadata_from_entity(entity, sg):
    """
    From a given entity, find the best metadata dictionary to use
    
    If there is metadata defined directly on the entity, then return it
    Otherwise traverse the dependencies in a minimal way
    
    Metadata is stored as a json dictionary, in a string field named 
    "sg_unity_metadata"
    
    Returns None if no metadata was found
    """
    if not entity or not entity.get('type') or not entity.get('id') or not sg:
        return None
    
    metadata_json = None
    metadata = {}
    fields = sg.schema_field_read(entity['type'])

    if fields.get('sg_unity_metadata'):
        # The field exists on the current entity. Get its value
        found_entity = sg.find_one(entity['type'], [['id', 'is', entity['id']]], ['sg_unity_metadata'])
        metadata_json = found_entity['sg_unity_metadata'] 

    if not metadata_json:
        # We did not find metadata on the entity. Try to look at its 
        # dependencies
        if entity['type'] == 'Note':
            # If the note is linked to a Version entity, try to get the metadata 
            # from that Version entity
            version = get_version_from_note(entity, sg)
            if not version:
                return None
            
            metadata = get_metadata_from_entity(version, sg)
                    
            # Add the note frame number to the metadata
            frame_number = _get_frame_from_note(entity, sg)
            if frame_number:
                metadata['frame_number'] = frame_number
            
            return metadata
            
    if metadata_json:
        try:
            metadata = json.loads(metadata_json)
        except:
            pass
            
    return metadata

def relates_to_current_project(metadata):
    from sg_client import GetUnityEngine

    # Make sure the right project is currently loaded
    loaded_project = GetUnityEngine().Application.dataPath

    # Remove /Assets
    loaded_project = os.path.split(loaded_project)[0]
    loaded_project = os.path.normpath(loaded_project)

    metadata_project = metadata.get('project_path')
    metadata_project = os.path.normpath(metadata_project)
    
    return metadata_project == loaded_project

def relates_to_existing_scene(metadata):
    from sg_client import GetUnityEditor
    
    metadata_scene_path = metadata.get('scene_path')
    if not metadata_scene_path:
        return False
    
    UnityEditor = GetUnityEditor()
    
    scene_guids = UnityEditor.AssetDatabase.FindAssets('t:scene')
    for guid in scene_guids:
        scene_path = UnityEditor.AssetDatabase.GUIDToAssetPath(guid)
        if scene_path == metadata_scene_path:
            return True

    return False

def get_version_from_note(note, sg):
    """
    Returns the Version entity associated with the passed Note entity
    """
    # Retrieve the note links
    found_entity = sg.find_one(note['type'], [['id', 'is', note['id']]], ['note_links'])
    note_links = found_entity['note_links']
    for link in note_links:
        if link['type'] == 'Version':
            return link
        
    return None
    