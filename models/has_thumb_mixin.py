from cairosvg import svg2png
from colorthief import ColorThief
from flask import current_app as app
from PIL import Image
import requests
import tempfile

from utils.human_ids import humanize
from utils.object_storage import delete_public_object,\
                                 get_public_object_date,\
                                 store_public_object
from utils.string_processing import inflect_engine

db = app.db


class HasThumbMixin(object):
    thumbCount = db.Column(db.Integer(), nullable=False, default=0)
    firstThumbDominantColor = db.Column(db.Binary(3), nullable=True)

    def delete_thumb(self, index):
        delete_public_object("thumbs", self.thumb_storage_id(index))

    def thumb_date(self, index):
        return get_public_object_date("thumbs", self.thumb_storage_id(index))

    def thumb_storage_id(self, index):
        return inflect_engine.plural(self.__class__.__name__.lower()) + "/"\
                                     + humanize(self.id)\
                                     + (('_' + str(index)) if index > 0 else '')

    def save_thumb(self, thumb, index, image_type = None):
        if isinstance(thumb, str):
            if not thumb[0:4] == 'http':
                raise ValueError('Invalid thumb URL for object '
                                 + str(self)
                                 + ' : ' + thumb)
            thumb_response = requests.get(thumb)
            content_type = thumb_response.headers['Content-type']
            if thumb_response.status_code == 200 and\
               content_type.split('/')[0] == 'image':
                thumb = thumb_response.content
                image_type = content_type.split('/')[1]
            else:
                raise ValueError('Error downloading thumb for object '
                                 + str(self)
                                 + ' status_code: ' + str(thumb_response.status_code) + ', '
                                 + ' content-type: ' + content_type)
        with tempfile.TemporaryFile() as tf:
            tf.write(thumb)
            if image_type is None:
                img = Image.open(tf)
                image_type = img.format.lower()
            if image_type == 'svg':
                color_thief = ColorThief(svg2png(bytestring=thumb))
            else:
                color_thief = ColorThief(tf)
            self.firstThumbDominantColor = bytearray(color_thief.get_color(quality=1))
        store_public_object("thumbs",
                            self.thumb_storage_id(index),
                            thumb,
                            "image/"+image_type)
        self.thumbCount = max(index+1, self.thumbCount or 0)


app.model.HasThumbMixin = HasThumbMixin
