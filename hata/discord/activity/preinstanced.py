__all__ = ('ActivityType',)

from ..bases import Preinstance as P, PreinstancedBase

from .metadata import ActivityMetadataBase, CustomActivityMetadata, RichActivityMetadata


class ActivityType(PreinstancedBase):
    """
    Represents an ``AutoModerationAction``'s type.
    
    Attributes
    ----------
    value : `int`
        The Discord side identifier value of the activity type.
    name : `str`
        The default name of the activity type.
    metadata_type : `type<ActivityMetadataBase>`
        The activity type's respective metadata type.
    
    
    Class Attributes
    ----------------
    INSTANCES : `dict` of (`str`, ``ActivityType``) items
        Stores the predefined activity types. This container is accessed when translating a Discord side
        identifier of a activity type. The identifier value is used as a key to get it's wrapper side
        representation.
    VALUE_TYPE : `type` = `str`
        The activity types' values' type.
    DEFAULT_NAME : `str` = `'Undefined'`
        The default name of the activity types.
    
    Every predefined activity type is also stored as a class attribute:
    
    +-----------------------+-----------------------+-----------+---------------------------------------+
    | Class attribute name  | Name                  | Value     | Metadata type                         |
    +=======================+=======================+===========+=======================================+
    | game                  | game                  | 0         | ``RichActivityMetadata``              |
    +-----------------------+-----------------------+-----------+---------------------------------------+
    | stream                | block stream          | 1         | ``RichActivityMetadata``              |
    +-----------------------+-----------------------+-----------+---------------------------------------+
    | spotify               | spotify               | 2         | ``RichActivityMetadata``              |
    +-----------------------+-----------------------+-----------+---------------------------------------+
    | watching              | watching              | 3         | ``RichActivityMetadata``              |
    +-----------------------+-----------------------+-----------+---------------------------------------+
    | custom                | custom                | 4         | ``CustomActivityMetadata``            |
    +-----------------------+-----------------------+-----------+---------------------------------------+
    | competing             | competing             | 5         | ``RichActivityMetadata``              |
    +-----------------------+-----------------------+-----------+---------------------------------------+
    | unknown               | unknown               | 127       | ``ActivityMetadataBase``              |
    +-----------------------+-----------------------+-----------+---------------------------------------+
    """
    __slots__ = ('metadata_type',)
    
    INSTANCES = {}
    VALUE_TYPE = int

    @classmethod
    def _from_value(cls, value):
        """
        Creates a new activity type with the given value.
        
        Parameters
        ----------
        value : `int`
            The activity type's identifier value.
        
        Returns
        -------
        self : ``ActivityType``
            The created instance.
        """
        self = object.__new__(cls)
        self.name = cls.DEFAULT_NAME
        self.value = value
        self.metadata_type = RichActivityMetadata
        
        return self
    
    
    def __init__(self, value, name, metadata_type):
        """
        Creates an ``ActivityType`` and stores it at the class's `.INSTANCES` class attribute as well.
        
        Parameters
        ----------
        value : `int`
            The Discord side identifier value of the activity type.
        name : `str`
            The default name of the activity type.
        metadata_type : `None`, `type<ActivityMetadataBase>`
            The activity type's respective metadata type.
        """
        self.value = value
        self.name = name
        self.metadata_type = metadata_type
        
        self.INSTANCES[value] = self
    
    # predefined
    game = P(0, 'game', RichActivityMetadata)
    stream = P(1, 'stream message', RichActivityMetadata)
    spotify = P(2, 'spotify', RichActivityMetadata)
    watching = P(3, 'watching', RichActivityMetadata)
    custom = P(4, 'custom', CustomActivityMetadata)
    competing = P(5, 'competing', RichActivityMetadata)
    unknown = P(127, 'unknown', ActivityMetadataBase)
