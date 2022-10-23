__all__ = ('ComponentMetadataMentionableSelect', )

from .select_base import ComponentMetadataSelectBase


class ComponentMetadataMentionableSelect(ComponentMetadataSelectBase):
    """
    mentionable (User and role) select component metadata.
    
    Attributes
    ----------
    custom_id : `None`, `str`
        Custom identifier to detect which component was used by the user.
    
    enabled : `bool`
        Whether the component is enabled.
    
    max_values : `int
        The maximal amount of options to select.
    
    min_values : `int`
        The minimal amount of options to select.
    
    placeholder : `None`, `str`
        Placeholder text of the select.
    """
    __slots__ = ()