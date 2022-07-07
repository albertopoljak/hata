__all__ = ('AutoModerationRuleTriggerMetadata', 'KeywordPresetTriggerMetadata', 'KeywordTriggerMetadata')

from scarletio import RichAttributeErrorBaseType, copy_docs, include


AutoModerationKeywordPresetType = include('AutoModerationKeywordPresetType')


def try_get_auto_moderation_trigger_metadata_type_from_data(data):
    """
    Tries to detect what type of auto moderation trigger metadata the given data is.
    
    Parameters
    ----------
    data : `dict` of (`str`, `str`) items
        Auto moderation trigger metadata data.
    
    Returns
    -------
    metadata_type : `None`, `type`
    """
    if 'keyword_filter' in data:
        metadata_type = KeywordTriggerMetadata
    elif 'presets' in data:
        metadata_type = KeywordPresetTriggerMetadata
    else:
        metadata_type = None
    
    return metadata_type


class AutoModerationRuleTriggerMetadata(RichAttributeErrorBaseType):
    """
    Base class for ``AutoModerationRule``'s trigger metadata.
    """
    __slots__ = ()
    
    def __new__(cls):
        """
        Creates a new trigger metadata instance.
        """
        return object.__new__(cls)
        
    def __repr__(self):
        """Returns the trigger metadata's representation."""
        return f'<{self.__class__.__name__}>'
    
    
    @classmethod
    def from_data(cls, data):
        """
        Creates a new auto moderation rule trigger metadata instance from the given data.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Auto moderation rule trigger metadata payload.
        
        Returns
        -------
        self : ``ScheduledEventEntityMetadata``
        """
        return object.__new__(cls)
    
    
    def to_data(self):
        """
        Converts the trigger metadata to json serializable object.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        return {}
    
    
    def __eq__(self, other):
        """Returns whether the two trigger metadatas are equal."""
        if type(self) is not type(other):
            return NotImplemented
        
        return True
    
    
    def __hash__(self):
        """Returns the trigger metadata's hash value."""
        return 0
    
    
    def copy(self):
        """
        Copies the trigger metadata.
        
        Returns
        -------
        new : ``AutoModerationRuleTriggerMetadata``
        """
        return object.__new__(type(self))


