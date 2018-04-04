from flask import current_app
from pathlib import Path
import os

from utils.human_ids import humanize
from utils.object_storage import store_public_object
from utils.string_processing import inflect_engine

default_mimes_by_folder = {
    "spreadsheets": "application/CSV",
    "thumbs": "image/jpeg",
    "zips": "application/zip"
}


def set_from_mock(folder, obj, thumb_id, mime_type=None):
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    collection_name = inflect_engine.plural(obj.__class__.__name__.lower())
    thumb_path = dir_path / '..' / 'mock'\
                 / folder / collection_name\
                 / str(thumb_id)
    with open(thumb_path, mode='rb') as file:
        contents = file.read()
    if mime_type is None:
        mime_type = default_mimes_by_folder[folder]
    if folder == "thumbs":
        obj.save_thumb(contents, 0, mime_type.split('/')[1])
    else:
        store_public_object(folder,
                            collection_name + '/' + humanize(obj.id),
                            contents,
                            mime_type)
    current_app.model.PcObject.check_and_save(obj)
