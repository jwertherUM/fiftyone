"""
Dataset sample fields.

| Copyright 2017-2020, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
# pragma pylint: disable=redefined-builtin
# pragma pylint: disable=unused-wildcard-import
# pragma pylint: disable=wildcard-import
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import *

# pragma pylint: enable=redefined-builtin
# pragma pylint: enable=unused-wildcard-import
# pragma pylint: enable=wildcard-import

from bson.binary import Binary
import mongoengine.fields
import numpy as np

import eta.core.image as etai
import eta.core.utils as etau

import fiftyone.core.utils as fou


class Field(mongoengine.fields.BaseField):
    """Base class for :class:`fiftyone.core.sample.Sample` fields."""

    def __str__(self):
        return etau.get_class_name(self)


class BooleanField(mongoengine.BooleanField, Field):
    """A boolean field."""

    pass


class IntField(mongoengine.IntField, Field):
    """A 32 bit integer field."""

    pass


class FloatField(mongoengine.FloatField, Field):
    """A floating point number field."""

    def validate(self, value):
        try:
            value = float(value)
        except OverflowError:
            self.error("The value is too large to be converted to float")
        except (TypeError, ValueError):
            self.error("%s could not be converted to float" % value)

        if self.min_value is not None and value < self.min_value:
            self.error("Float value is too small")

        if self.max_value is not None and value > self.max_value:
            self.error("Float value is too large")


class StringField(mongoengine.StringField, Field):
    """A unicode string field."""

    pass


class ListField(mongoengine.ListField, Field):
    """A list field that wraps a standard :class:`Field`, allowing multiple
    instances of the field to be stored as a list in the database.

    If this field is not set, its default value is ``[]``.

    Args:
        field (None): an optional :class:`Field` instance describing the
            type of the list elements
    """

    def __init__(self, field=None, **kwargs):
        if field is not None:
            if not isinstance(field, Field):
                raise ValueError(
                    "Invalid field type '%s'; must be a subclass of %s"
                    % (type(field), Field)
                )

        super().__init__(field=field, **kwargs)

    def __str__(self):
        if self.field is not None:
            return "%s(%s)" % (
                etau.get_class_name(self),
                etau.get_class_name(self.field),
            )

        return etau.get_class_name(self)


class DictField(mongoengine.DictField, Field):
    """A dictionary field that wraps a standard Python dictionary.

    If this field is not set, its default value is ``{}``.

    Args:
        field (None): an optional :class:`Field` instance describing the type
            of the values in the dict
    """

    def __init__(self, field=None, **kwargs):
        if field is not None:
            if not isinstance(field, Field):
                raise ValueError(
                    "Invalid field type '%s'; must be a subclass of %s"
                    % (type(field), Field)
                )

        super().__init__(field=field, **kwargs)

    def __str__(self):
        if self.field is not None:
            return "%s(%s)" % (
                etau.get_class_name(self),
                etau.get_class_name(self.field),
            )

        return etau.get_class_name(self)


class VectorField(Field):
    """A one-dimensional array field.

    :class:`VectorField` instances accept lists, tuples, and numpy array
    values. The underlying data is stored as a list in the database and always
    retrieved as a numpy array.
    """

    def to_mongo(self, value):
        if value is None:
            return None

        return np.asarray(value).tolist()

    def to_python(self, value):
        if value is None or isinstance(value, np.ndarray):
            return value

        return np.asarray(value)

    def validate(self, value):
        if isinstance(value, np.ndarray):
            if value.ndim > 1:
                self.error("Only 1D arrays may be used in a vector field")
        elif not isinstance(value, (list, tuple)):
            self.error(
                "Only numpy arrays, lists, and tuples may be used in a "
                "vector field"
            )


class ArrayField(mongoengine.fields.BinaryField, Field):
    """An n-dimensional array field.

    :class:`ArrayField` instances accept numpy array values. The underlying
    data is serialized and stored in the database as zlib-compressed bytes
    generated by ``numpy.save`` and always retrieved as a numpy array.
    """

    def to_mongo(self, value):
        if value is None:
            return None

        bytes = fou.serialize_numpy_array(value)
        return super().to_mongo(bytes)

    def to_python(self, value):
        if value is None or isinstance(value, np.ndarray):
            return value

        return fou.deserialize_numpy_array(value)

    def validate(self, value):
        if not isinstance(value, (np.ndarray, Binary)):
            self.error("Only numpy arrays may be used in an array field")


class ImageLabelsField(Field):
    """A field that stores an ``eta.core.image.ImageLabels`` instance.

    :class:`ImageLabelsField` instances accept ``eta.core.image.ImageLabels``
    instances or serialized dict representations of them. The underlying data
    is stored as a serialized dictionary in the dataset and always retrieved as
    an ``eta.core.image.ImageLabels`` instance.
    """

    def to_mongo(self, value):
        if value is None:
            return None

        return value.serialize()

    def to_python(self, value):
        if value is None or isinstance(value, etai.ImageLabels):
            return value

        return etai.ImageLabels.from_dict(value)

    def validate(self, value):
        if not isinstance(value, (dict, etai.ImageLabels)):
            self.error(
                "Only dicts and `eta.core.image.ImageLabels` instances may be "
                "used in an ImageLabels field"
            )


class EmbeddedDocumentField(mongoengine.EmbeddedDocumentField, Field):
    """A field that stores instances of a given type of
    :class:`fiftyone.core.odm.BaseEmbeddedDocument` object.

    Args:
        document_type: the :class:`fiftyone.core.odm.BaseEmbeddedDocument` type
            stored in this field
    """

    def __init__(self, document_type, **kwargs):
        #
        # @todo resolve circular import errors in `fiftyone.core.odm.sample`
        # so that this validation can occur here
        #
        # import fiftyone.core.odm as foo
        #
        # if not issubclass(document_type, foo.BaseEmbeddedDocument):
        #     raise ValueError(
        #         "Invalid document type %s; must be a subclass of %s"
        #         % (document_type, foo.BaseEmbeddedDocument)
        #     )
        #

        super().__init__(document_type, **kwargs)

    def __str__(self):
        return "%s(%s)" % (
            etau.get_class_name(self),
            etau.get_class_name(self.document_type),
        )