class KeywordTriggerMetadata(AutoModerationRuleTriggerMetadata):
    """
    Keyword trigger metadata for an auto moderation rule.
    
    Attributes
    ----------
    keywords : `None`, `tuple` of `str`
        Substrings which will be searched for in content.
    
    Matching Strategies
    -------------------
    Use the `*` wildcard symbol at the beginning and end of a keyword to define how the keyword should be matched.
    All keywords are not case sensitive.
    
    - `Prefix` - word must start with the keyword
        +-----------+---------------------------------------+
        | Keyword   | Matches                               |
        +===========+=======================================+
        | cat*      | catch, Catapult, CAttLE               |
        +-----------+---------------------------------------+
        | tra*      | train, trade, TRAditional             |
        +-----------+---------------------------------------+
        | the mat*  | the matrix                            |
        +-----------+---------------------------------------+
    
    
    - `Suffix` - word must end with the keyword
    
        +-----------+---------------------------------------+
        | Keyword   | Matches                               |
        +===========+=======================================+
        | *cat      | wildcat, copyCat                      |
        +-----------+---------------------------------------+
        | *tra      | extra, ultra, orchesTRA               |
        +-----------+---------------------------------------+
        | *the mat  | breathe mat                           |
        +-----------+---------------------------------------+
    
    
    - `Anywhere` - keyword can appear anywhere in the content
    
        +-----------+---------------------------------------+
        | Keyword     | Matches                             |
        +===========+=======================================+
        | *cat*       | location, eduCation                 |
        +-----------+---------------------------------------+
        | *tra*       | abstracted, outrage                 |
        +-----------+---------------------------------------+
        | *the mat*   | breathe matter                      |
        +-----------+---------------------------------------+
    
    
    - `Whole Word` - keyword is a full word or phrase and must be surrounded by whitespace at the beginning and end
    
        +-----------+---------------------------------------+
        | Keyword   | Matches                               |
        +===========+=======================================+
        | cat       | cat                                   |
        +-----------+---------------------------------------+
        | train     | train                                 |
        +-----------+---------------------------------------+
        | the mat   | the mat                               |
        +-----------+---------------------------------------+
    """
    __slots__ = ('keywords',)
    
    def __new__(cls, keywords):
        """
        Creates a new keyword trigger metadata for ``AutoModerationRule``-s.
        
        Parameters
        ----------
        keywords : `None`, `str`, `iterable` of `str`
            Substrings which will be searched for in content.
               
        Raises
        ------
        TypeError
            - If `keywords` type is incorrect.
            - If a keyword's type is incorrect.
        """
        if keywords is None:
            processed_keywords = None
        
        elif isinstance(keywords, str):
            processed_keywords = (keywords, )
        
        else:
            iterator = getattr(type(keywords), '__iter__', None)
            if iterator is None:
                raise TypeError(
                    f'`keywords` can be `None`, `str`, `iterable` of `str`, '
                    f'got {keywords.__class__.__name__}; {keywords!r}.'
                )
            
            processed_keywords = None
            
            for keyword in iterator(keywords):
                if not isinstance(keyword, str):
                    raise TypeError(
                        f'`keywords` can contain `str` elements, got {keyword.__class__.__name__}; {keyword!r}; '
                        f'keywords={keywords!r}'
                    )
                
                if processed_keywords is None:
                    processed_keywords = set()
                
                processed_keywords.add(keyword)
            
            if (processed_keywords is not None):
                processed_keywords = tuple(sorted(processed_keywords))
        
        self = object.__new__(cls)
        self.keywords = processed_keywords
        return self
    
    
    @copy_docs(AutoModerationRuleTriggerMetadata.__repr__)
    def __repr__(self):
        repr_parts = ['<', self.__class__.__name__]
        
        # keywords
        keywords = self.keywords
        repr_parts.append(' keywords=[')
        if (keywords is not None):
            index = 0
            limit = len(keywords)
            while True:
                keyword = keywords[index]
                repr_parts.append(repr(keyword))
                
                index += 1
                if index == limit:
                    break
                
                repr_parts.append(', ')
                continue
        
        repr_parts.append(']')
        
        repr_parts.append('>')
        return ''.join(repr_parts)
    
    
    @classmethod
    @copy_docs(AutoModerationRuleTriggerMetadata.from_data)
    def from_data(cls, data):
        keyword_array = data.get('keyword_filter', None)
        if (keyword_array is None) or (not keyword_array):
            keywords = None
        else:
            keywords = tuple(sorted(keyword_array))
        
        self = object.__new__(cls)
        self.keywords = keywords
        return self
    
    
    @copy_docs(AutoModerationRuleTriggerMetadata.to_data)
    def to_data(self):
        data = {}
        
        data['keyword_filter'] = [*self.iter_keywords()]
        
        return data
    
    
    @copy_docs(AutoModerationRuleTriggerMetadata.__eq__)
    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        
        if self.keywords != other.keywords:
            return False
        
        return True
    
    
    @copy_docs(AutoModerationRuleTriggerMetadata.__hash__)
    def __hash__(self):
        hash_value = 0
        
        keywords = self.keywords
        if (keywords is not None):
            hash_value ^= len(keywords)
            
            for keyword in keywords:
                hash_value ^= hash(keyword)
        
        return hash_value
    
    
    @copy_docs(AutoModerationRuleTriggerMetadata.copy)
    def copy(self):
        new = AutoModerationRuleTriggerMetadata.copy(self)
        
        # keywords
        keywords = self.keywords
        if (keywords is not None):
            keywords = tuple(keyword for keyword in keywords)
        new.keywords = keywords
        
        return new
    
    
    def iter_keywords(self):
        """
        Iterates over the keywords of the keyword trigger metadata.
        
        This method is an iterable generator.
        
        Yields
        ------
        keyword : `str`
        """
        keywords = self.keywords
        if (keywords is not None):
            yield from keywords


