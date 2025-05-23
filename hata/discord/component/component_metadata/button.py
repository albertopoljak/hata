__all__ = ('ComponentMetadataButton', )

from scarletio import copy_docs

from ...utils import url_cutter

from ..shared_helpers import create_auto_custom_id

from .base import ComponentMetadataBase
from .constants import BUTTON_STYLE_DEFAULT
from .fields import (
    parse_button_style, parse_custom_id, parse_emoji, parse_enabled, parse_label, parse_sku_id, parse_url,
    put_button_style, put_custom_id, put_emoji, put_enabled, put_label, put_sku_id, put_url, validate_button_style,
    validate_custom_id, validate_emoji, validate_enabled, validate_label, validate_sku_id, validate_url
)
from .preinstanced import ButtonStyle


class ComponentMetadataButton(ComponentMetadataBase):
    """
    Button component metadata.
    
    Attributes
    ----------
    button_style : ``ButtonStyle``
        The button's style.
    
    custom_id : `None | str`
        Custom identifier to detect which button was clicked by the user.
        
        > Mutually exclusive with the `sku_id` and `url` fields.
    
    emoji : ``None | Emoji``
        Emoji of the button if applicable.
    
    enabled : `bool`
        Whether the component is enabled.
    
    label : `None | str`
        Label of the component.
    
    sku_id : `int`
        Purchasable stock keeping unit identifier.
        
        > Mutually exclusive with the `custom_id` and `url` fields.
    
    url : `None | str`
        Url to redirect to when clicking on the button.
        
        > Mutually exclusive with the `custom_id` and `sku_id` fields.
    """
    __slots__ = ('button_style', 'custom_id', 'emoji', 'enabled', 'label', 'sku_id', 'url',)
    
    
    def __new__(
        cls,
        *,
        button_style = ...,
        custom_id = ...,
        emoji = ...,
        enabled = ...,
        label = ...,
        sku_id = ...,
        url = ...,
    ):
        """
        Creates a new button component metadata.
        
        Parameters
        ----------
        button_style : ``int | ButtonStyle``, Optional (Keyword only)
            The button's style.
        
        custom_id : `None | str`, Optional (Keyword only)
            Custom identifier to detect which button was clicked by the user.
            
            > Mutually exclusive with the `sku_id` and `url` fields.
        
        emoji : ``None | Emoji``, Optional (Keyword only)
            Emoji of the button if applicable.
        
        enabled : `bool`, Optional (Keyword only)
            Whether the component is enabled.
        
        label : `None | str`, Optional (Keyword only)
            Label of the component.
        
        sku_id : ``int | SKU``, Optional (Keyword only)
            Purchasable stock keeping unit identifier.
            
            > Mutually exclusive with the `custom_id` and `url` fields.
        
        url : `None | str`, Optional (Keyword only)
            Url to redirect to when clicking on the button.
            
            > Mutually exclusive with the `custom_id` and `sku_id` fields.
        
        Raises
        ------
        TypeError
            - If a parameter's type is incorrect.
        ValueError
            - If a parameter's value is incorrect.
        """
        # button_style
        if button_style is ...:
            button_style = BUTTON_STYLE_DEFAULT
        else:
            button_style = validate_button_style(button_style)
        
        # custom_id
        if custom_id is ...:
            custom_id = None
        else:
            custom_id = validate_custom_id(custom_id)
        
        # emoji
        if emoji is ...:
            emoji = None
        else:
            emoji = validate_emoji(emoji)
        
        # enabled
        if enabled is ...:
            enabled = True
        else:
            enabled = validate_enabled(enabled)
        
        # label
        if label is ...:
            label = None
        else:
            label = validate_label(label)
        
        # sku
        if sku_id is ...:
            sku_id = 0
        else:
            sku_id = validate_sku_id(sku_id)
        
        # url
        if url is ...:
            url = None
        else:
            url = validate_url(url)
        
        # Postprocess
        if url is not None:
            button_style = ButtonStyle.link
        
        elif sku_id:
            button_style = ButtonStyle.subscription
        
        else:
            if custom_id is None:
                custom_id = create_auto_custom_id()
            
            if (
                (button_style is ButtonStyle.none) or
                (button_style is ButtonStyle.link) or
                (button_style is ButtonStyle.subscription)
            ):
                button_style = BUTTON_STYLE_DEFAULT
        
        # Construct
        self = object.__new__(cls)
        self.button_style = button_style
        self.custom_id = custom_id
        self.emoji = emoji
        self.enabled = enabled
        self.label = label
        self.sku_id = sku_id
        self.url = url
        
        return self
    
    
    @classmethod
    @copy_docs(ComponentMetadataBase.from_keyword_parameters)
    def from_keyword_parameters(cls, keyword_parameters):
        return cls(
            button_style = keyword_parameters.pop('button_style', ...),
            custom_id = keyword_parameters.pop('custom_id', ...),
            emoji = keyword_parameters.pop('emoji', ...),
            enabled = keyword_parameters.pop('enabled', ...),
            label = keyword_parameters.pop('label', ...),
            sku_id = keyword_parameters.pop('sku_id', ...),
            url = keyword_parameters.pop('url', ...),
        )
    
    
    @copy_docs(ComponentMetadataBase.__repr__)
    def __repr__(self):
        repr_parts = ['<', type(self).__name__]
        
        # Descriptive fields : button_style
        
        # button_style
        button_style = self.button_style
        repr_parts.append(' button_style = ')
        repr_parts.append(button_style.name)
        repr_parts.append(' ~ ')
        repr_parts.append(repr(button_style.value))
        
        # System fields : custom_id
        
        # custom_id
        custom_id = self.custom_id
        if (custom_id is not None):
            repr_parts.append(', custom_id = ')
            repr_parts.append(repr(custom_id))
        
        # Text fields : emoji & label
        
        # emoji
        emoji = self.emoji
        if (emoji is not None):
            repr_parts.append(', emoji = ')
            repr_parts.append(repr(emoji))
        
        # label
        label = self.label
        if (label is not None):
            repr_parts.append(', label = ')
            repr_parts.append(repr(label))
        
        
        # Optional descriptive fields: url & enabled
        
        # sku_id
        sku_id = self.sku_id
        if sku_id:
            repr_parts.append(', sku_id = ')
            repr_parts.append(repr(sku_id))
        
        # url
        url = self.url
        if (url is not None):
            repr_parts.append(', url = ')
            repr_parts.append(url_cutter(url))
        
        # enabled
        enabled = self.enabled
        if (not enabled):
            repr_parts.append(', enabled = ')
            repr_parts.append(repr(enabled))
        
        repr_parts.append('>')
        return ''.join(repr_parts)
    
    
    @copy_docs(ComponentMetadataBase.__hash__)
    def __hash__(self):
        hash_value = 0
        
        # button_style
        hash_value ^= self.button_style.value
        
        # custom_id
        custom_id = self.custom_id
        if (custom_id is not None):
            hash_value ^= hash(custom_id)
        
        # emoji
        emoji = self.emoji
        if (emoji is not None):
            hash_value ^= emoji.id
        
        # enabled
        if self.enabled:
            hash_value ^= 1 << 8
        
        # label
        label = self.label
        if (label is not None):
            hash_value ^= hash(label)
        
        # sku_id
        hash_value ^= self.sku_id
        
        # url
        url = self.url
        if (url is not None):
            hash_value ^= hash(url)
        
        return hash_value
    
    
    @copy_docs(ComponentMetadataBase._is_equal_same_type)
    def _is_equal_same_type(self, other):
        # button_style
        if self.button_style is not other.button_style:
            return False
        
        # custom_id
        if self.custom_id != other.custom_id:
            return False
        
        # emoji
        if self.emoji is not other.emoji:
            return False
        
        # enabled
        if self.enabled != other.enabled:
            return False
        
        # label
        if self.label != other.label:
            return False
        
        # sku_id
        if self.sku_id != other.sku_id:
            return False
        
        # url
        if self.url != other.url:
            return False
        
        return True
    
    
    @classmethod
    @copy_docs(ComponentMetadataBase.from_data)
    def from_data(cls, data):
        self = object.__new__(cls)
        
        self.button_style = parse_button_style(data)
        self.custom_id = parse_custom_id(data)
        self.emoji = parse_emoji(data)
        self.enabled = parse_enabled(data)
        self.label = parse_label(data)
        self.sku_id = parse_sku_id(data)
        self.url = parse_url(data)
        
        return self
    
    
    @copy_docs(ComponentMetadataBase.to_data)
    def to_data(self, *, defaults = False, include_internals = False):
        data = {}
        
        put_button_style(self.button_style, data, defaults)
        put_custom_id(self.custom_id, data, defaults)
        put_emoji(self.emoji, data, defaults)
        put_enabled(self.enabled, data, defaults)
        put_label(self.label, data, defaults)
        put_sku_id(self.sku_id, data, defaults)
        put_url(self.url, data, defaults)
        
        return data
    
    
    @copy_docs(ComponentMetadataBase.clean_copy)
    def clean_copy(self, guild = None):
        new = object.__new__(type(self))
        
        new.button_style = self.button_style
        new.custom_id = self.custom_id
        new.emoji = self.emoji
        new.enabled = self.enabled
        new.label = self.label
        new.sku_id = self.sku_id
        new.url = self.url
        
        return new
    
    
    @copy_docs(ComponentMetadataBase.copy)
    def copy(self):
        new = object.__new__(type(self))
        
        new.button_style = self.button_style
        new.custom_id = self.custom_id
        new.emoji = self.emoji
        new.enabled = self.enabled
        new.label = self.label
        new.sku_id = self.sku_id
        new.url = self.url
        
        return new
    
    
    def copy_with(
        self,
        *,
        button_style = ...,
        custom_id = ...,
        emoji = ...,
        enabled = ...,
        label = ...,
        sku_id = ...,
        url = ...,
    ):
        """
        Copies the button component metadata with the given fields.
        
        Parameters
        ----------
        button_style : ``int | ButtonStyle``, Optional (Keyword only)
            The button's style.
        
        custom_id : `None | str`, Optional (Keyword only)
            Custom identifier to detect which button was clicked by the user.
            
            > Mutually exclusive with the `sku_id` and `url`fields.
        
        emoji : ``None | Emoji``, Optional (Keyword only)
            Emoji of the button if applicable.
        
        enabled : `bool`, Optional (Keyword only)
            Whether the component is enabled.
        
        label : `None | str`, Optional (Keyword only)
            Label of the component.
        
        sku_id : ``int | SKU``, Optional (Keyword only)
            Purchasable stock keeping unit identifier.
            
            > Mutually exclusive with the `custom_id` and `url` fields.
        
        url : `None | str`, Optional (Keyword only)
            Url to redirect to when clicking on the button.
            
            > Mutually exclusive with the `custom_id` and `sku_id` fields.
        
        Returns
        -------
        new : `instance<type<self>>`
        
        Raises
        ------
        TypeError
            - If a parameter's type is incorrect.
        ValueError
            - If a parameter's value is incorrect.
        """
        # button_style
        if button_style is ...:
            button_style = self.button_style
        else:
            button_style = validate_button_style(button_style)
        
        # custom_id
        if custom_id is ...:
            custom_id = self.custom_id
        else:
            custom_id = validate_custom_id(custom_id)
        
        # emoji
        if emoji is ...:
            emoji = self.emoji
        else:
            emoji = validate_emoji(emoji)
        
        # enabled
        if enabled is ...:
            enabled = self.enabled
        else:
            enabled = validate_enabled(enabled)
        
        # label
        if label is ...:
            label = self.label
        else:
            label = validate_label(label)
        
        # sku_id
        if sku_id is ...:
            sku_id = self.sku_id
        else:
            sku_id = validate_sku_id(sku_id)
        
        # url
        if url is ...:
            url = self.url
        else:
            url = validate_url(url)
        
        # Postprocess
        if url is not None:
            button_style = ButtonStyle.link
        
        elif sku_id:
            button_style = ButtonStyle.subscription
        
        else:
            if custom_id is None:
                custom_id = create_auto_custom_id()
            
            if (
                (button_style is ButtonStyle.none) or
                (button_style is ButtonStyle.link) or
                (button_style is ButtonStyle.subscription)
            ):
                button_style = BUTTON_STYLE_DEFAULT
        
        # Construct
        new = object.__new__(type(self))
        new.button_style = button_style
        new.custom_id = custom_id
        new.emoji = emoji
        new.enabled = enabled
        new.label = label
        new.sku_id = sku_id
        new.url = url
        
        return new
    
    
    @copy_docs(ComponentMetadataBase.copy_with_keyword_parameters)
    def copy_with_keyword_parameters(self, keyword_parameters):
        return self.copy_with(
            button_style = keyword_parameters.pop('button_style', ...),
            custom_id = keyword_parameters.pop('custom_id', ...),
            emoji = keyword_parameters.pop('emoji', ...),
            enabled = keyword_parameters.pop('enabled', ...),
            label = keyword_parameters.pop('label', ...),
            sku_id = keyword_parameters.pop('sku_id', ...),
            url = keyword_parameters.pop('url', ...),
        )