class KeywordPresetTriggerMetadata(AutoModerationRuleTriggerMetadata):
    """
    Keyword keyword preset trigger metadata for an auto moderation rule.
    
    Attributes
    ----------
    keyword_presets : `None`, `tuple` of `str`
        Substrings which will be searched for in content.
    """
    __slots__ = ('keyword_presets',)
    
    def __new__(cls, keyword_presets):
        """
        Creates a new keyword preset trigger metadata for ``AutoModerationRule``-s.
        
        Parameters
        ----------
        keyword_presets : `None`, `int`, ``AutoModerationKeywordPresetType``, \
                `iterable` of (`int`, ``AutoModerationKeywordPresetType``)
            Keyword preset defined by Discord which will be searched for in content.
        
        Raises
        ------
        TypeError
            - If `keyword_presets` type is incorrect.
            - If a keyword preset's type is incorrect.
        """
        if keyword_presets is None:
            processed_keyword_presets = None
        
        elif isinstance(keyword_presets, int):
            keyword_preset = AutoModerationKeywordPresetType.get(keyword_presets)
            processed_keyword_presets = (keyword_preset, )
        
        elif isinstance(keyword_presets, AutoModerationKeywordPresetType):
            processed_keyword_presets = (keyword_presets, )
        
        else:
            iterator = getattr(type(keyword_presets), '__iter__', None)
            if iterator is None:
                raise TypeError(
                    f'`keyword_presets` can be `None`, `int`, `{AutoModerationKeywordPresetType.__name__}`, '
                    f'`iterable` of (`int`, `{AutoModerationKeywordPresetType.__name__}`'
                    f'got {keyword_presets.__class__.__name__}; {keyword_presets!r}.'
                )
            
            processed_keyword_presets = None
            
            for keyword_preset in iterator(keyword_presets):
                if isinstance(keyword_preset, int):
                    keyword_preset = AutoModerationKeywordPresetType.get(keyword_preset)
                
                elif isinstance(keyword_preset, AutoModerationKeywordPresetType):
                    pass
                
                else:
                    raise TypeError(
                        f'`keyword_preset` can contain `int`, `{AutoModerationKeywordPresetType.__name__}` elements, '
                        f'got {keyword_preset.__class__.__name__}; {keyword_preset!r}; '
                        f'keyword_presets={keyword_presets!r}'
                    )
                
                if processed_keyword_presets is None:
                    processed_keyword_presets = set()
                
                processed_keyword_presets.add(keyword_preset)
            
            if (processed_keyword_presets is not None):
                processed_keyword_presets = tuple(sorted(processed_keyword_presets))
        
        self = object.__new__(cls)
        self.keyword_presets = processed_keyword_presets
        return self
    
    @copy_docs(AutoModerationRuleTriggerMetadata.__repr__)
    def __repr__(self):
        repr_parts = ['<', self.__class__.__name__]
        
        # keyword_presets
        keyword_presets = self.keyword_presets
        repr_parts.append(' keywords=[')
        if (keyword_presets is not None):
            index = 0
            limit = len(keyword_presets)
            while True:
                keyword = keyword_presets[index]
                repr_parts.append(repr(keyword.name))
                repr_parts.append('~')
                repr_parts.append(repr(keyword.value))
                
                index += 1
                if index == limit:
                    break
                
                repr_parts.append(', ')
                continue
        
        repr_parts.append(']')
        
        repr_parts.append('>')
        return ''.join(repr_parts)
    
    
    @classmethod
    @copy_docs(AutoModerationRuleTriggerMetadata.from_data)
    def from_data(cls, data):
        keyword_preset_array = data.get('presets', None)
        if (keyword_preset_array is None) or (not keyword_preset_array):
            keyword_presets = None
        else:
            keyword_presets = tuple(sorted(
                AutoModerationKeywordPresetType.get(keyword_preset) for keyword_preset in keyword_preset_array
            ))
        
        self = object.__new__(cls)
        self.keyword_presets = keyword_presets
        return self
    
    
    @copy_docs(AutoModerationRuleTriggerMetadata.to_data)
    def to_data(self):
        data = {}
        
        keyword_presets = self.keyword_presets
        if (keyword_presets is None):
            keyword_preset_array = []
        else:
            keyword_preset_array = [keyword_preset.value for keyword_preset in keyword_presets]
        
        data['presets'] = keyword_preset_array
        
        return data
    
    
    @copy_docs(AutoModerationRuleTriggerMetadata.__eq__)
    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        
        if self.keyword_presets != other.keyword_presets:
            return False
        
        return True
    
    
    @copy_docs(AutoModerationRuleTriggerMetadata.__hash__)
    def __hash__(self):
        hash_value = 0
        
        keyword_presets = self.keyword_presets
        if (keyword_presets is not None):
            hash_value ^= len(keyword_presets)
            
            shift = 0
            
            for keyword_preset in keyword_presets:
                shift += 4
                
                hash_value ^= keyword_preset.value << shift
        
        return hash_value
    
    
    @copy_docs(AutoModerationRuleTriggerMetadata.copy)
    def copy(self):
        new = AutoModerationRuleTriggerMetadata.copy(self)
        
        # keywords
        keyword_presets = self.keyword_presets
        if (keyword_presets is not None):
            keyword_presets = tuple(keyword_preset for keyword_preset in keyword_presets)
        new.keyword_presets = keyword_presets
        
        return new
    
    
    def iter_keyword_presets(self):
        """
        Iterates over the keyword presets of the keyword trigger metadata.
        
        This method is an iterable generator.
        
        Yields
        ------
        keyword_preset : `AutoModerationKeywordPresetType`
        """
        keyword_presets = self.keyword_presets
        if (keyword_presets is not None):
            yield from keyword_presets
