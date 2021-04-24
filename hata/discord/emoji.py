﻿# -*- coding: utf-8 -*-
__all__ = ('BUILTIN_EMOJIS', 'UNICODE_TO_EMOJI', 'Emoji', 'parse_emoji', 'parse_custom_emojis', 'reaction_mapping',
    'reaction_mapping_line',)

from ..backend.utils import DOCS_ENABLED
from ..backend.export import export

from .bases import DiscordEntity
from .client_core import EMOJIS
from .utils import id_to_time, EMOJI_RP, DISCORD_EPOCH_START, DATETIME_FORMAT_CODE
from .user import User, ZEROUSER
from .preconverters import preconvert_str, preconvert_bool, preconvert_snowflake
from .role import create_partial_role

from . import urls as module_urls

UNICODE_EMOJI_LIMIT = 1<<21

BUILTIN_EMOJIS = {}
UNICODE_TO_EMOJI = {}

@export
def create_partial_emoji(data):
    """
    Creates an emoji from partial emoji data sent by Discord.
    
    Parameters
    ----------
    data : `dict` of (`str`, `Any`) items
        Partial emoji data.
    
    Returns
    -------
    emoji : ``Emoji``
    """
    try:
        name = data['name']
    except KeyError:
        name = data['emoji_name']
        emoji_id = data.get('emoji_id', None)
    else:
        emoji_id = data.get('id', None)
    
    if emoji_id is None:
        try:
            return UNICODE_TO_EMOJI[name]
        except KeyError:
            raise RuntimeError(f'Undefined emoji : {name.encode()!r}\nPlease open an issue with this message.') \
                from None
    
    emoji_id = int(emoji_id)
    
    try:
        emoji = EMOJIS[emoji_id]
    except KeyError:
        emoji = object.__new__(Emoji)
        emoji.id = emoji_id
        emoji.animated = data.get('animated', False)
        EMOJIS[emoji_id] = emoji
        emoji.unicode = None
        emoji.guild = None
    
    # name can change
    if name is None:
        name = ''
    
    emoji.name = name
    
    return emoji


def create_partial_emoji_data(emoji):
    """
    Creates partial emoji data form the given emoji.
    
    Parameters
    ----------
    emoji : ``Emoji``
        The emoji to serialize.
    
    Returns
    -------
    data : `dict` of (`str`, `Any`) items
        The serialized emoji data.
    """
    emoji_data = {}
    unicode = emoji.unicode
    if unicode is None:
        emoji_data['id'] = emoji.id
        emoji_data['name'] = emoji.name
    else:
        emoji_data['name'] = unicode
    
    return emoji_data

class Emoji(DiscordEntity, immortal=True):
    """
    Represents a Discord emoji. It can be custom or builtin (unicode) emoji as well. Builtin emojis are loaded when the
    module is imported and they are stores at `BUILTIN_EMOJIS` dictionary. At `BUILTIN_EMOJIS` the keys are the
    emoji's names, so it is easy to access any Discord unicode emoji like that.
    
    Custom emojis are loaded with ``Guild``-s on startup, but new partial custom emojis can be created later as well,
    when a ``Message`` receives any reaction.
    
    Attributes
    ----------
    id : `int`
        Unique identifier of the emoji.
    animated : `bool`
        Whether the emoji is animated.
    available : `bool`
        Whether the emoji is available.
    guild : `None` or ``Guild``
        The emoji's guild. Can be set as `None` if:
        - If the emoji is a builtin (unicode).
        - If the emoji's guild is unknown.
        - If the emoji is deleted.
    managed : `bool`
        Whether the emoji is managed by an integration.
    name : `int`
        The emoji's name.
    roles : `None` or `list` of ``Role`` objects
        The set of roles for which the custom emoji is whitelisted to. If the emoji is not limited for specific roles,
        then this value is set to `None`. If the emoji is a builtin (unicode) emoji, then this attribute is set to
        `None` as  well.
    unicode : `None` or `str`
        At the case of custom emojis this attribute is always `None`, but at the case of builtin (unicode) emojis this
        attribute stores the emoji's unicode representation.
    user : ``User`` or ``Client``
        The creator of the custom emoji. The emoji must be requested from Discord's API, or it's user will be just
        the default `ZEROUSER`.
        
    See Also
    --------
    - ``create_partial_emoji`` : A function to create an emoji object from partial emoji data.
    - ``parse_emoji`` : Parses a partial emoji object out from text.
    """
    __slots__ = ('animated', 'available', 'guild', 'managed', 'name', 'require_colons', 'roles', 'unicode', 'user', )
    
    def __new__(cls, data, guild):
        """
        Creates a new emoji object from emoji data included with it's guild's. If the emoji already exists, picks that
        up instead of creating a new one.
        
        This method can not create builtin (unicode) emojis. Those are created when the library is loaded.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Emoji data received from Discord.
        guild : ``Guild``
            The guild of the emoji.
        
        Returns
        -------
        emoji : ``Emoji``
        """
        emoji_id = int(data['id'])

        try:
            emoji = EMOJIS[emoji_id]
        except KeyError:
            emoji = object.__new__(cls)
            emoji.id = emoji_id
            EMOJIS[emoji_id] = emoji
        else:
            # whenever we receive an emoji, it will have no user data included,
            # so it is enough if we check for user data only whenever we
            # receive emoji data from a request or so.
            if (emoji.guild is not None):
                if not emoji.user.id:
                    try:
                        user_data = data['user']
                    except KeyError:
                        pass
                    else:
                        emoji.user = User(user_data)
                return emoji
        
        name = data['name']
        if name is None:
            name = ''
        
        emoji.name = name
        emoji.animated = data.get('animated', False)
        emoji.require_colons= data.get('require_colons', True)
        emoji.managed = data.get('managed', False)
        emoji.guild = guild
        emoji.available = data.get('available', True)
        emoji.user = ZEROUSER
        emoji.unicode = None
        
        role_ids = data.get('roles', None)
        if (role_ids is None) or (not role_ids):
            roles = None
        else:
            roles = sorted(create_partial_role(int(role_id)) for role_id in role_ids)
        
        emoji.roles = roles
        
        return emoji
    
    @classmethod
    def precreate(cls, emoji_id, **kwargs):
        """
        Precreates the emoji by creating a partial one with the given parameters. When the emoji is loaded
        the precrated one will be picked up. If an already existing emoji would be precreated, returns that
        instead and updates that only, if that is partial.
        
        Parameters
        ----------
        emoji_id : `snowflake`
            The emoji's id.
        **kwargs : keyword arguments
            Additional predefined attributes for the emoji.
        
        Other Parameters
        ----------------
        name : `str`, Optional (Keyword only)
            The emoji's ``.name``. Can be between length `2` and `32`.
        animated : `bool`, Optional (Keyword only)
            Whether the emoji is animated.
        
        Returns
        -------
        emoji : ``Emoji``
        
        Raises
        ------
        TypeError
            If any argument's type is bad or if unexpected argument is passed.
        ValueError
            If an argument's type is good, but it's value is unacceptable.
        """
        emoji_id = preconvert_snowflake(emoji_id, 'emoji_id')
        
        if kwargs:
            processable = []
            
            try:
                name = kwargs.pop('name')
            except KeyError:
                pass
            else:
                name = preconvert_str(name, 'name', 2, 32)
                processable.append(('name',name))
            
            try:
                animated = kwargs.pop('animated')
            except KeyError:
                pass
            else:
                animated = preconvert_bool(animated, 'animated')
                processable.append(('animated', animated))
            
            if kwargs:
                raise TypeError(f'Unused or unsettable attributes: {kwargs}')
        
        else:
            processable = None
        
        try:
            emoji = EMOJIS[emoji_id]
        except KeyError:
            emoji = object.__new__(cls)
            
            emoji.name = ''
            emoji.animated = False
            emoji.id = emoji_id 
            emoji.guild = None
            emoji.unicode = None
            emoji.user = ZEROUSER
            
            EMOJIS[emoji_id]= emoji
        else:
            if (emoji.guild is not None) or (emoji.unicode is not None):
                return emoji
        
        if (processable is not None):
            for name, value in processable:
                setattr(emoji, name, value)
        
        return emoji
    
    def __str__(self):
        """Returns the emoji's name."""
        return self.name
    
    def __repr__(self):
        """Returns the emoji's representation."""
        return f'<{self.__class__.__name__} id={self.id}, name={self.name!r}>'
    
    def __format__(self, code):
        """
        Formats the emoji in a format string.
        
        Parameters
        ----------
        code : `str`
            The option on based the result will be formatted.
        
        Returns
        -------
        emoji : `str`
        
        Raises
        ------
        ValueError
            Unknown format code.
        
        Examples
        --------
        ```py
        >>> from hata import Emoji, now_as_id, BUILTIN_EMOJIS
        >>> emoji = Emoji.precreate(now_as_id(), name='nice')
        >>> emoji
        <Emoji id=712359434843586560, name='nice'>
        >>> # no code stands for str(emoji)
        >>> f'{emoji}'
        'nice'
        >>> # 'e' stands for emoji format.
        >>> f'{emoji:e}'
        '<:nice:712359434843586560>'
        >>> # 'r' stands for reaction format.
        >>> f'{emoji:r}'
        'nice:712359434843586560'
        >>> # 'c' stands for created at.
        >>> f'{emoji:c}'
        '2020.05.19-17:42:04'
        >>> # The following works with builtin (unicode) emojis as well.
        >>> emoji = BUILTIN_EMOJIS['heart']
        >>> f'{emoji}'
        'heart'
        >>> f'{emoji:e}'
        '❤️'
        >>> f'{emoji:r}'
        '❤️'
        >>> f'{emoji:c}'
        '2015.01.01-00:00:00'
        ```
        """
        if not code:
            return self.name
        
        if code == 'e':
            if self.id < UNICODE_EMOJI_LIMIT:
                return self.unicode
            
            if self.animated:
                return f'<a:{self.name}:{self.id}>'
            else:
                return f'<:{self.name}:{self.id}>'
        
        if code == 'r':
            if self.id < UNICODE_EMOJI_LIMIT:
                return self.unicode
            
            return f'{self.name}:{self.id}'
        
        if code == 'c':
            return self.created_at.__format__(DATETIME_FORMAT_CODE)
        
        raise ValueError(f'Unknown format code {code!r} for object of type {self.__class__.__name__!r}')
    
    @property
    def partial(self):
        """
        Returns whether the emoji is partial.
        
        Returns
        -------
        partial : `bool`
        """
        if (self.unicode is not None):
            return False
        
        if (self.guild is not None):
            return False
        
        return True
    
    def is_custom_emoji(self):
        """
        Returns whether the emoji is a custom emoji.
        
        Returns
        -------
        is_custom_emoji : `bool`
        """
        return (self.id >= UNICODE_EMOJI_LIMIT)

    def is_unicode_emoji(self):
        """
        Returns whether the emoji is a unicode emoji.
        
        Returns
        -------
        is_custom_emoji : `bool`
        """
        return (self.id < UNICODE_EMOJI_LIMIT)
    
    @property
    def as_reaction(self):
        """
        Returns the emoji's reaction form, which is used by the Discord API at requests when working with reactions.
        
        Returns
        -------
        as_reaction : `str`
        """
        if self.id < UNICODE_EMOJI_LIMIT:
            return self.unicode
        
        return f'{self.name}:{self.id}'
    
    @property
    def as_emoji(self):
        """
        Returns the emoji's emoji form. Should be used when sending an emoji within a ``Message``.
        
        Returns
        -------
        as_emoji : `str`
        """
        if self.id < UNICODE_EMOJI_LIMIT:
            return self.unicode
        
        if self.animated:
            return f'<a:{self.name}:{self.id}>'
        else:
            return f'<:{self.name}:{self.id}>'
    
    @property
    def created_at(self):
        """
        When the emoji was created. If the emoji is unicode emoji, then returns Discord epoch's start.
        
        Returns
        -------
        created_at : `datetime`
        """
        id_ = self.id
        if id_ > UNICODE_EMOJI_LIMIT:
            created_at = id_to_time(id_)
        else:
            created_at = DISCORD_EPOCH_START
        
        return created_at

    url = property(module_urls.emoji_url)
    url_as = module_urls.emoji_url_as
    
    def _delete(self):
        """
        Removes the emoji's references.
        
        Used when the emoji is deleted.
        """
        guild = self.guild
        if guild is None:
            return
        
        del guild.emojis[self.id]
        self.roles = None
        self.guild = None
        self.available = False
        
    def _update_no_return(self, data):
        """
        Updates the emoji with overwriting it's old attributes.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Emojis data received from Discord
        """
        self.require_colons = data.get('require_colons', True)
        self.managed = data.get('managed', False)
        
        self.animated = data.get('animated', False)
        
        name = data['name']
        if name is None:
            name = ''
        
        self.name = name
        
        role_ids = data.get('roles', None)
        if (role_ids is None) or (not role_ids):
            roles = None
        else:
            roles = sorted(create_partial_role(int(role_id)) for role_id in role_ids)
        
        self.roles = roles
        
        try:
            user_data = data['user']
        except KeyError:
            pass
        else:
            self.user = User(user_data)

        self.available = data.get('available', True)
            
    def _update(self, data):
        """
        Updates the emoji and returns it's overwritten old attributes as a `dict` with a `attribute-name` - `old-value`
        relation.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Emoji data received from Discord.
        
        Returns
        -------
        old_attributes : `dict` of (`str`, `Any`) items
            All item in the returned dict is optional.
        
        Returned Data Structure
        -----------------------
        +-------------------+-------------------------------+
        | Keys              | Values                        |
        +===================+===============================+
        | animated          | `bool`                        |
        +-------------------+-------------------------------+
        | available         | `bool`                        |
        +-------------------+-------------------------------+
        | managed           | `bool`                        |
        +-------------------+-------------------------------+
        | name              | `int`                         |
        +-------------------+-------------------------------+
        | require_colons    | `bool`                        |
        +-------------------+-------------------------------+
        | roles             | `None` or `set` of ``Role``   |
        +-------------------+-------------------------------+
        """
        old_attributes = {}
        
        require_colons = data.get('require_colons', True)
        if self.require_colons != require_colons:
            old_attributes['require_colons'] = self.require_colons
            self.require_colons = require_colons
        
        managed = data.get('managed', False)
        if self.managed != managed:
            old_attributes['managed'] = self.managed
            self.managed = managed
        
        animated = data.get('animated', False)
        if self.animated != animated:
            old_attributes['animated'] = self.animated
            self.animated = animated
        
        name = data['name']
        if name is None:
            name = ''
        if self.name != name:
            old_attributes['name'] = self.name
            self.name = name
        
        role_ids = data.get('roles', None)
        if (role_ids is None) or (not role_ids):
            roles = None
        else:
            roles = sorted(create_partial_role(int(role_id)) for role_id in role_ids)
        
        if self.roles != roles:
            old_attributes['roles'] = self.roles
            self.roles = roles
        
        try:
            user_data = data['user']
        except KeyError:
            pass
        else:
            self.user = User(user_data)
        
        available = data.get('available', True)
        if self.available != available:
            old_attributes['available'] = self.available
            self.available = available
        
        return old_attributes
    
    @classmethod
    def _from_parsed_group(cls, groups):
        """
        Creates a new emoji from the given parsed out groups.
        
        Parameters
        ----------
        groups : `tuple` ((`str` or `None`), `str`, `str`)
            A tuple, which contains whether the emoji to create is animated (element 0), the emoji's name (element 1) and
            the emoji's id. (element 2).
        
        Returns
        -------
        emoji : ``Emoji``
        """
        animated, name, emoji_id = groups
        emoji_id = int(emoji_id)
        
        try:
            emoji = EMOJIS[emoji_id]
            if emoji.guild is None:
                emoji.name = name
        except KeyError:
            emoji = object.__new__(cls)
            emoji.id = emoji_id
            emoji.animated = (animated is not None)
            emoji.name = name
            emoji.unicode = None
            emoji.guild = None
            emoji.available = True
            emoji.require_colons = True
            emoji.managed = False
            emoji.user = ZEROUSER
            emoji.roles = None
            EMOJIS[emoji_id] = emoji
        
        return emoji

class reaction_mapping_line(set):
    """
    A `set` subclass which contains the users who reacted with the given ``Emoji`` on a ``Message``.
    
    Attributes
    ----------
    unknown : `int`
        The amount of not known reactors.
    """
    __slots__ = ('unknown',)
    
    def __init__(self, unknown):
        """
        Creates a `reaction_mapping_line`.
        
        Parameters
        ----------
        unknown : `int`
            The amount of not known reactors.
        """
        self.unknown = unknown
    
    def __len__(self):
        """Returns the amount of users, who reacted with the given emoji on the respective message."""
        return set.__len__(self)+self.unknown
    
    def __repr__(self):
        """Returns the representation of the container."""
        result = [
            self.__class__.__name__,
            '({',
        ]
        
        # set indexing is not public, so we need to do a check, like this
        if set.__len__(self):
            for user in self:
                result.append(repr(user))
                result.append(', ')
            
            result[-1] = '}'
        else:
            result.append('}')
        
        unknown = self.unknown
        if unknown:
            result.append(', unknown=')
            result.append(repr(unknown))
        
        result.append(')')
        
        return ''.join(result)
    
    @classmethod
    def _full(cls, users):
        """
        Creates a new ``reaction_mapping_line`` with the given users with `.unknown` set to `0`.
        
        Parameters
        ----------
        users : `list` of (``User`` or ``Client``) objects
            A `list`, which should already contain all the users of the reaction mapping line.

        Returns
        -------
        self : ``reaction_mapping_line``
        """
        self = set.__new__(cls)
        set.__init__(self, users)
        self.unknown = 0
        return self
    
    def update(self, users):
        """
        Updates the reaction mapping line with the given users.
        
        Parameters
        ----------
        users : `list` of (``User`` or ``Client``) objects
            A `list` of users, who reacted on the respective `Message` with the respective ``Emoji``.
        """
        ln_old = len(self)
        set.update(self,users)
        ln_new = len(self)
        self.unknown -= (ln_new-ln_old)
    
    def copy(self):
        """
        Copies the reaction mapping line.
        
        Returns
        -------
        new : ``reaction_mapping_line``
        """
        new = set.__new__(type(self))
        set.__init__(new,self)
        new.unknown = self.unknown
        return new
    
    # executes an api request if we know we know all reactors
    def filter_after(self, limit, after):
        """
        If we know all the reactors, then instead of executing a Discord API request we filter the reactors locally
        using this method.
        
        Parameters
        ----------
        limit : `int`
            The maximal limit of the users to return.
        after : `int`
            Gets the users after this specified id.
        
        Returns
        -------
        users : `
        """
        list_form = sorted(self)
        
        after = after+1 # do not include the specified id
        
        bot = 0
        top = len(list_form)
        while True:
            if bot<top:
                half = (bot+top)>>1
                if list_form[half].id<after:
                    bot = half+1
                else:
                    top = half
                continue
            break
        
        index = bot
        
        length = len(list_form)
        users = []
        
        while True:
            if index == length:
                break
            
            if limit <= 0:
                break
            
            users.append(list_form[index])
            index += 1
            limit -= 1
            continue
        
        return users
    
    def clear(self):
        """
        Clears the reaction mapping line by removing every ``User`` object from it.
        """
        clients = []
        for user in self:
            if type(user) is User:
                continue
            clients.append(user)

        self.unknown += (set.__len__(self) - len(clients))
        set.clear(self)
        set.update(self,clients)

class reaction_mapping(dict):
    """
    A `dict` subclass, which contains the reactions on a ``Message`` with (``Emoji``, ``reaction_mapping_line``)
    items.
    
    Attributes
    ----------
    fully_loaded : `bool`
        Whether the reaction mapping line is fully loaded.
    """
    __slots__ = ('fully_loaded',)
    def __init__(self, data):
        """
        Fills the reaction mapping with the given data.
        
        Parameters
        ----------
        data : `None` or `dict` of (`str`, `Any`) items
        """
        if (data is None) or (not data):
            self.fully_loaded = True
            return
        
        self.fully_loaded = False
        for line in data:
            self[create_partial_emoji(line['emoji'])] = reaction_mapping_line(line.get('count', 1))
    
    emoji_count = property(dict.__len__)
    if DOCS_ENABLED:
        emoji_count.__doc__ = (
        """
        The amount of different emojis, which were added on the reaction mapping's respective ``Message``.
        
        Returns
        -------
        emoji_count : `int`
        """)
    
    @property
    def total_count(self):
        """
        The total amount reactions given on the reaction mapping's respective message.
        
        Returns
        -------
        total_count : `int`
        """
        count = 0
        for line in self.values():
            count += set.__len__(line)
            count += line.unknown
        return count
    
    def clear(self):
        """
        Clears the reaction mapping with clearing it's lines.
        """
        for value in self.values():
            value.clear()
        if self.fully_loaded:
            self._full_check()
    
    def add(self, emoji, user):
        """
        Adds a user to the reactors.
        
        Parameters
        ----------
        emoji : ``Emoji``
            The reacted emoji.
        user : ``User`` or ``Client``
            The reactor user.
        """
        try:
            line = self[emoji]
        except KeyError:
            line = reaction_mapping_line(0)
            self[emoji] = line
        line.add(user)
    
    def remove(self, emoji, user):
        """
        Removes a user to the reactors.
        
        Parameters
        ----------
        emoji : ``Emoji``
            The removed reacted emoji.
        user : ``User`` or ``Client``
            The removed reactor user.
        """
        try:
            line = self[emoji]
        except KeyError:
            return

        if set.__len__(line):
            try:
                line.remove(user)
            except KeyError:
                pass
            else:
                if set.__len__(line) or line.unknown:
                    return
                del self[emoji]
                return
        
        if line.unknown:
            line.unknown -=1
            if set.__len__(line):
                if line.unknown:
                    return
                self._full_check()
                return
            if line.unknown:
                return
            del self[emoji]
    
    def remove_emoji(self, emoji):
        """
        Removes all the users who reacted with the given ``Emoji`` and then returns the stored line.
        
        Parameters
        ----------
        emoji : ``Emoji``
            The emoji to remove.
        
        Returns
        -------
        line : `None` or ``reaction_mapping_line``
        """
        line = self.pop(emoji, None)
        if line is None:
            return
        
        if line.unknown:
            self._full_check()
        
        return line
    
    #this function is called if an emoji loses all it's unknown reactors
    def _full_check(self):
        """
        Checks whether the reaction mapping is fully loaded, by checking it's values' `.unknown` and sets the current
        state to `.fully_loaded`.
        """
        for line in self.values():
            if line.unknown:
                self.fully_loaded = False
                return 
        
        self.fully_loaded = True
        
    #we call this when we get SOME reactors of an emoji
    def _update_some_users(self, emoji, users):
        """
        Called when some reactors of an emoji are updated.
        
        Parameters
        ----------
        emoji : ``Emoji``
            The emoji, which's users' are updated.
        users : `list` of (``User`` or ``Client``) objects
            The added reactors.
        """
        self[emoji].update(users)
        self._full_check()
        
    def _update_all_users(self, emoji, users):
        """
        Called when all the reactors of an emoji are updated of the reaction mapping.
        
        Parameters
        ----------
        emoji : ``Emoji``
            The emoji, which's users' are updated.
        users : `list` of (``User`` or ``Client``) objects
            The added reactors.
        """
        self[emoji] = reaction_mapping_line._full(users)
        self._full_check()

def parse_emoji(text):
    """
    Tries to parse out an ``Emoji`` from the inputted text. This emoji can be custom and unicode emoji as well.
    
    If the parsing yields a custom emoji what is not loaded, the function will return an `untrusted` partial emoji,
    what means it wont be stored at `EMOJIS`. If the parsing fails the function returns `None`.
    
    Returns
    -------
    emoji : `None` or ``Emoji``
    """
    parsed = EMOJI_RP.fullmatch(text)
    if parsed is None:
        emoji = UNICODE_TO_EMOJI.get(text, None)
    else:
        emoji = Emoji._from_parsed_group(parsed.groups())
    
    return emoji


def parse_custom_emojis(text):
    """
    Parses out every custom emoji from the given text.
    
    Parameters
    ----------
    text : `str`
        Text, what might contain custom emojis.
    
    Returns
    -------
    emojis : `set` of ``Emoji``
    """
    emojis = set()
    for groups in EMOJI_RP.findall(text):
        emoji = Emoji._from_parsed_group(groups)
        emojis.add(emoji)
    
    return emojis


def generate_builtin_emojis():
    for emoji_id, element in enumerate((
            (b'\xf0\x9f\x8f\xbb', 'skin_tone_1', 'skin_tone_1'),
            (b'\xf0\x9f\x8f\xbc', 'skin_tone_2', 'skin_tone_2'),
            (b'\xf0\x9f\x8f\xbd', 'skin_tone_3', 'skin_tone_3'),
            (b'\xf0\x9f\x8f\xbe', 'skin_tone_4', 'skin_tone_4'),
            (b'\xf0\x9f\x8f\xbf', 'skin_tone_5', 'skin_tone_5'),
            (b'\xf0\x9f\x98\x93', 'sweat', 'sweat', ',:(', ',:-(', ',=(', ',=-('),
            (b'\xf0\x9f\x98\x85', 'sweat_smile', 'sweat_smile', ',:)', ',:-)', ',=)', ',=-)'),
            (b'\xf0\x9f\x98\x87', 'innocent', 'innocent', '0:)', '0:-)', '0=)', '0=-)', 'o:)', 'O:)', 'o:-)', 'O:-)', 'o=)', 'O=)', 'o=-)', 'O=-)'),
            (b'\xf0\x9f\x98\x8e', 'sunglasses', 'sunglasses', '8-)', 'B-)'),
            (b'\xf0\x9f\x98\x92', 'unamused', 'unamused', ':$', ':-$', ':-S', ':-Z', ':s', ':z', '=$', '=-$', '=-S', '=-Z', '=s', '=z'),
            (b'\xf0\x9f\x98\xa2', 'cry', 'cry', ":'(", ":'-(", ':,(', ':,-(', "='(", "='-(", '=,(', '=,-('),
            (b'\xf0\x9f\x98\x82', 'joy', 'joy', ":')", ":'-)", ":'-D", ":'D", ':,)', ':,-)', ':,-D', ':,D', "=')", "='-)", "='-D", "='D", '=,)', '=,-)', '=,-D', '=,D'),
            (b'\xf0\x9f\x98\xa6', 'frowning', 'frowning', ':(', ':-(', '=(', '=-('),
            (b'\xf0\x9f\x98\x83', 'smiley', 'smiley', ':)', ':-)', '=)', '=-)'),
            (b'\xf0\x9f\x98\x97', 'kissing', 'kissing', ':*', ':-*', '=*', '=-*'),
            (b'\xf0\x9f\x91\x8d', 'thumbsup', 'thumbsup', 'thumbup', '+1'),
            (b'\xf0\x9f\x91\x8d\xf0\x9f\x8f\xbb', 'thumbsup_tone1', 'thumbsup_tone1', 'thumbup_tone1', '+1_tone1'),
            (b'\xf0\x9f\x91\x8d\xf0\x9f\x8f\xbc', 'thumbsup_tone2', 'thumbsup_tone2', 'thumbup_tone2', '+1_tone2'),
            (b'\xf0\x9f\x91\x8d\xf0\x9f\x8f\xbd', 'thumbsup_tone3', 'thumbsup_tone3', 'thumbup_tone3', '+1_tone3'),
            (b'\xf0\x9f\x91\x8d\xf0\x9f\x8f\xbe', 'thumbsup_tone4', 'thumbsup_tone4', 'thumbup_tone4', '+1_tone4'),
            (b'\xf0\x9f\x91\x8d\xf0\x9f\x8f\xbf', 'thumbsup_tone5', 'thumbsup_tone5', 'thumbup_tone5', '+1_tone5'),
            (b'\xf0\x9f\x98\xad', 'sob', 'sob', ":,'(", ":,'-(", ';(', ';-(', "=,'(", "=,'-("),
            (b'\xf0\x9f\x98\x95', 'confused', 'confused', ':-/', ':-\\', '=-/', '=-\\'),
            (b'\xf0\x9f\x91\x8e', 'thumbdown', 'thumbdown', 'thumbsdown', '-1'),
            (b'\xf0\x9f\x91\x8e\xf0\x9f\x8f\xbb', 'thumbdown_tone1', 'thumbdown_tone1', 'thumbsdown_tone1', '_1_tone1', '-1_tone1'),
            (b'\xf0\x9f\x91\x8e\xf0\x9f\x8f\xbc', 'thumbdown_tone2', 'thumbdown_tone2', 'thumbsdown_tone2', '_1_tone2', '-1_tone2'),
            (b'\xf0\x9f\x91\x8e\xf0\x9f\x8f\xbd', 'thumbdown_tone3', 'thumbdown_tone3', 'thumbsdown_tone3', '_1_tone3', '-1_tone3'),
            (b'\xf0\x9f\x91\x8e\xf0\x9f\x8f\xbe', 'thumbdown_tone4', 'thumbdown_tone4', 'thumbsdown_tone4', '_1_tone4', '-1_tone4'),
            (b'\xf0\x9f\x91\x8e\xf0\x9f\x8f\xbf', 'thumbdown_tone5', 'thumbdown_tone5', 'thumbsdown_tone5', '_1_tone5', '-1_tone5'),
            (b'\xf0\x9f\x98\xa1', 'rage', 'rage', ':-@', ':@', '=-@', '=@'),
            (b'\xf0\x9f\x98\x8a', 'blush', 'blush', ':-")', ':")', '=-")', '=")'),
            (b'\xf0\x9f\x98\x84', 'smile', 'smile', ':-D', ':D', '=-D', '=D'),
            (b'\xf0\x9f\x98\xae', 'open_mouth', 'open_mouth', ':-o', ':-O', ':o', ':O', '=-o', '=-O', '=o', '=O'),
            (b'\xf0\x9f\x98\x9b', 'stuck_out_tongue', 'stuck_out_tongue', ':-P', ':P', '=-P', '=P'),
            (b'\xf0\x9f\x98\x90', 'neutral_face', 'neutral_face', ':-|', ':|', '=-|', '=|'),
            (b'\xf0\x9f\x92\xaf', '100', '100'),
            (b'\xf0\x9f\x94\xa2', '1234', '1234'),
            (b'\xf0\x9f\x8e\xb1', '8ball', '8ball'),
            (b'\xf0\x9f\x85\xb0', 'a', 'a_vs16'),
            (b'\xf0\x9f\x86\x8e', 'ab', 'ab'),
            (b'\xf0\x9f\x94\xa4', 'abc', 'abc'),
            (b'\xf0\x9f\x94\xa1', 'abcd', 'abcd'),
            (b'\xf0\x9f\x89\x91', 'accept', 'accept'),
            (b'\xf0\x9f\x8e\x9f', 'admission_tickets', 'admission_tickets_vs16'),
            (b'\xf0\x9f\x9a\xa1', 'aerial_tramway', 'aerial_tramway'),
            (b'\xe2\x9c\x88', 'airplane', 'airplane_vs16'),
            (b'\xf0\x9f\x9b\xac', 'airplane_arriving', 'airplane_arriving'),
            (b'\xf0\x9f\x9b\xab', 'airplane_departure', 'airplane_departure'),
            (b'\xf0\x9f\x9b\xa9', 'airplane_small', 'airplane_small_vs16'),
            (b'\xe2\x8f\xb0', 'alarm_clock', 'alarm_clock'),
            (b'\xe2\x9a\x97', 'alembic', 'alembic_vs16'),
            (b'\xf0\x9f\x91\xbd', 'alien', 'alien'),
            (b'\xf0\x9f\x9a\x91', 'ambulance', 'ambulance'),
            (b'\xf0\x9f\x8f\xba', 'amphora', 'amphora'),
            (b'\xe2\x9a\x93', 'anchor', 'anchor'),
            (b'\xf0\x9f\x91\xbc', 'angel', 'angel'),
            (b'\xf0\x9f\x91\xbc\xf0\x9f\x8f\xbb', 'angel_tone1', 'angel_tone1'),
            (b'\xf0\x9f\x91\xbc\xf0\x9f\x8f\xbc', 'angel_tone2', 'angel_tone2'),
            (b'\xf0\x9f\x91\xbc\xf0\x9f\x8f\xbd', 'angel_tone3', 'angel_tone3'),
            (b'\xf0\x9f\x91\xbc\xf0\x9f\x8f\xbe', 'angel_tone4', 'angel_tone4'),
            (b'\xf0\x9f\x91\xbc\xf0\x9f\x8f\xbf', 'angel_tone5', 'angel_tone5'),
            (b'\xf0\x9f\x92\xa2', 'anger', 'anger'),
            (b'\xf0\x9f\x97\xaf', 'anger_right', 'anger_right_vs16'),
            (b'\xf0\x9f\x98\xa0', 'angry', 'angry', '>:(', '>:-(', '>=(', '>=-('),
            (b'\xf0\x9f\x98\xa7', 'anguished', 'anguished'),
            (b'\xf0\x9f\x90\x9c', 'ant', 'ant'),
            (b'\xf0\x9f\x8d\x8e', 'apple', 'apple'),
            (b'\xe2\x99\x92', 'aquarius', 'aquarius'),
            (b'\xf0\x9f\x8f\xb9', 'archery', 'archery', 'bow_and_arrow'),
            (b'\xe2\x99\x88', 'aries', 'aries'),
            (b'\xe2\x97\x80', 'arrow_backward', 'arrow_backward_vs16'),
            (b'\xe2\x8f\xac', 'arrow_double_down', 'arrow_double_down'),
            (b'\xe2\x8f\xab', 'arrow_double_up', 'arrow_double_up'),
            (b'\xe2\xac\x87', 'arrow_down', 'arrow_down_vs16'),
            (b'\xf0\x9f\x94\xbd', 'arrow_down_small', 'arrow_down_small'),
            (b'\xe2\x96\xb6', 'arrow_forward', 'arrow_forward_vs16'),
            (b'\xe2\xa4\xb5', 'arrow_heading_down', 'arrow_heading_down_vs16'),
            (b'\xe2\xa4\xb4', 'arrow_heading_up', 'arrow_heading_up_vs16'),
            (b'\xe2\xac\x85', 'arrow_left', 'arrow_left_vs16'),
            (b'\xe2\x86\x99', 'arrow_lower_left', 'arrow_lower_left_vs16'),
            (b'\xe2\x86\x98', 'arrow_lower_right', 'arrow_lower_right_vs16'),
            (b'\xe2\x9e\xa1', 'arrow_right', 'arrow_right_vs16'),
            (b'\xe2\x86\xaa', 'arrow_right_hook', 'arrow_right_hook_vs16'),
            (b'\xe2\xac\x86', 'arrow_up', 'arrow_up_vs16'),
            (b'\xe2\x86\x95', 'arrow_up_down', 'arrow_up_down_vs16'),
            (b'\xf0\x9f\x94\xbc', 'arrow_up_small', 'arrow_up_small'),
            (b'\xe2\x86\x96', 'arrow_upper_left', 'arrow_upper_left_vs16'),
            (b'\xe2\x86\x97', 'arrow_upper_right', 'arrow_upper_right_vs16'),
            (b'\xf0\x9f\x94\x83', 'arrows_clockwise', 'arrows_clockwise'),
            (b'\xf0\x9f\x94\x84', 'arrows_counterclockwise', 'arrows_counterclockwise'),
            (b'\xf0\x9f\x8e\xa8', 'art', 'art'),
            (b'\xf0\x9f\x9a\x9b', 'articulated_lorry', 'articulated_lorry'),
            (b'*\xe2\x83\xa3', 'asterisk', 'asterisk_vs16'),
            (b'\xf0\x9f\x98\xb2', 'astonished', 'astonished'),
            (b'\xf0\x9f\x91\x9f', 'athletic_shoe', 'athletic_shoe'),
            (b'\xf0\x9f\x8f\xa7', 'atm', 'atm'),
            (b'\xe2\x9a\x9b', 'atom', 'atom_vs16'),
            (b'\xf0\x9f\xa5\x91', 'avocado', 'avocado'),
            (b'\xf0\x9f\x85\xb1', 'b', 'b_vs16'),
            (b'\xf0\x9f\x91\xb6', 'baby', 'baby'),
            (b'\xf0\x9f\x91\xb6\xf0\x9f\x8f\xbb', 'baby_tone1', 'baby_tone1'),
            (b'\xf0\x9f\x91\xb6\xf0\x9f\x8f\xbc', 'baby_tone2', 'baby_tone2'),
            (b'\xf0\x9f\x91\xb6\xf0\x9f\x8f\xbd', 'baby_tone3', 'baby_tone3'),
            (b'\xf0\x9f\x91\xb6\xf0\x9f\x8f\xbe', 'baby_tone4', 'baby_tone4'),
            (b'\xf0\x9f\x91\xb6\xf0\x9f\x8f\xbf', 'baby_tone5', 'baby_tone5'),
            (b'\xf0\x9f\x8d\xbc', 'baby_bottle', 'baby_bottle'),
            (b'\xf0\x9f\x90\xa4', 'baby_chick', 'baby_chick'),
            (b'\xf0\x9f\x9a\xbc', 'baby_symbol', 'baby_symbol'),
            (b'\xf0\x9f\x94\x99', 'back', 'back'),
            (b'\xf0\x9f\xa4\x9a', 'back_of_hand', 'back_of_hand', 'raised_back_of_hand'),
            (b'\xf0\x9f\xa4\x9a\xf0\x9f\x8f\xbb', 'back_of_hand_tone1', 'back_of_hand_tone1', 'raised_back_of_hand_tone1'),
            (b'\xf0\x9f\xa4\x9a\xf0\x9f\x8f\xbc', 'back_of_hand_tone2', 'back_of_hand_tone2', 'raised_back_of_hand_tone2'),
            (b'\xf0\x9f\xa4\x9a\xf0\x9f\x8f\xbd', 'back_of_hand_tone3', 'back_of_hand_tone3', 'raised_back_of_hand_tone3'),
            (b'\xf0\x9f\xa4\x9a\xf0\x9f\x8f\xbe', 'back_of_hand_tone4', 'back_of_hand_tone4', 'raised_back_of_hand_tone4'),
            (b'\xf0\x9f\xa4\x9a\xf0\x9f\x8f\xbf', 'back_of_hand_tone5', 'back_of_hand_tone5', 'raised_back_of_hand_tone5'),
            (b'\xf0\x9f\xa5\x93', 'bacon', 'bacon'),
            (b'\xf0\x9f\x8f\xb8', 'badminton', 'badminton'),
            (b'\xf0\x9f\x9b\x84', 'baggage_claim', 'baggage_claim'),
            (b'\xf0\x9f\xa5\x96', 'baguette_bread', 'baguette_bread', 'french_bread'),
            (b'\xf0\x9f\x8e\x88', 'balloon', 'balloon'),
            (b'\xf0\x9f\x97\xb3', 'ballot_box', 'ballot_box_vs16'),
            (b'\xe2\x98\x91', 'ballot_box_with_check', 'ballot_box_with_check_vs16'),
            (b'\xf0\x9f\x8e\x8d', 'bamboo', 'bamboo'),
            (b'\xf0\x9f\x8d\x8c', 'banana', 'banana'),
            (b'\xe2\x80\xbc', 'bangbang', 'bangbang_vs16'),
            (b'\xf0\x9f\x8f\xa6', 'bank', 'bank'),
            (b'\xf0\x9f\x93\x8a', 'bar_chart', 'bar_chart'),
            (b'\xf0\x9f\x92\x88', 'barber', 'barber'),
            (b'\xe2\x9a\xbe', 'baseball', 'baseball'),
            (b'\xf0\x9f\x8f\x80', 'basketball', 'basketball'),
            (b'\xe2\x9b\xb9', 'basketball_player', 'basketball_player_vs16'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbb', 'basketball_player_tone1', 'basketball_player_tone1', 'person_with_ball_tone1', 'person_bouncing_ball_tone1'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbc', 'basketball_player_tone2', 'basketball_player_tone2', 'person_with_ball_tone2', 'person_bouncing_ball_tone2'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbd', 'basketball_player_tone3', 'basketball_player_tone3', 'person_with_ball_tone3', 'person_bouncing_ball_tone3'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbe', 'basketball_player_tone4', 'basketball_player_tone4', 'person_with_ball_tone4', 'person_bouncing_ball_tone4'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbf', 'basketball_player_tone5', 'basketball_player_tone5', 'person_with_ball_tone5', 'person_bouncing_ball_tone5'),
            (b'\xf0\x9f\xa6\x87', 'bat', 'bat'),
            (b'\xf0\x9f\x9b\x80', 'bath', 'bath'),
            (b'\xf0\x9f\x9b\x80\xf0\x9f\x8f\xbb', 'bath_tone1', 'bath_tone1'),
            (b'\xf0\x9f\x9b\x80\xf0\x9f\x8f\xbc', 'bath_tone2', 'bath_tone2'),
            (b'\xf0\x9f\x9b\x80\xf0\x9f\x8f\xbd', 'bath_tone3', 'bath_tone3'),
            (b'\xf0\x9f\x9b\x80\xf0\x9f\x8f\xbe', 'bath_tone4', 'bath_tone4'),
            (b'\xf0\x9f\x9b\x80\xf0\x9f\x8f\xbf', 'bath_tone5', 'bath_tone5'),
            (b'\xf0\x9f\x9b\x81', 'bathtub', 'bathtub'),
            (b'\xf0\x9f\x94\x8b', 'battery', 'battery'),
            (b'\xf0\x9f\x8f\x96', 'beach', 'beach_vs16'),
            (b'\xe2\x9b\xb1', 'beach_umbrella', 'beach_umbrella_vs16'),
            (b'\xf0\x9f\x90\xbb', 'bear', 'bear'),
            (b'\xf0\x9f\x9b\x8f', 'bed', 'bed_vs16'),
            (b'\xf0\x9f\x90\x9d', 'bee', 'bee'),
            (b'\xf0\x9f\x8d\xba', 'beer', 'beer'),
            (b'\xf0\x9f\x8d\xbb', 'beers', 'beers'),
            (b'\xf0\x9f\x90\x9e', 'beetle', 'beetle'),
            (b'\xf0\x9f\x94\xb0', 'beginner', 'beginner'),
            (b'\xf0\x9f\x94\x94', 'bell', 'bell'),
            (b'\xf0\x9f\x9b\x8e', 'bellhop', 'bellhop_vs16'),
            (b'\xf0\x9f\x8d\xb1', 'bento', 'bento'),
            (b'\xf0\x9f\x9a\xb4', 'bicyclist', 'bicyclist', 'person_biking'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbb', 'bicyclist_tone1', 'bicyclist_tone1', 'person_biking_tone1'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbc', 'bicyclist_tone2', 'bicyclist_tone2', 'person_biking_tone2'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbd', 'bicyclist_tone3', 'bicyclist_tone3', 'person_biking_tone3'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbe', 'bicyclist_tone4', 'bicyclist_tone4', 'person_biking_tone4'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbf', 'bicyclist_tone5', 'bicyclist_tone5', 'person_biking_tone5'),
            (b'\xf0\x9f\x9a\xb2', 'bike', 'bike'),
            (b'\xf0\x9f\x91\x99', 'bikini', 'bikini'),
            (b'\xe2\x98\xa3', 'biohazard', 'biohazard_vs16'),
            (b'\xf0\x9f\x90\xa6', 'bird', 'bird'),
            (b'\xf0\x9f\x8e\x82', 'birthday', 'birthday'),
            (b'\xe2\x9a\xab', 'black_circle', 'black_circle'),
            (b'\xf0\x9f\x96\xa4', 'black_heart', 'black_heart'),
            (b'\xf0\x9f\x83\x8f', 'black_joker', 'black_joker'),
            (b'\xe2\xac\x9b', 'black_large_square', 'black_large_square'),
            (b'\xe2\x97\xbe', 'black_medium_small_square', 'black_medium_small_square'),
            (b'\xe2\x97\xbc', 'black_medium_square', 'black_medium_square_vs16'),
            (b'\xe2\x9c\x92', 'black_nib', 'black_nib_vs16'),
            (b'\xe2\x96\xaa', 'black_small_square', 'black_small_square_vs16'),
            (b'\xf0\x9f\x94\xb2', 'black_square_button', 'black_square_button'),
            (b'\xf0\x9f\x8c\xbc', 'blossom', 'blossom'),
            (b'\xf0\x9f\x90\xa1', 'blowfish', 'blowfish'),
            (b'\xf0\x9f\x93\x98', 'blue_book', 'blue_book'),
            (b'\xf0\x9f\x9a\x99', 'blue_car', 'blue_car'),
            (b'\xf0\x9f\x92\x99', 'blue_heart', 'blue_heart'),
            (b'\xf0\x9f\x90\x97', 'boar', 'boar'),
            (b'\xf0\x9f\x92\xa3', 'bomb', 'bomb'),
            (b'\xf0\x9f\x93\x96', 'book', 'book'),
            (b'\xf0\x9f\x94\x96', 'bookmark', 'bookmark'),
            (b'\xf0\x9f\x93\x91', 'bookmark_tabs', 'bookmark_tabs'),
            (b'\xf0\x9f\x93\x9a', 'books', 'books'),
            (b'\xf0\x9f\x92\xa5', 'boom', 'boom'),
            (b'\xf0\x9f\x91\xa2', 'boot', 'boot'),
            (b'\xf0\x9f\x8d\xbe', 'bottle_with_popping_cork', 'bottle_with_popping_cork', 'champagne'),
            (b'\xf0\x9f\x92\x90', 'bouquet', 'bouquet'),
            (b'\xf0\x9f\x99\x87', 'bow', 'bow', 'person_bowing'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbb', 'bow_tone1', 'bow_tone1', 'person_bowing_tone1'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbc', 'bow_tone2', 'bow_tone2', 'person_bowing_tone2'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbd', 'bow_tone3', 'bow_tone3', 'person_bowing_tone3'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbe', 'bow_tone4', 'bow_tone4', 'person_bowing_tone4'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbf', 'bow_tone5', 'bow_tone5', 'person_bowing_tone5'),
            (b'\xf0\x9f\x8e\xb3', 'bowling', 'bowling'),
            (b'\xf0\x9f\xa5\x8a', 'boxing_glove', 'boxing_glove', 'boxing_gloves'),
            (b'\xf0\x9f\x91\xa6', 'boy', 'boy'),
            (b'\xf0\x9f\x91\xa6\xf0\x9f\x8f\xbb', 'boy_tone1', 'boy_tone1'),
            (b'\xf0\x9f\x91\xa6\xf0\x9f\x8f\xbc', 'boy_tone2', 'boy_tone2'),
            (b'\xf0\x9f\x91\xa6\xf0\x9f\x8f\xbd', 'boy_tone3', 'boy_tone3'),
            (b'\xf0\x9f\x91\xa6\xf0\x9f\x8f\xbe', 'boy_tone4', 'boy_tone4'),
            (b'\xf0\x9f\x91\xa6\xf0\x9f\x8f\xbf', 'boy_tone5', 'boy_tone5'),
            (b'\xf0\x9f\x8d\x9e', 'bread', 'bread'),
            (b'\xf0\x9f\x91\xb0', 'bride_with_veil', 'bride_with_veil', 'person_with_veil'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbb', 'bride_with_veil_tone1', 'bride_with_veil_tone1', 'bride_with_veil_tone1'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbc', 'bride_with_veil_tone2', 'bride_with_veil_tone2', 'bride_with_veil_tone2'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbd', 'bride_with_veil_tone3', 'bride_with_veil_tone3', 'bride_with_veil_tone3'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbe', 'bride_with_veil_tone4', 'bride_with_veil_tone4', 'bride_with_veil_tone4'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbf', 'bride_with_veil_tone5', 'bride_with_veil_tone5', 'bride_with_veil_tone5'),
            (b'\xf0\x9f\x8c\x89', 'bridge_at_night', 'bridge_at_night'),
            (b'\xf0\x9f\x92\xbc', 'briefcase', 'briefcase'),
            (b'\xf0\x9f\x92\x94', 'broken_heart', 'broken_heart', '</3', '<\\3'),
            (b'\xf0\x9f\x90\x9b', 'bug', 'bug'),
            (b'\xf0\x9f\x8f\x97', 'building_construction', 'building_construction_vs16'),
            (b'\xf0\x9f\x92\xa1', 'bulb', 'bulb'),
            (b'\xf0\x9f\x9a\x85', 'bullettrain_front', 'bullettrain_front'),
            (b'\xf0\x9f\x9a\x84', 'bullettrain_side', 'bullettrain_side'),
            (b'\xf0\x9f\x8c\xaf', 'burrito', 'burrito'),
            (b'\xf0\x9f\x9a\x8c', 'bus', 'bus'),
            (b'\xf0\x9f\x9a\x8f', 'busstop', 'busstop'),
            (b'\xf0\x9f\x91\xa4', 'bust_in_silhouette', 'bust_in_silhouette'),
            (b'\xf0\x9f\x91\xa5', 'busts_in_silhouette', 'busts_in_silhouette'),
            (b'\xf0\x9f\xa6\x8b', 'butterfly', 'butterfly'),
            (b'\xf0\x9f\x8c\xb5', 'cactus', 'cactus'),
            (b'\xf0\x9f\x8d\xb0', 'cake', 'cake'),
            (b'\xf0\x9f\x93\x86', 'calendar', 'calendar'),
            (b'\xf0\x9f\x97\x93', 'calendar_spiral', 'calendar_spiral_vs16'),
            (b'\xf0\x9f\xa4\x99', 'call_me', 'call_me', 'call_me_hand'),
            (b'\xf0\x9f\xa4\x99\xf0\x9f\x8f\xbb', 'call_me_tone1', 'call_me_tone1', 'call_me_hand_tone1'),
            (b'\xf0\x9f\xa4\x99\xf0\x9f\x8f\xbc', 'call_me_tone2', 'call_me_tone2', 'call_me_hand_tone2'),
            (b'\xf0\x9f\xa4\x99\xf0\x9f\x8f\xbd', 'call_me_tone3', 'call_me_tone3', 'call_me_hand_tone3'),
            (b'\xf0\x9f\xa4\x99\xf0\x9f\x8f\xbe', 'call_me_tone4', 'call_me_tone4', 'call_me_hand_tone4'),
            (b'\xf0\x9f\xa4\x99\xf0\x9f\x8f\xbf', 'call_me_tone5', 'call_me_tone5', 'call_me_hand_tone5'),
            (b'\xf0\x9f\x93\xb2', 'calling', 'calling'),
            (b'\xf0\x9f\x90\xab', 'camel', 'camel'),
            (b'\xf0\x9f\x93\xb7', 'camera', 'camera'),
            (b'\xf0\x9f\x93\xb8', 'camera_with_flash', 'camera_with_flash'),
            (b'\xf0\x9f\x8f\x95', 'camping', 'camping_vs16'),
            (b'\xe2\x99\x8b', 'cancer', 'cancer'),
            (b'\xf0\x9f\x95\xaf', 'candle', 'candle_vs16'),
            (b'\xf0\x9f\x8d\xac', 'candy', 'candy'),
            (b'\xf0\x9f\x9b\xb6', 'canoe', 'canoe', 'kayak'),
            (b'\xf0\x9f\x94\xa0', 'capital_abcd', 'capital_abcd'),
            (b'\xe2\x99\x91', 'capricorn', 'capricorn'),
            (b'\xf0\x9f\x97\x83', 'card_box', 'card_box_vs16'),
            (b'\xf0\x9f\x93\x87', 'card_index', 'card_index'),
            (b'\xf0\x9f\x97\x82', 'card_index_dividers', 'card_index_dividers_vs16'),
            (b'\xf0\x9f\x8e\xa0', 'carousel_horse', 'carousel_horse'),
            (b'\xf0\x9f\xa5\x95', 'carrot', 'carrot'),
            (b'\xf0\x9f\xa4\xb8', 'cartwheel', 'cartwheel', 'person_doing_cartwheel'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbb', 'cartwheel_tone1', 'cartwheel_tone1', 'person_doing_cartwheel_tone1'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbc', 'cartwheel_tone2', 'cartwheel_tone2', 'person_doing_cartwheel_tone2'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbd', 'cartwheel_tone3', 'cartwheel_tone3', 'person_doing_cartwheel_tone3'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbe', 'cartwheel_tone4', 'cartwheel_tone4', 'person_doing_cartwheel_tone4'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbf', 'cartwheel_tone5', 'cartwheel_tone5', 'person_doing_cartwheel_tone5'),
            (b'\xf0\x9f\x90\x88', 'cat2', 'cat2'),
            (b'\xf0\x9f\x90\xb1', 'cat', 'cat'),
            (b'\xf0\x9f\x92\xbf', 'cd', 'cd'),
            (b'\xe2\x9b\x93', 'chains', 'chains_vs16'),
            (b'\xf0\x9f\xa5\x82', 'champagne_glass', 'champagne_glass', 'clinking_glass'),
            (b'\xf0\x9f\x92\xb9', 'chart', 'chart'),
            (b'\xf0\x9f\x93\x89', 'chart_with_downwards_trend', 'chart_with_downwards_trend'),
            (b'\xf0\x9f\x93\x88', 'chart_with_upwards_trend', 'chart_with_upwards_trend'),
            (b'\xf0\x9f\x8f\x81', 'checkered_flag', 'checkered_flag'),
            (b'\xf0\x9f\xa7\x80', 'cheese', 'cheese', 'cheese_wedge'),
            (b'\xf0\x9f\x8d\x92', 'cherries', 'cherries'),
            (b'\xf0\x9f\x8c\xb8', 'cherry_blossom', 'cherry_blossom'),
            (b'\xf0\x9f\x8c\xb0', 'chestnut', 'chestnut'),
            (b'\xf0\x9f\x90\x94', 'chicken', 'chicken'),
            (b'\xf0\x9f\x9a\xb8', 'children_crossing', 'children_crossing'),
            (b'\xf0\x9f\x90\xbf', 'chipmunk', 'chipmunk_vs16'),
            (b'\xf0\x9f\x8d\xab', 'chocolate_bar', 'chocolate_bar'),
            (b'\xf0\x9f\x8e\x84', 'christmas_tree', 'christmas_tree'),
            (b'\xe2\x9b\xaa', 'church', 'church'),
            (b'\xf0\x9f\x8e\xa6', 'cinema', 'cinema'),
            (b'\xf0\x9f\x8e\xaa', 'circus_tent', 'circus_tent'),
            (b'\xf0\x9f\x8c\x86', 'city_dusk', 'city_dusk'),
            (b'\xf0\x9f\x8c\x87', 'city_sunrise', 'city_sunrise', 'city_sunset'),
            (b'\xf0\x9f\x8f\x99', 'cityscape', 'cityscape_vs16'),
            (b'\xf0\x9f\x86\x91', 'cl', 'cl'),
            (b'\xf0\x9f\x91\x8f', 'clap', 'clap'),
            (b'\xf0\x9f\x91\x8f\xf0\x9f\x8f\xbb', 'clap_tone1', 'clap_tone1'),
            (b'\xf0\x9f\x91\x8f\xf0\x9f\x8f\xbc', 'clap_tone2', 'clap_tone2'),
            (b'\xf0\x9f\x91\x8f\xf0\x9f\x8f\xbd', 'clap_tone3', 'clap_tone3'),
            (b'\xf0\x9f\x91\x8f\xf0\x9f\x8f\xbe', 'clap_tone4', 'clap_tone4'),
            (b'\xf0\x9f\x91\x8f\xf0\x9f\x8f\xbf', 'clap_tone5', 'clap_tone5'),
            (b'\xf0\x9f\x8e\xac', 'clapper', 'clapper'),
            (b'\xf0\x9f\x8f\x9b', 'classical_building', 'classical_building_vs16'),
            (b'\xf0\x9f\x93\x8b', 'clipboard', 'clipboard'),
            (b'\xf0\x9f\x95\xa5', 'clock1030', 'clock1030'),
            (b'\xf0\x9f\x95\x99', 'clock10', 'clock10'),
            (b'\xf0\x9f\x95\xa6', 'clock1130', 'clock1130'),
            (b'\xf0\x9f\x95\x9a', 'clock11', 'clock11'),
            (b'\xf0\x9f\x95\xa7', 'clock1230', 'clock1230'),
            (b'\xf0\x9f\x95\x9b', 'clock12', 'clock12'),
            (b'\xf0\x9f\x95\x9c', 'clock130', 'clock130'),
            (b'\xf0\x9f\x95\x90', 'clock1', 'clock1'),
            (b'\xf0\x9f\x95\x9d', 'clock230', 'clock230'),
            (b'\xf0\x9f\x95\x91', 'clock2', 'clock2'),
            (b'\xf0\x9f\x95\x9e', 'clock330', 'clock330'),
            (b'\xf0\x9f\x95\x92', 'clock3', 'clock3'),
            (b'\xf0\x9f\x95\x9f', 'clock430', 'clock430'),
            (b'\xf0\x9f\x95\x93', 'clock4', 'clock4'),
            (b'\xf0\x9f\x95\xa0', 'clock530', 'clock530'),
            (b'\xf0\x9f\x95\x94', 'clock5', 'clock5'),
            (b'\xf0\x9f\x95\xa1', 'clock630', 'clock630'),
            (b'\xf0\x9f\x95\x95', 'clock6', 'clock6'),
            (b'\xf0\x9f\x95\xa2', 'clock730', 'clock730'),
            (b'\xf0\x9f\x95\x96', 'clock7', 'clock7'),
            (b'\xf0\x9f\x95\xa3', 'clock830', 'clock830'),
            (b'\xf0\x9f\x95\x97', 'clock8', 'clock8'),
            (b'\xf0\x9f\x95\xa4', 'clock930', 'clock930'),
            (b'\xf0\x9f\x95\x98', 'clock9', 'clock9'),
            (b'\xf0\x9f\x95\xb0', 'clock', 'clock_vs16'),
            (b'\xf0\x9f\x93\x95', 'closed_book', 'closed_book'),
            (b'\xf0\x9f\x94\x90', 'closed_lock_with_key', 'closed_lock_with_key'),
            (b'\xf0\x9f\x8c\x82', 'closed_umbrella', 'closed_umbrella'),
            (b'\xe2\x98\x81', 'cloud', 'cloud_vs16'),
            (b'\xf0\x9f\x8c\xa9', 'cloud_lightning', 'cloud_lightning_vs16'),
            (b'\xf0\x9f\x8c\xa7', 'cloud_rain', 'cloud_rain_vs16'),
            (b'\xf0\x9f\x8c\xa8', 'cloud_snow', 'cloud_snow_vs16'),
            (b'\xf0\x9f\x8c\xaa', 'cloud_tornado', 'cloud_tornado_vs16'),
            (b'\xf0\x9f\xa4\xa1', 'clown', 'clown', 'clown_face'),
            (b'\xe2\x99\xa3', 'clubs', 'clubs_vs16'),
            (b'\xf0\x9f\x8d\xb8', 'cocktail', 'cocktail'),
            (b'\xe2\x98\x95', 'coffee', 'coffee'),
            (b'\xe2\x9a\xb0', 'coffin', 'coffin_vs16'),
            (b'\xf0\x9f\x98\xb0', 'cold_sweat', 'cold_sweat'),
            (b'\xe2\x98\x84', 'comet', 'comet_vs16'),
            (b'\xf0\x9f\x97\x9c', 'compression', 'compression_vs16'),
            (b'\xf0\x9f\x92\xbb', 'computer', 'computer'),
            (b'\xf0\x9f\x8e\x8a', 'confetti_ball', 'confetti_ball'),
            (b'\xf0\x9f\x98\x96', 'confounded', 'confounded'),
            (b'\xe3\x8a\x97', 'congratulations', 'congratulations_vs16'),
            (b'\xf0\x9f\x9a\xa7', 'construction', 'construction'),
            (b'\xf0\x9f\x91\xb7', 'construction_worker', 'construction_worker'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbb', 'construction_worker_tone1', 'construction_worker_tone1'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbc', 'construction_worker_tone2', 'construction_worker_tone2'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbd', 'construction_worker_tone3', 'construction_worker_tone3'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbe', 'construction_worker_tone4', 'construction_worker_tone4'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbf', 'construction_worker_tone5', 'construction_worker_tone5'),
            (b'\xf0\x9f\x8e\x9b', 'control_knobs', 'control_knobs_vs16'),
            (b'\xf0\x9f\x8f\xaa', 'convenience_store', 'convenience_store'),
            (b'\xf0\x9f\x8d\xaa', 'cookie', 'cookie'),
            (b'\xf0\x9f\x8d\xb3', 'cooking', 'cooking'),
            (b'\xf0\x9f\x86\x92', 'cool', 'cool'),
            (b'\xf0\x9f\x91\xae', 'cop', 'cop', 'police_officer'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbb', 'cop_tone1', 'cop_tone1', 'police_officer_tone1'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbc', 'cop_tone2', 'cop_tone2', 'police_officer_tone2'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbd', 'cop_tone3', 'cop_tone3', 'police_officer_tone3'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbe', 'cop_tone4', 'cop_tone4', 'police_officer_tone4'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbf', 'cop_tone5', 'cop_tone5', 'police_officer_tone5'),
            (b'\xc2\xa9', 'copyright', 'copyright_vs16'),
            (b'\xf0\x9f\x8c\xbd', 'corn', 'corn'),
            (b'\xf0\x9f\x9b\x8b', 'couch', 'couch_vs16'),
            (b'\xf0\x9f\x91\xab', 'couple', 'couple'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xe2\x9d\xa4\xef\xb8\x8f\xe2\x80\x8d\xf0\x9f\x91\xa8', 'couple_mm', 'couple_mm', 'couple_with_heart_mm'),
            (b'\xf0\x9f\x92\x91', 'couple_with_heart', 'couple_with_heart'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xe2\x9d\xa4\xef\xb8\x8f\xe2\x80\x8d\xf0\x9f\x91\xa9', 'couple_with_heart_ww', 'couple_with_heart_ww', 'couple_ww'),
            (b'\xf0\x9f\x92\x8f', 'couplekiss', 'couplekiss'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xe2\x9d\xa4\xef\xb8\x8f\xe2\x80\x8d\xf0\x9f\x92\x8b\xe2\x80\x8d\xf0\x9f\x91\xa8', 'couplekiss_mm', 'couplekiss_mm', 'kiss_mm'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xe2\x9d\xa4\xef\xb8\x8f\xe2\x80\x8d\xf0\x9f\x92\x8b\xe2\x80\x8d\xf0\x9f\x91\xa9', 'couplekiss_ww', 'couplekiss_ww', 'kiss_ww'),
            (b'\xf0\x9f\x90\x84', 'cow2', 'cow2'),
            (b'\xf0\x9f\x90\xae', 'cow', 'cow'),
            (b'\xf0\x9f\xa4\xa0', 'cowboy', 'cowboy', 'face_with_cowboy_hat'),
            (b'\xf0\x9f\xa6\x80', 'crab', 'crab'),
            (b'\xf0\x9f\x96\x8d', 'crayon', 'crayon_vs16'),
            (b'\xf0\x9f\x92\xb3', 'credit_card', 'credit_card'),
            (b'\xf0\x9f\x8c\x99', 'crescent_moon', 'crescent_moon'),
            (b'\xf0\x9f\x8f\x8f', 'cricket', 'cricket_vs16'),
            (b'\xf0\x9f\x90\x8a', 'crocodile', 'crocodile'),
            (b'\xf0\x9f\xa5\x90', 'croissant', 'croissant'),
            (b'\xe2\x9c\x9d', 'cross', 'cross_vs16'),
            (b'\xf0\x9f\x8e\x8c', 'crossed_flags', 'crossed_flags'),
            (b'\xe2\x9a\x94', 'crossed_swords', 'crossed_swords_vs16'),
            (b'\xf0\x9f\x91\x91', 'crown', 'crown'),
            (b'\xf0\x9f\x9b\xb3', 'cruise_ship', 'cruise_ship_vs16'),
            (b'\xf0\x9f\x98\xbf', 'crying_cat_face', 'crying_cat_face'),
            (b'\xf0\x9f\x94\xae', 'crystal_ball', 'crystal_ball'),
            (b'\xf0\x9f\xa5\x92', 'cucumber', 'cucumber'),
            (b'\xf0\x9f\x92\x98', 'cupid', 'cupid'),
            (b'\xe2\x9e\xb0', 'curly_loop', 'curly_loop'),
            (b'\xf0\x9f\x92\xb1', 'currency_exchange', 'currency_exchange'),
            (b'\xf0\x9f\x8d\x9b', 'curry', 'curry'),
            (b'\xf0\x9f\x8d\xae', 'custard', 'custard', 'flan', 'pudding'),
            (b'\xf0\x9f\x9b\x83', 'customs', 'customs'),
            (b'\xf0\x9f\x8c\x80', 'cyclone', 'cyclone'),
            (b'\xf0\x9f\x97\xa1', 'dagger', 'dagger_vs16'),
            (b'\xf0\x9f\x92\x83', 'dancer', 'dancer'),
            (b'\xf0\x9f\x92\x83\xf0\x9f\x8f\xbb', 'dancer_tone1', 'dancer_tone1'),
            (b'\xf0\x9f\x92\x83\xf0\x9f\x8f\xbc', 'dancer_tone2', 'dancer_tone2'),
            (b'\xf0\x9f\x92\x83\xf0\x9f\x8f\xbd', 'dancer_tone3', 'dancer_tone3'),
            (b'\xf0\x9f\x92\x83\xf0\x9f\x8f\xbe', 'dancer_tone4', 'dancer_tone4'),
            (b'\xf0\x9f\x92\x83\xf0\x9f\x8f\xbf', 'dancer_tone5', 'dancer_tone5'),
            (b'\xf0\x9f\x91\xaf', 'dancers', 'dancers', 'people_with_bunny_ears_partying'),
            (b'\xf0\x9f\x8d\xa1', 'dango', 'dango'),
            (b'\xf0\x9f\x95\xb6', 'dark_sunglasses', 'dark_sunglasses_vs16'),
            (b'\xf0\x9f\x8e\xaf', 'dart', 'dart'),
            (b'\xf0\x9f\x92\xa8', 'dash', 'dash'),
            (b'\xf0\x9f\x93\x85', 'date', 'date'),
            (b'\xf0\x9f\x8c\xb3', 'deciduous_tree', 'deciduous_tree'),
            (b'\xf0\x9f\xa6\x8c', 'deer', 'deer'),
            (b'\xf0\x9f\x8f\xac', 'department_store', 'department_store'),
            (b'\xf0\x9f\x8f\x9a', 'derelict_house_building', 'derelict_house_building_vs16'),
            (b'\xf0\x9f\x8f\x9c', 'desert', 'desert_vs16'),
            (b'\xf0\x9f\x8f\x9d', 'desert_island', 'desert_island_vs16'),
            (b'\xf0\x9f\x96\xa5', 'desktop', 'desktop_vs16'),
            (b'\xf0\x9f\x92\xa0', 'diamond_shape_with_a_dot_inside', 'diamond_shape_with_a_dot_inside'),
            (b'\xe2\x99\xa6', 'diamonds', 'diamonds_vs16'),
            (b'\xf0\x9f\x98\x9e', 'disappointed', 'disappointed'),
            (b'\xf0\x9f\x98\xa5', 'disappointed_relieved', 'disappointed_relieved'),
            (b'\xf0\x9f\x92\xab', 'dizzy', 'dizzy'),
            (b'\xf0\x9f\x98\xb5', 'dizzy_face', 'dizzy_face'),
            (b'\xf0\x9f\x9a\xaf', 'do_not_litter', 'do_not_litter'),
            (b'\xf0\x9f\x90\x95', 'dog2', 'dog2'),
            (b'\xf0\x9f\x90\xb6', 'dog', 'dog'),
            (b'\xf0\x9f\x92\xb5', 'dollar', 'dollar'),
            (b'\xf0\x9f\x8e\x8e', 'dolls', 'dolls'),
            (b'\xf0\x9f\x90\xac', 'dolphin', 'dolphin'),
            (b'\xf0\x9f\x9a\xaa', 'door', 'door'),
            (b'\xe2\x8f\xb8', 'double_vertical_bar', 'double_vertical_bar_vs16'),
            (b'\xf0\x9f\x8d\xa9', 'doughnut', 'doughnut'),
            (b'\xf0\x9f\x95\x8a', 'dove', 'dove_vs16'),
            (b'\xf0\x9f\x90\x89', 'dragon', 'dragon'),
            (b'\xf0\x9f\x90\xb2', 'dragon_face', 'dragon_face'),
            (b'\xf0\x9f\x91\x97', 'dress', 'dress'),
            (b'\xf0\x9f\x90\xaa', 'dromedary_camel', 'dromedary_camel'),
            (b'\xf0\x9f\xa4\xa4', 'drool', 'drool', 'drooling_face'),
            (b'\xf0\x9f\x92\xa7', 'droplet', 'droplet'),
            (b'\xf0\x9f\xa5\x81', 'drum', 'drum', 'drum_with_drumsticks'),
            (b'\xf0\x9f\xa6\x86', 'duck', 'duck'),
            (b'\xf0\x9f\x93\x80', 'dvd', 'dvd'),
            (b'\xf0\x9f\x93\xa7', 'e_mail', 'e_mail', 'email'),
            (b'\xf0\x9f\xa6\x85', 'eagle', 'eagle'),
            (b'\xf0\x9f\x91\x82', 'ear', 'ear'),
            (b'\xf0\x9f\x91\x82\xf0\x9f\x8f\xbb', 'ear_tone1', 'ear_tone1'),
            (b'\xf0\x9f\x91\x82\xf0\x9f\x8f\xbc', 'ear_tone2', 'ear_tone2'),
            (b'\xf0\x9f\x91\x82\xf0\x9f\x8f\xbd', 'ear_tone3', 'ear_tone3'),
            (b'\xf0\x9f\x91\x82\xf0\x9f\x8f\xbe', 'ear_tone4', 'ear_tone4'),
            (b'\xf0\x9f\x91\x82\xf0\x9f\x8f\xbf', 'ear_tone5', 'ear_tone5'),
            (b'\xf0\x9f\x8c\xbe', 'ear_of_rice', 'ear_of_rice'),
            (b'\xf0\x9f\x8c\x8d', 'earth_africa', 'earth_africa'),
            (b'\xf0\x9f\x8c\x8e', 'earth_americas', 'earth_americas'),
            (b'\xf0\x9f\x8c\x8f', 'earth_asia', 'earth_asia'),
            (b'\xf0\x9f\xa5\x9a', 'egg', 'egg'),
            (b'\xf0\x9f\x8d\x86', 'eggplant', 'eggplant'),
            (b'8\xe2\x83\xa3', 'eight', 'eight_vs16'),
            (b'\xe2\x9c\xb4', 'eight_pointed_black_star', 'eight_pointed_black_star_vs16'),
            (b'\xe2\x9c\xb3', 'eight_spoked_asterisk', 'eight_spoked_asterisk_vs16'),
            (b'\xe2\x8f\x8f', 'eject', 'eject_vs16'),
            (b'\xf0\x9f\x94\x8c', 'electric_plug', 'electric_plug'),
            (b'\xf0\x9f\x90\x98', 'elephant', 'elephant'),
            (b'\xf0\x9f\x94\x9a', 'end', 'end'),
            (b'\xe2\x9c\x89', 'envelope', 'envelope_vs16'),
            (b'\xf0\x9f\x93\xa9', 'envelope_with_arrow', 'envelope_with_arrow'),
            (b'\xf0\x9f\x92\xb6', 'euro', 'euro'),
            (b'\xf0\x9f\x8f\xb0', 'european_castle', 'european_castle'),
            (b'\xf0\x9f\x8f\xa4', 'european_post_office', 'european_post_office'),
            (b'\xf0\x9f\x8c\xb2', 'evergreen_tree', 'evergreen_tree'),
            (b'\xe2\x9d\x97', 'exclamation', 'exclamation'),
            (b'\xf0\x9f\xa4\xb0', 'expecting_woman', 'expecting_woman', 'pregnant_woman'),
            (b'\xf0\x9f\xa4\xb0\xf0\x9f\x8f\xbb', 'expecting_woman_tone1', 'expecting_woman_tone1', 'pregnant_woman_tone1'),
            (b'\xf0\x9f\xa4\xb0\xf0\x9f\x8f\xbc', 'expecting_woman_tone2', 'expecting_woman_tone2', 'pregnant_woman_tone2'),
            (b'\xf0\x9f\xa4\xb0\xf0\x9f\x8f\xbd', 'expecting_woman_tone3', 'expecting_woman_tone3', 'pregnant_woman_tone3'),
            (b'\xf0\x9f\xa4\xb0\xf0\x9f\x8f\xbe', 'expecting_woman_tone4', 'expecting_woman_tone4', 'pregnant_woman_tone4'),
            (b'\xf0\x9f\xa4\xb0\xf0\x9f\x8f\xbf', 'expecting_woman_tone5', 'expecting_woman_tone5', 'pregnant_woman_tone5'),
            (b'\xf0\x9f\x98\x91', 'expressionless', 'expressionless'),
            (b'\xf0\x9f\x91\x81', 'eye', 'eye_vs16'),
            (b'\xf0\x9f\x91\x81\xe2\x80\x8d\xf0\x9f\x97\xa8', 'eye_in_speech_bubble', 'eye_in_speech_bubble'),
            (b'\xf0\x9f\x91\x93', 'eyeglasses', 'eyeglasses'),
            (b'\xf0\x9f\x91\x80', 'eyes', 'eyes'),
            (b'\xf0\x9f\xa4\xa6', 'face_palm', 'face_palm', 'facepalm', 'person_facepalming'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbb', 'face_palm_tone1', 'face_palm_tone1', 'facepalm_tone1', 'person_facepalming_tone1'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbc', 'face_palm_tone2', 'face_palm_tone2', 'facepalm_tone2', 'person_facepalming_tone2'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbd', 'face_palm_tone3', 'face_palm_tone3', 'facepalm_tone3', 'person_facepalming_tone3'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbe', 'face_palm_tone4', 'face_palm_tone4', 'facepalm_tone4', 'person_facepalming_tone4'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbf', 'face_palm_tone5', 'face_palm_tone5', 'facepalm_tone5', 'person_facepalming_tone5'),
            (b'\xf0\x9f\xa4\x95', 'face_with_head_bandage', 'face_with_head_bandage', 'head_bandage'),
            (b'\xf0\x9f\x99\x84', 'face_with_rolling_eyes', 'face_with_rolling_eyes', 'rolling_eyes'),
            (b'\xf0\x9f\xa4\x92', 'face_with_thermometer', 'face_with_thermometer', 'thermometer_face'),
            (b'\xf0\x9f\x8f\xad', 'factory', 'factory'),
            (b'\xf0\x9f\x8d\x82', 'fallen_leaf', 'fallen_leaf'),
            (b'\xf0\x9f\x91\xaa', 'family', 'family'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_mmb', 'family_mmb'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa6\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_mmbb', 'family_mmbb'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa7', 'family_mmg', 'family_mmg'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa7\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_mmgb', 'family_mmgb'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa7\xe2\x80\x8d\xf0\x9f\x91\xa7', 'family_mmgg', 'family_mmgg'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa6\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_mwbb', 'family_mwbb'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa7', 'family_mwg', 'family_mwg'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa7\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_mwgb', 'family_mwgb'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa7\xe2\x80\x8d\xf0\x9f\x91\xa7', 'family_mwgg', 'family_mwgg'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_wwb', 'family_wwb'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa6\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_wwbb', 'family_wwbb'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa7', 'family_wwg', 'family_wwg'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa7\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_wwgb', 'family_wwgb'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa7\xe2\x80\x8d\xf0\x9f\x91\xa7', 'family_wwgg', 'family_wwgg'),
            (b'\xe2\x8f\xa9', 'fast_forward', 'fast_forward'),
            (b'\xf0\x9f\x93\xa0', 'fax', 'fax'),
            (b'\xf0\x9f\x98\xa8', 'fearful', 'fearful'),
            (b'\xf0\x9f\x90\xbe', 'feet', 'feet', 'paw_prints'),
            (b'\xf0\x9f\xa4\xba', 'fencer', 'fencer', 'fencing', 'person_fencing'),
            (b'\xf0\x9f\x8e\xa1', 'ferris_wheel', 'ferris_wheel'),
            (b'\xe2\x9b\xb4', 'ferry', 'ferry_vs16'),
            (b'\xf0\x9f\x8f\x91', 'field_hockey', 'field_hockey'),
            (b'\xf0\x9f\x97\x84', 'file_cabinet', 'file_cabinet_vs16'),
            (b'\xf0\x9f\x93\x81', 'file_folder', 'file_folder'),
            (b'\xf0\x9f\x8e\x9e', 'film_frames', 'film_frames_vs16'),
            (b'\xf0\x9f\x93\xbd', 'film_projector', 'film_projector_vs16'),
            (b'\xf0\x9f\xa4\x9e', 'fingers_crossed', 'fingers_crossed', 'hand_with_index_and_middle_finger_crossed'),
            (b'\xf0\x9f\xa4\x9e\xf0\x9f\x8f\xbb', 'fingers_crossed_tone1', 'fingers_crossed_tone1', 'hand_with_index_and_middle_finger_crossed_tone1', 'hand_with_index_and_middle_fingers_crossed_tone1'),
            (b'\xf0\x9f\xa4\x9e\xf0\x9f\x8f\xbc', 'fingers_crossed_tone2', 'fingers_crossed_tone2', 'hand_with_index_and_middle_finger_crossed_tone2', 'hand_with_index_and_middle_fingers_crossed_tone2'),
            (b'\xf0\x9f\xa4\x9e\xf0\x9f\x8f\xbd', 'fingers_crossed_tone3', 'fingers_crossed_tone3', 'hand_with_index_and_middle_finger_crossed_tone3', 'hand_with_index_and_middle_fingers_crossed_tone3'),
            (b'\xf0\x9f\xa4\x9e\xf0\x9f\x8f\xbe', 'fingers_crossed_tone4', 'fingers_crossed_tone4', 'hand_with_index_and_middle_finger_crossed_tone4', 'hand_with_index_and_middle_fingers_crossed_tone4'),
            (b'\xf0\x9f\xa4\x9e\xf0\x9f\x8f\xbf', 'fingers_crossed_tone5', 'fingers_crossed_tone5', 'hand_with_index_and_middle_finger_crossed_tone5', 'hand_with_index_and_middle_fingers_crossed_tone5'),
            (b'\xf0\x9f\x94\xa5', 'fire', 'fire', 'flame'),
            (b'\xf0\x9f\x9a\x92', 'fire_engine', 'fire_engine'),
            (b'\xf0\x9f\x8e\x86', 'fireworks', 'fireworks'),
            (b'\xf0\x9f\xa5\x87', 'first_place', 'first_place', 'first_place_medal'),
            (b'\xf0\x9f\x8c\x93', 'first_quarter_moon', 'first_quarter_moon'),
            (b'\xf0\x9f\x8c\x9b', 'first_quarter_moon_with_face', 'first_quarter_moon_with_face'),
            (b'\xf0\x9f\x90\x9f', 'fish', 'fish'),
            (b'\xf0\x9f\x8d\xa5', 'fish_cake', 'fish_cake'),
            (b'\xf0\x9f\x8e\xa3', 'fishing_pole_and_fish', 'fishing_pole_and_fish'),
            (b'\xe2\x9c\x8a', 'fist', 'fist'),
            (b'\xe2\x9c\x8a\xf0\x9f\x8f\xbb', 'fist_tone1', 'fist_tone1'),
            (b'\xe2\x9c\x8a\xf0\x9f\x8f\xbc', 'fist_tone2', 'fist_tone2'),
            (b'\xe2\x9c\x8a\xf0\x9f\x8f\xbd', 'fist_tone3', 'fist_tone3'),
            (b'\xe2\x9c\x8a\xf0\x9f\x8f\xbe', 'fist_tone4', 'fist_tone4'),
            (b'\xe2\x9c\x8a\xf0\x9f\x8f\xbf', 'fist_tone5', 'fist_tone5'),
            (b'5\xe2\x83\xa3', 'five', 'five_vs16'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xa8', 'flag_ac', 'flag_ac'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xa9', 'flag_ad', 'flag_ad'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xaa', 'flag_ae', 'flag_ae'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xab', 'flag_af', 'flag_af'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xac', 'flag_ag', 'flag_ag'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xae', 'flag_ai', 'flag_ai'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xb1', 'flag_al', 'flag_al'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xb2', 'flag_am', 'flag_am'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xb4', 'flag_ao', 'flag_ao'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xb6', 'flag_aq', 'flag_aq'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xb7', 'flag_ar', 'flag_ar'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xb8', 'flag_as', 'flag_as'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xb9', 'flag_at', 'flag_at'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xba', 'flag_au', 'flag_au'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xbc', 'flag_aw', 'flag_aw'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xbd', 'flag_ax', 'flag_ax'),
            (b'\xf0\x9f\x87\xa6\xf0\x9f\x87\xbf', 'flag_az', 'flag_az'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xa6', 'flag_ba', 'flag_ba'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xa7', 'flag_bb', 'flag_bb'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xa9', 'flag_bd', 'flag_bd'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xaa', 'flag_be', 'flag_be'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xab', 'flag_bf', 'flag_bf'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xac', 'flag_bg', 'flag_bg'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xad', 'flag_bh', 'flag_bh'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xae', 'flag_bi', 'flag_bi'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xaf', 'flag_bj', 'flag_bj'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xb1', 'flag_bl', 'flag_bl'),
            (b'\xf0\x9f\x8f\xb4', 'flag_black', 'flag_black'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xb2', 'flag_bm', 'flag_bm'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xb3', 'flag_bn', 'flag_bn'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xb4', 'flag_bo', 'flag_bo'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xb6', 'flag_bq', 'flag_bq'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xb7', 'flag_br', 'flag_br'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xb8', 'flag_bs', 'flag_bs'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xb9', 'flag_bt', 'flag_bt'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xbb', 'flag_bv', 'flag_bv'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xbc', 'flag_bw', 'flag_bw'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xbe', 'flag_by', 'flag_by'),
            (b'\xf0\x9f\x87\xa7\xf0\x9f\x87\xbf', 'flag_bz', 'flag_bz'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xa6', 'flag_ca', 'flag_ca'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xa8', 'flag_cc', 'flag_cc'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xa9', 'flag_cd', 'flag_cd'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xab', 'flag_cf', 'flag_cf'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xac', 'flag_cg', 'flag_cg'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xad', 'flag_ch', 'flag_ch'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xae', 'flag_ci', 'flag_ci'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xb0', 'flag_ck', 'flag_ck'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xb1', 'flag_cl', 'flag_cl'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xb2', 'flag_cm', 'flag_cm'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xb3', 'flag_cn', 'flag_cn'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xb4', 'flag_co', 'flag_co'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xb5', 'flag_cp', 'flag_cp'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xb7', 'flag_cr', 'flag_cr'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xba', 'flag_cu', 'flag_cu'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xbb', 'flag_cv', 'flag_cv'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xbc', 'flag_cw', 'flag_cw'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xbd', 'flag_cx', 'flag_cx'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xbe', 'flag_cy', 'flag_cy'),
            (b'\xf0\x9f\x87\xa8\xf0\x9f\x87\xbf', 'flag_cz', 'flag_cz'),
            (b'\xf0\x9f\x87\xa9\xf0\x9f\x87\xaa', 'flag_de', 'flag_de'),
            (b'\xf0\x9f\x87\xa9\xf0\x9f\x87\xac', 'flag_dg', 'flag_dg'),
            (b'\xf0\x9f\x87\xa9\xf0\x9f\x87\xaf', 'flag_dj', 'flag_dj'),
            (b'\xf0\x9f\x87\xa9\xf0\x9f\x87\xb0', 'flag_dk', 'flag_dk'),
            (b'\xf0\x9f\x87\xa9\xf0\x9f\x87\xb2', 'flag_dm', 'flag_dm'),
            (b'\xf0\x9f\x87\xa9\xf0\x9f\x87\xb4', 'flag_do', 'flag_do'),
            (b'\xf0\x9f\x87\xa9\xf0\x9f\x87\xbf', 'flag_dz', 'flag_dz'),
            (b'\xf0\x9f\x87\xaa\xf0\x9f\x87\xa6', 'flag_ea', 'flag_ea'),
            (b'\xf0\x9f\x87\xaa\xf0\x9f\x87\xa8', 'flag_ec', 'flag_ec'),
            (b'\xf0\x9f\x87\xaa\xf0\x9f\x87\xaa', 'flag_ee', 'flag_ee'),
            (b'\xf0\x9f\x87\xaa\xf0\x9f\x87\xac', 'flag_eg', 'flag_eg'),
            (b'\xf0\x9f\x87\xaa\xf0\x9f\x87\xad', 'flag_eh', 'flag_eh'),
            (b'\xf0\x9f\x87\xaa\xf0\x9f\x87\xb7', 'flag_er', 'flag_er'),
            (b'\xf0\x9f\x87\xaa\xf0\x9f\x87\xb8', 'flag_es', 'flag_es'),
            (b'\xf0\x9f\x87\xaa\xf0\x9f\x87\xb9', 'flag_et', 'flag_et'),
            (b'\xf0\x9f\x87\xaa\xf0\x9f\x87\xba', 'flag_eu', 'flag_eu'),
            (b'\xf0\x9f\x87\xab\xf0\x9f\x87\xae', 'flag_fi', 'flag_fi'),
            (b'\xf0\x9f\x87\xab\xf0\x9f\x87\xaf', 'flag_fj', 'flag_fj'),
            (b'\xf0\x9f\x87\xab\xf0\x9f\x87\xb0', 'flag_fk', 'flag_fk'),
            (b'\xf0\x9f\x87\xab\xf0\x9f\x87\xb2', 'flag_fm', 'flag_fm'),
            (b'\xf0\x9f\x87\xab\xf0\x9f\x87\xb4', 'flag_fo', 'flag_fo'),
            (b'\xf0\x9f\x87\xab\xf0\x9f\x87\xb7', 'flag_fr', 'flag_fr'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xa6', 'flag_ga', 'flag_ga'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xa7', 'flag_gb', 'flag_gb'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xa9', 'flag_gd', 'flag_gd'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xaa', 'flag_ge', 'flag_ge'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xab', 'flag_gf', 'flag_gf'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xac', 'flag_gg', 'flag_gg'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xad', 'flag_gh', 'flag_gh'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xae', 'flag_gi', 'flag_gi'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xb1', 'flag_gl', 'flag_gl'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xb2', 'flag_gm', 'flag_gm'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xb3', 'flag_gn', 'flag_gn'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xb5', 'flag_gp', 'flag_gp'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xb6', 'flag_gq', 'flag_gq'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xb7', 'flag_gr', 'flag_gr'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xb8', 'flag_gs', 'flag_gs'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xb9', 'flag_gt', 'flag_gt'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xba', 'flag_gu', 'flag_gu'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xbc', 'flag_gw', 'flag_gw'),
            (b'\xf0\x9f\x87\xac\xf0\x9f\x87\xbe', 'flag_gy', 'flag_gy'),
            (b'\xf0\x9f\x87\xad\xf0\x9f\x87\xb0', 'flag_hk', 'flag_hk'),
            (b'\xf0\x9f\x87\xad\xf0\x9f\x87\xb2', 'flag_hm', 'flag_hm'),
            (b'\xf0\x9f\x87\xad\xf0\x9f\x87\xb3', 'flag_hn', 'flag_hn'),
            (b'\xf0\x9f\x87\xad\xf0\x9f\x87\xb7', 'flag_hr', 'flag_hr'),
            (b'\xf0\x9f\x87\xad\xf0\x9f\x87\xb9', 'flag_ht', 'flag_ht'),
            (b'\xf0\x9f\x87\xad\xf0\x9f\x87\xba', 'flag_hu', 'flag_hu'),
            (b'\xf0\x9f\x87\xae\xf0\x9f\x87\xa8', 'flag_ic', 'flag_ic'),
            (b'\xf0\x9f\x87\xae\xf0\x9f\x87\xa9', 'flag_id', 'flag_id'),
            (b'\xf0\x9f\x87\xae\xf0\x9f\x87\xaa', 'flag_ie', 'flag_ie'),
            (b'\xf0\x9f\x87\xae\xf0\x9f\x87\xb1', 'flag_il', 'flag_il'),
            (b'\xf0\x9f\x87\xae\xf0\x9f\x87\xb2', 'flag_im', 'flag_im'),
            (b'\xf0\x9f\x87\xae\xf0\x9f\x87\xb3', 'flag_in', 'flag_in'),
            (b'\xf0\x9f\x87\xae\xf0\x9f\x87\xb4', 'flag_io', 'flag_io'),
            (b'\xf0\x9f\x87\xae\xf0\x9f\x87\xb6', 'flag_iq', 'flag_iq'),
            (b'\xf0\x9f\x87\xae\xf0\x9f\x87\xb7', 'flag_ir', 'flag_ir'),
            (b'\xf0\x9f\x87\xae\xf0\x9f\x87\xb8', 'flag_is', 'flag_is'),
            (b'\xf0\x9f\x87\xae\xf0\x9f\x87\xb9', 'flag_it', 'flag_it'),
            (b'\xf0\x9f\x87\xaf\xf0\x9f\x87\xaa', 'flag_je', 'flag_je'),
            (b'\xf0\x9f\x87\xaf\xf0\x9f\x87\xb2', 'flag_jm', 'flag_jm'),
            (b'\xf0\x9f\x87\xaf\xf0\x9f\x87\xb4', 'flag_jo', 'flag_jo'),
            (b'\xf0\x9f\x87\xaf\xf0\x9f\x87\xb5', 'flag_jp', 'flag_jp'),
            (b'\xf0\x9f\x87\xb0\xf0\x9f\x87\xaa', 'flag_ke', 'flag_ke'),
            (b'\xf0\x9f\x87\xb0\xf0\x9f\x87\xac', 'flag_kg', 'flag_kg'),
            (b'\xf0\x9f\x87\xb0\xf0\x9f\x87\xad', 'flag_kh', 'flag_kh'),
            (b'\xf0\x9f\x87\xb0\xf0\x9f\x87\xae', 'flag_ki', 'flag_ki'),
            (b'\xf0\x9f\x87\xb0\xf0\x9f\x87\xb2', 'flag_km', 'flag_km'),
            (b'\xf0\x9f\x87\xb0\xf0\x9f\x87\xb3', 'flag_kn', 'flag_kn'),
            (b'\xf0\x9f\x87\xb0\xf0\x9f\x87\xb5', 'flag_kp', 'flag_kp'),
            (b'\xf0\x9f\x87\xb0\xf0\x9f\x87\xb7', 'flag_kr', 'flag_kr'),
            (b'\xf0\x9f\x87\xb0\xf0\x9f\x87\xbc', 'flag_kw', 'flag_kw'),
            (b'\xf0\x9f\x87\xb0\xf0\x9f\x87\xbe', 'flag_ky', 'flag_ky'),
            (b'\xf0\x9f\x87\xb0\xf0\x9f\x87\xbf', 'flag_kz', 'flag_kz'),
            (b'\xf0\x9f\x87\xb1\xf0\x9f\x87\xa6', 'flag_la', 'flag_la'),
            (b'\xf0\x9f\x87\xb1\xf0\x9f\x87\xa7', 'flag_lb', 'flag_lb'),
            (b'\xf0\x9f\x87\xb1\xf0\x9f\x87\xa8', 'flag_lc', 'flag_lc'),
            (b'\xf0\x9f\x87\xb1\xf0\x9f\x87\xae', 'flag_li', 'flag_li'),
            (b'\xf0\x9f\x87\xb1\xf0\x9f\x87\xb0', 'flag_lk', 'flag_lk'),
            (b'\xf0\x9f\x87\xb1\xf0\x9f\x87\xb7', 'flag_lr', 'flag_lr'),
            (b'\xf0\x9f\x87\xb1\xf0\x9f\x87\xb8', 'flag_ls', 'flag_ls'),
            (b'\xf0\x9f\x87\xb1\xf0\x9f\x87\xb9', 'flag_lt', 'flag_lt'),
            (b'\xf0\x9f\x87\xb1\xf0\x9f\x87\xba', 'flag_lu', 'flag_lu'),
            (b'\xf0\x9f\x87\xb1\xf0\x9f\x87\xbb', 'flag_lv', 'flag_lv'),
            (b'\xf0\x9f\x87\xb1\xf0\x9f\x87\xbe', 'flag_ly', 'flag_ly'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xa6', 'flag_ma', 'flag_ma'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xa8', 'flag_mc', 'flag_mc'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xa9', 'flag_md', 'flag_md'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xaa', 'flag_me', 'flag_me'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xab', 'flag_mf', 'flag_mf'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xac', 'flag_mg', 'flag_mg'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xad', 'flag_mh', 'flag_mh'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xb0', 'flag_mk', 'flag_mk'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xb1', 'flag_ml', 'flag_ml'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xb2', 'flag_mm', 'flag_mm'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xb3', 'flag_mn', 'flag_mn'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xb4', 'flag_mo', 'flag_mo'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xb5', 'flag_mp', 'flag_mp'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xb6', 'flag_mq', 'flag_mq'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xb7', 'flag_mr', 'flag_mr'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xb8', 'flag_ms', 'flag_ms'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xb9', 'flag_mt', 'flag_mt'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xba', 'flag_mu', 'flag_mu'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xbb', 'flag_mv', 'flag_mv'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xbc', 'flag_mw', 'flag_mw'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xbd', 'flag_mx', 'flag_mx'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xbe', 'flag_my', 'flag_my'),
            (b'\xf0\x9f\x87\xb2\xf0\x9f\x87\xbf', 'flag_mz', 'flag_mz'),
            (b'\xf0\x9f\x87\xb3\xf0\x9f\x87\xa6', 'flag_na', 'flag_na'),
            (b'\xf0\x9f\x87\xb3\xf0\x9f\x87\xa8', 'flag_nc', 'flag_nc'),
            (b'\xf0\x9f\x87\xb3\xf0\x9f\x87\xaa', 'flag_ne', 'flag_ne'),
            (b'\xf0\x9f\x87\xb3\xf0\x9f\x87\xab', 'flag_nf', 'flag_nf'),
            (b'\xf0\x9f\x87\xb3\xf0\x9f\x87\xac', 'flag_ng', 'flag_ng'),
            (b'\xf0\x9f\x87\xb3\xf0\x9f\x87\xae', 'flag_ni', 'flag_ni'),
            (b'\xf0\x9f\x87\xb3\xf0\x9f\x87\xb1', 'flag_nl', 'flag_nl'),
            (b'\xf0\x9f\x87\xb3\xf0\x9f\x87\xb4', 'flag_no', 'flag_no'),
            (b'\xf0\x9f\x87\xb3\xf0\x9f\x87\xb5', 'flag_np', 'flag_np'),
            (b'\xf0\x9f\x87\xb3\xf0\x9f\x87\xb7', 'flag_nr', 'flag_nr'),
            (b'\xf0\x9f\x87\xb3\xf0\x9f\x87\xba', 'flag_nu', 'flag_nu'),
            (b'\xf0\x9f\x87\xb3\xf0\x9f\x87\xbf', 'flag_nz', 'flag_nz'),
            (b'\xf0\x9f\x87\xb4\xf0\x9f\x87\xb2', 'flag_om', 'flag_om'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xa6', 'flag_pa', 'flag_pa'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xaa', 'flag_pe', 'flag_pe'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xab', 'flag_pf', 'flag_pf'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xac', 'flag_pg', 'flag_pg'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xad', 'flag_ph', 'flag_ph'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xb0', 'flag_pk', 'flag_pk'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xb1', 'flag_pl', 'flag_pl'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xb2', 'flag_pm', 'flag_pm'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xb3', 'flag_pn', 'flag_pn'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xb7', 'flag_pr', 'flag_pr'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xb8', 'flag_ps', 'flag_ps'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xb9', 'flag_pt', 'flag_pt'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xbc', 'flag_pw', 'flag_pw'),
            (b'\xf0\x9f\x87\xb5\xf0\x9f\x87\xbe', 'flag_py', 'flag_py'),
            (b'\xf0\x9f\x87\xb6\xf0\x9f\x87\xa6', 'flag_qa', 'flag_qa'),
            (b'\xf0\x9f\x87\xb7\xf0\x9f\x87\xaa', 'flag_re', 'flag_re'),
            (b'\xf0\x9f\x87\xb7\xf0\x9f\x87\xb4', 'flag_ro', 'flag_ro'),
            (b'\xf0\x9f\x87\xb7\xf0\x9f\x87\xb8', 'flag_rs', 'flag_rs'),
            (b'\xf0\x9f\x87\xb7\xf0\x9f\x87\xba', 'flag_ru', 'flag_ru'),
            (b'\xf0\x9f\x87\xb7\xf0\x9f\x87\xbc', 'flag_rw', 'flag_rw'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xa6', 'flag_sa', 'flag_sa'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xa7', 'flag_sb', 'flag_sb'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xa8', 'flag_sc', 'flag_sc'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xa9', 'flag_sd', 'flag_sd'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xaa', 'flag_se', 'flag_se'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xac', 'flag_sg', 'flag_sg'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xad', 'flag_sh', 'flag_sh'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xae', 'flag_si', 'flag_si'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xaf', 'flag_sj', 'flag_sj'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xb0', 'flag_sk', 'flag_sk'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xb1', 'flag_sl', 'flag_sl'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xb2', 'flag_sm', 'flag_sm'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xb3', 'flag_sn', 'flag_sn'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xb4', 'flag_so', 'flag_so'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xb7', 'flag_sr', 'flag_sr'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xb8', 'flag_ss', 'flag_ss'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xb9', 'flag_st', 'flag_st'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xbb', 'flag_sv', 'flag_sv'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xbd', 'flag_sx', 'flag_sx'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xbe', 'flag_sy', 'flag_sy'),
            (b'\xf0\x9f\x87\xb8\xf0\x9f\x87\xbf', 'flag_sz', 'flag_sz'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xa6', 'flag_ta', 'flag_ta'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xa8', 'flag_tc', 'flag_tc'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xa9', 'flag_td', 'flag_td'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xab', 'flag_tf', 'flag_tf'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xac', 'flag_tg', 'flag_tg'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xad', 'flag_th', 'flag_th'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xaf', 'flag_tj', 'flag_tj'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xb0', 'flag_tk', 'flag_tk'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xb1', 'flag_tl', 'flag_tl'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xb2', 'flag_tm', 'flag_tm'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xb3', 'flag_tn', 'flag_tn'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xb4', 'flag_to', 'flag_to'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xb7', 'flag_tr', 'flag_tr'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xb9', 'flag_tt', 'flag_tt'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xbb', 'flag_tv', 'flag_tv'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xbc', 'flag_tw', 'flag_tw'),
            (b'\xf0\x9f\x87\xb9\xf0\x9f\x87\xbf', 'flag_tz', 'flag_tz'),
            (b'\xf0\x9f\x87\xba\xf0\x9f\x87\xa6', 'flag_ua', 'flag_ua'),
            (b'\xf0\x9f\x87\xba\xf0\x9f\x87\xac', 'flag_ug', 'flag_ug'),
            (b'\xf0\x9f\x87\xba\xf0\x9f\x87\xb2', 'flag_um', 'flag_um'),
            (b'\xf0\x9f\x87\xba\xf0\x9f\x87\xb8', 'flag_us', 'flag_us'),
            (b'\xf0\x9f\x87\xba\xf0\x9f\x87\xbe', 'flag_uy', 'flag_uy'),
            (b'\xf0\x9f\x87\xba\xf0\x9f\x87\xbf', 'flag_uz', 'flag_uz'),
            (b'\xf0\x9f\x87\xbb\xf0\x9f\x87\xa6', 'flag_va', 'flag_va'),
            (b'\xf0\x9f\x87\xbb\xf0\x9f\x87\xa8', 'flag_vc', 'flag_vc'),
            (b'\xf0\x9f\x87\xbb\xf0\x9f\x87\xaa', 'flag_ve', 'flag_ve'),
            (b'\xf0\x9f\x87\xbb\xf0\x9f\x87\xac', 'flag_vg', 'flag_vg'),
            (b'\xf0\x9f\x87\xbb\xf0\x9f\x87\xae', 'flag_vi', 'flag_vi'),
            (b'\xf0\x9f\x87\xbb\xf0\x9f\x87\xb3', 'flag_vn', 'flag_vn'),
            (b'\xf0\x9f\x87\xbb\xf0\x9f\x87\xba', 'flag_vu', 'flag_vu'),
            (b'\xf0\x9f\x87\xbc\xf0\x9f\x87\xab', 'flag_wf', 'flag_wf'),
            (b'\xf0\x9f\x8f\xb3', 'flag_white', 'flag_white_vs16'),
            (b'\xf0\x9f\x87\xbc\xf0\x9f\x87\xb8', 'flag_ws', 'flag_ws'),
            (b'\xf0\x9f\x87\xbd\xf0\x9f\x87\xb0', 'flag_xk', 'flag_xk'),
            (b'\xf0\x9f\x87\xbe\xf0\x9f\x87\xaa', 'flag_ye', 'flag_ye'),
            (b'\xf0\x9f\x87\xbe\xf0\x9f\x87\xb9', 'flag_yt', 'flag_yt'),
            (b'\xf0\x9f\x87\xbf\xf0\x9f\x87\xa6', 'flag_za', 'flag_za'),
            (b'\xf0\x9f\x87\xbf\xf0\x9f\x87\xb2', 'flag_zm', 'flag_zm'),
            (b'\xf0\x9f\x87\xbf\xf0\x9f\x87\xbc', 'flag_zw', 'flag_zw'),
            (b'\xf0\x9f\x8e\x8f', 'flags', 'flags'),
            (b'\xf0\x9f\x94\xa6', 'flashlight', 'flashlight'),
            (b'\xe2\x9a\x9c', 'fleur_de_lis', 'fleur_de_lis_vs16'),
            (b'\xf0\x9f\x92\xbe', 'floppy_disk', 'floppy_disk'),
            (b'\xf0\x9f\x8e\xb4', 'flower_playing_cards', 'flower_playing_cards'),
            (b'\xf0\x9f\x98\xb3', 'flushed', 'flushed'),
            (b'\xf0\x9f\x8c\xab', 'fog', 'fog_vs16'),
            (b'\xf0\x9f\x8c\x81', 'foggy', 'foggy'),
            (b'\xf0\x9f\x8f\x88', 'football', 'football'),
            (b'\xf0\x9f\x91\xa3', 'footprints', 'footprints'),
            (b'\xf0\x9f\x8d\xb4', 'fork_and_knife', 'fork_and_knife'),
            (b'\xf0\x9f\x8d\xbd', 'fork_and_knife_with_plate', 'fork_and_knife_with_plate_vs16'),
            (b'\xe2\x9b\xb2', 'fountain', 'fountain'),
            (b'4\xe2\x83\xa3', 'four', 'four_vs16'),
            (b'\xf0\x9f\x8d\x80', 'four_leaf_clover', 'four_leaf_clover'),
            (b'\xf0\x9f\xa6\x8a', 'fox', 'fox', 'fox_face'),
            (b'\xf0\x9f\x96\xbc', 'frame_photo', 'frame_photo_vs16'),
            (b'\xf0\x9f\x86\x93', 'free', 'free'),
            (b'\xf0\x9f\x8d\xa4', 'fried_shrimp', 'fried_shrimp'),
            (b'\xf0\x9f\x8d\x9f', 'fries', 'fries'),
            (b'\xf0\x9f\x90\xb8', 'frog', 'frog'),
            (b'\xe2\x98\xb9', 'frowning2', 'frowning2_vs16'),
            (b'\xe2\x9b\xbd', 'fuelpump', 'fuelpump'),
            (b'\xf0\x9f\x8c\x95', 'full_moon', 'full_moon'),
            (b'\xf0\x9f\x8c\x9d', 'full_moon_with_face', 'full_moon_with_face'),
            (b'\xe2\x9a\xb1', 'funeral_urn', 'funeral_urn_vs16'),
            (b'\xf0\x9f\x8e\xb2', 'game_die', 'game_die'),
            (b'\xf0\x9f\x8f\xb3\xef\xb8\x8f\xe2\x80\x8d\xf0\x9f\x8c\x88', 'gay_pride_flag', 'gay_pride_flag', 'rainbow_flag'),
            (b'\xe2\x9a\x99', 'gear', 'gear_vs16'),
            (b'\xf0\x9f\x92\x8e', 'gem', 'gem'),
            (b'\xe2\x99\x8a', 'gemini', 'gemini'),
            (b'\xf0\x9f\x91\xbb', 'ghost', 'ghost'),
            (b'\xf0\x9f\x8e\x81', 'gift', 'gift'),
            (b'\xf0\x9f\x92\x9d', 'gift_heart', 'gift_heart'),
            (b'\xf0\x9f\x91\xa7', 'girl', 'girl'),
            (b'\xf0\x9f\x91\xa7\xf0\x9f\x8f\xbb', 'girl_tone1', 'girl_tone1'),
            (b'\xf0\x9f\x91\xa7\xf0\x9f\x8f\xbc', 'girl_tone2', 'girl_tone2'),
            (b'\xf0\x9f\x91\xa7\xf0\x9f\x8f\xbd', 'girl_tone3', 'girl_tone3'),
            (b'\xf0\x9f\x91\xa7\xf0\x9f\x8f\xbe', 'girl_tone4', 'girl_tone4'),
            (b'\xf0\x9f\x91\xa7\xf0\x9f\x8f\xbf', 'girl_tone5', 'girl_tone5'),
            (b'\xf0\x9f\xa5\x9b', 'glass_of_milk', 'glass_of_milk', 'milk'),
            (b'\xf0\x9f\x8c\x90', 'globe_with_meridians', 'globe_with_meridians'),
            (b'\xf0\x9f\xa5\x85', 'goal', 'goal', 'goal_net'),
            (b'\xf0\x9f\x90\x90', 'goat', 'goat'),
            (b'\xe2\x9b\xb3', 'golf', 'golf'),
            (b'\xf0\x9f\x8f\x8c', 'golfer', 'golfer_vs16'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbb', 'golfer_tone1', 'golfer_tone1', 'person_golfing_tone1'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbc', 'golfer_tone2', 'golfer_tone2', 'person_golfing_tone2'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbd', 'golfer_tone3', 'golfer_tone3', 'person_golfing_tone3'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbe', 'golfer_tone4', 'golfer_tone4', 'person_golfing_tone4'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbf', 'golfer_tone5', 'golfer_tone5', 'person_golfing_tone5'),
            (b'\xf0\x9f\xa6\x8d', 'gorilla', 'gorilla'),
            (b'\xf0\x9f\x91\xb5', 'grandma', 'grandma', 'older_woman'),
            (b'\xf0\x9f\x91\xb5\xf0\x9f\x8f\xbb', 'grandma_tone1', 'grandma_tone1', 'older_woman_tone1'),
            (b'\xf0\x9f\x91\xb5\xf0\x9f\x8f\xbc', 'grandma_tone2', 'grandma_tone2', 'older_woman_tone2'),
            (b'\xf0\x9f\x91\xb5\xf0\x9f\x8f\xbd', 'grandma_tone3', 'grandma_tone3', 'older_woman_tone3'),
            (b'\xf0\x9f\x91\xb5\xf0\x9f\x8f\xbe', 'grandma_tone4', 'grandma_tone4', 'older_woman_tone4'),
            (b'\xf0\x9f\x91\xb5\xf0\x9f\x8f\xbf', 'grandma_tone5', 'grandma_tone5', 'older_woman_tone5'),
            (b'\xf0\x9f\x8d\x87', 'grapes', 'grapes'),
            (b'\xf0\x9f\x8d\x8f', 'green_apple', 'green_apple'),
            (b'\xf0\x9f\x93\x97', 'green_book', 'green_book'),
            (b'\xf0\x9f\x92\x9a', 'green_heart', 'green_heart'),
            (b'\xf0\x9f\xa5\x97', 'green_salad', 'green_salad', 'salad'),
            (b'\xe2\x9d\x95', 'grey_exclamation', 'grey_exclamation'),
            (b'\xe2\x9d\x94', 'grey_question', 'grey_question'),
            (b'\xf0\x9f\x98\xac', 'grimacing', 'grimacing'),
            (b'\xf0\x9f\x98\x81', 'grin', 'grin'),
            (b'\xf0\x9f\x98\x80', 'grinning', 'grinning'),
            (b'\xf0\x9f\x92\x82', 'guardsman', 'guardsman', 'guard'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbb', 'guardsman_tone1', 'guardsman_tone1', 'guard_tone1'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbc', 'guardsman_tone2', 'guardsman_tone2', 'guard_tone2'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbd', 'guardsman_tone3', 'guardsman_tone3', 'guard_tone3'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbe', 'guardsman_tone4', 'guardsman_tone4', 'guard_tone4'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbf', 'guardsman_tone5', 'guardsman_tone5', 'guard_tone5'),
            (b'\xf0\x9f\x8e\xb8', 'guitar', 'guitar'),
            (b'\xf0\x9f\x94\xab', 'gun', 'gun'),
            (b'\xf0\x9f\x92\x87', 'haircut', 'haircut', 'person_getting_haircut'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbb', 'haircut_tone1', 'haircut_tone1', 'person_getting_haircut_tone1'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbc', 'haircut_tone2', 'haircut_tone2', 'person_getting_haircut_tone2'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbd', 'haircut_tone3', 'haircut_tone3', 'person_getting_haircut_tone3'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbe', 'haircut_tone4', 'haircut_tone4', 'person_getting_haircut_tone4'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbf', 'haircut_tone5', 'haircut_tone5', 'person_getting_haircut_tone5'),
            (b'\xf0\x9f\x8d\x94', 'hamburger', 'hamburger'),
            (b'\xf0\x9f\x94\xa8', 'hammer', 'hammer'),
            (b'\xe2\x9a\x92', 'hammer_and_pick', 'hammer_and_pick_vs16'),
            (b'\xf0\x9f\x9b\xa0', 'hammer_and_wrench', 'hammer_and_wrench_vs16'),
            (b'\xf0\x9f\x90\xb9', 'hamster', 'hamster'),
            (b'\xf0\x9f\x96\x90', 'hand_splayed', 'hand_splayed_vs16'),
            (b'\xf0\x9f\x96\x90\xf0\x9f\x8f\xbb', 'hand_splayed_tone1', 'hand_splayed_tone1', 'raised_hand_with_fingers_splayed_tone1'),
            (b'\xf0\x9f\x96\x90\xf0\x9f\x8f\xbc', 'hand_splayed_tone2', 'hand_splayed_tone2', 'raised_hand_with_fingers_splayed_tone2'),
            (b'\xf0\x9f\x96\x90\xf0\x9f\x8f\xbd', 'hand_splayed_tone3', 'hand_splayed_tone3', 'raised_hand_with_fingers_splayed_tone3'),
            (b'\xf0\x9f\x96\x90\xf0\x9f\x8f\xbe', 'hand_splayed_tone4', 'hand_splayed_tone4', 'raised_hand_with_fingers_splayed_tone4'),
            (b'\xf0\x9f\x96\x90\xf0\x9f\x8f\xbf', 'hand_splayed_tone5', 'hand_splayed_tone5', 'raised_hand_with_fingers_splayed_tone5'),
            (b'\xf0\x9f\x91\x9c', 'handbag', 'handbag'),
            (b'\xf0\x9f\xa4\xbe', 'handball', 'handball', 'person_playing_handball'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbb', 'handball_tone1', 'handball_tone1', 'person_playing_handball_tone1'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbc', 'handball_tone2', 'handball_tone2', 'person_playing_handball_tone2'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbd', 'handball_tone3', 'handball_tone3', 'person_playing_handball_tone3'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbe', 'handball_tone4', 'handball_tone4', 'person_playing_handball_tone4'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbf', 'handball_tone5', 'handball_tone5', 'person_playing_handball_tone5'),
            (b'\xf0\x9f\xa4\x9d', 'handshake', 'handshake', 'shaking_hands'),
            (b'\xf0\x9f\x92\xa9', 'hankey', 'hankey', 'poo', 'poop', 'shit'),
            (b'#\xe2\x83\xa3', 'hash', 'hash_vs16'),
            (b'\xf0\x9f\x90\xa5', 'hatched_chick', 'hatched_chick'),
            (b'\xf0\x9f\x90\xa3', 'hatching_chick', 'hatching_chick'),
            (b'\xf0\x9f\x8e\xa7', 'headphones', 'headphones'),
            (b'\xf0\x9f\x99\x89', 'hear_no_evil', 'hear_no_evil'),
            (b'\xe2\x9d\xa4', 'heart', 'heart_vs16'),
            (b'\xf0\x9f\x92\x9f', 'heart_decoration', 'heart_decoration'),
            (b'\xe2\x9d\xa3', 'heart_exclamation', 'heart_exclamation_vs16'),
            (b'\xf0\x9f\x98\x8d', 'heart_eyes', 'heart_eyes'),
            (b'\xf0\x9f\x98\xbb', 'heart_eyes_cat', 'heart_eyes_cat'),
            (b'\xf0\x9f\x92\x93', 'heartbeat', 'heartbeat'),
            (b'\xf0\x9f\x92\x97', 'heartpulse', 'heartpulse'),
            (b'\xe2\x99\xa5', 'hearts', 'hearts_vs16'),
            (b'\xe2\x9c\x94', 'heavy_check_mark', 'heavy_check_mark_vs16'),
            (b'\xe2\x9e\x97', 'heavy_division_sign', 'heavy_division_sign'),
            (b'\xf0\x9f\x92\xb2', 'heavy_dollar_sign', 'heavy_dollar_sign'),
            (b'\xe2\x9e\x96', 'heavy_minus_sign', 'heavy_minus_sign'),
            (b'\xe2\x9c\x96', 'heavy_multiplication_x', 'heavy_multiplication_x_vs16'),
            (b'\xe2\x9e\x95', 'heavy_plus_sign', 'heavy_plus_sign'),
            (b'\xf0\x9f\x9a\x81', 'helicopter', 'helicopter'),
            (b'\xe2\x9b\x91', 'helmet_with_cross', 'helmet_with_cross_vs16'),
            (b'\xf0\x9f\x8c\xbf', 'herb', 'herb'),
            (b'\xf0\x9f\x8c\xba', 'hibiscus', 'hibiscus'),
            (b'\xf0\x9f\x94\x86', 'high_brightness', 'high_brightness'),
            (b'\xf0\x9f\x91\xa0', 'high_heel', 'high_heel'),
            (b'\xf0\x9f\x8f\x92', 'hockey', 'hockey'),
            (b'\xf0\x9f\x95\xb3', 'hole', 'hole_vs16'),
            (b'\xf0\x9f\x8f\x98', 'homes', 'homes_vs16'),
            (b'\xf0\x9f\x8d\xaf', 'honey_pot', 'honey_pot'),
            (b'\xf0\x9f\x90\xb4', 'horse', 'horse'),
            (b'\xf0\x9f\x8f\x87', 'horse_racing', 'horse_racing'),
            (b'\xf0\x9f\x8f\x87\xf0\x9f\x8f\xbb', 'horse_racing_tone1', 'horse_racing_tone1'),
            (b'\xf0\x9f\x8f\x87\xf0\x9f\x8f\xbc', 'horse_racing_tone2', 'horse_racing_tone2'),
            (b'\xf0\x9f\x8f\x87\xf0\x9f\x8f\xbd', 'horse_racing_tone3', 'horse_racing_tone3'),
            (b'\xf0\x9f\x8f\x87\xf0\x9f\x8f\xbe', 'horse_racing_tone4', 'horse_racing_tone4'),
            (b'\xf0\x9f\x8f\x87\xf0\x9f\x8f\xbf', 'horse_racing_tone5', 'horse_racing_tone5'),
            (b'\xf0\x9f\x8f\xa5', 'hospital', 'hospital'),
            (b'\xf0\x9f\x8c\xad', 'hot_dog', 'hot_dog', 'hotdog'),
            (b'\xf0\x9f\x8c\xb6', 'hot_pepper', 'hot_pepper_vs16'),
            (b'\xf0\x9f\x8f\xa8', 'hotel', 'hotel'),
            (b'\xe2\x99\xa8', 'hotsprings', 'hotsprings_vs16'),
            (b'\xe2\x8c\x9b', 'hourglass', 'hourglass'),
            (b'\xe2\x8f\xb3', 'hourglass_flowing_sand', 'hourglass_flowing_sand'),
            (b'\xf0\x9f\x8f\xa0', 'house', 'house'),
            (b'\xf0\x9f\x8f\xa1', 'house_with_garden', 'house_with_garden'),
            (b'\xf0\x9f\xa4\x97', 'hugging', 'hugging', 'hugging_face'),
            (b'\xf0\x9f\x98\xaf', 'hushed', 'hushed'),
            (b'\xf0\x9f\x8d\xa8', 'ice_cream', 'ice_cream'),
            (b'\xe2\x9b\xb8', 'ice_skate', 'ice_skate_vs16'),
            (b'\xf0\x9f\x8d\xa6', 'icecream', 'icecream'),
            (b'\xf0\x9f\x86\x94', 'id', 'id'),
            (b'\xf0\x9f\x89\x90', 'ideograph_advantage', 'ideograph_advantage'),
            (b'\xf0\x9f\x91\xbf', 'imp', 'imp', ']:(', ']:-(', ']=(', ']=-('),
            (b'\xf0\x9f\x93\xa5', 'inbox_tray', 'inbox_tray'),
            (b'\xf0\x9f\x93\xa8', 'incoming_envelope', 'incoming_envelope'),
            (b'\xf0\x9f\x92\x81', 'information_desk_person', 'information_desk_person', 'person_tipping_hand'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbb', 'information_desk_person_tone1', 'information_desk_person_tone1', 'person_tipping_hand_tone1'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbc', 'information_desk_person_tone2', 'information_desk_person_tone2', 'person_tipping_hand_tone2'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbd', 'information_desk_person_tone3', 'information_desk_person_tone3', 'person_tipping_hand_tone3'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbe', 'information_desk_person_tone4', 'information_desk_person_tone4', 'person_tipping_hand_tone4'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbf', 'information_desk_person_tone5', 'information_desk_person_tone5', 'person_tipping_hand_tone5'),
            (b'\xe2\x84\xb9', 'information_source', 'information_source_vs16'),
            (b'\xe2\x81\x89', 'interrobang', 'interrobang_vs16'),
            (b'\xf0\x9f\x93\xb1', 'iphone', 'iphone', 'mobile_phone'),
            (b'\xf0\x9f\x8f\xae', 'izakaya_lantern', 'izakaya_lantern'),
            (b'\xf0\x9f\x8e\x83', 'jack_o_lantern', 'jack_o_lantern'),
            (b'\xf0\x9f\x97\xbe', 'japan', 'japan'),
            (b'\xf0\x9f\x8f\xaf', 'japanese_castle', 'japanese_castle'),
            (b'\xf0\x9f\x91\xba', 'japanese_goblin', 'japanese_goblin'),
            (b'\xf0\x9f\x91\xb9', 'japanese_ogre', 'japanese_ogre'),
            (b'\xf0\x9f\x91\x96', 'jeans', 'jeans'),
            (b'\xf0\x9f\x98\xb9', 'joy_cat', 'joy_cat'),
            (b'\xf0\x9f\x95\xb9', 'joystick', 'joystick_vs16'),
            (b'\xf0\x9f\xa4\xb9', 'juggler', 'juggler', 'juggling', 'person_juggling'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbb', 'juggler_tone1', 'juggler_tone1', 'juggling_tone1', 'person_juggling_tone1'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbc', 'juggler_tone2', 'juggler_tone2', 'juggling_tone2', 'person_juggling_tone2'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbd', 'juggler_tone3', 'juggler_tone3', 'juggling_tone3', 'person_juggling_tone3'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbe', 'juggler_tone4', 'juggler_tone4', 'juggling_tone4', 'person_juggling_tone4'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbf', 'juggler_tone5', 'juggler_tone5', 'juggling_tone5', 'person_juggling_tone5'),
            (b'\xf0\x9f\x95\x8b', 'kaaba', 'kaaba'),
            (b'\xf0\x9f\xa5\x8b', 'karate_uniform', 'karate_uniform', 'martial_arts_uniform'),
            (b'\xf0\x9f\x97\x9d', 'key2', 'key2_vs16'),
            (b'\xf0\x9f\x94\x91', 'key', 'key'),
            (b'\xe2\x8c\xa8', 'keyboard', 'keyboard_vs16'),
            (b'\xf0\x9f\x94\x9f', 'keycap_ten', 'keycap_ten'),
            (b'\xf0\x9f\x91\x98', 'kimono', 'kimono'),
            (b'\xf0\x9f\x92\x8b', 'kiss', 'kiss'),
            (b'\xf0\x9f\x98\xbd', 'kissing_cat', 'kissing_cat'),
            (b'\xf0\x9f\x98\x9a', 'kissing_closed_eyes', 'kissing_closed_eyes'),
            (b'\xf0\x9f\x98\x98', 'kissing_heart', 'kissing_heart'),
            (b'\xf0\x9f\x98\x99', 'kissing_smiling_eyes', 'kissing_smiling_eyes'),
            (b'\xf0\x9f\xa5\x9d', 'kiwi', 'kiwi', 'kiwifruit'),
            (b'\xf0\x9f\x94\xaa', 'knife', 'knife'),
            (b'\xf0\x9f\x90\xa8', 'koala', 'koala'),
            (b'\xf0\x9f\x88\x81', 'koko', 'koko'),
            (b'\xf0\x9f\x8f\xb7', 'label', 'label_vs16'),
            (b'\xf0\x9f\x94\xb5', 'large_blue_circle', 'large_blue_circle', 'blue_circle'),
            (b'\xf0\x9f\x94\xb7', 'large_blue_diamond', 'large_blue_diamond'),
            (b'\xf0\x9f\x94\xb6', 'large_orange_diamond', 'large_orange_diamond'),
            (b'\xf0\x9f\x8c\x97', 'last_quarter_moon', 'last_quarter_moon'),
            (b'\xf0\x9f\x8c\x9c', 'last_quarter_moon_with_face', 'last_quarter_moon_with_face'),
            (b'\xf0\x9f\x98\x86', 'laughing', 'laughing', 'satisfied', 'x-)', 'X-)'),
            (b'\xf0\x9f\x8d\x83', 'leaves', 'leaves'),
            (b'\xf0\x9f\x93\x92', 'ledger', 'ledger'),
            (b'\xf0\x9f\xa4\x9b', 'left_facing_fist', 'left_facing_fist', 'left_fist'),
            (b'\xf0\x9f\xa4\x9b\xf0\x9f\x8f\xbb', 'left_facing_fist_tone1', 'left_facing_fist_tone1', 'left_fist_tone1'),
            (b'\xf0\x9f\xa4\x9b\xf0\x9f\x8f\xbc', 'left_facing_fist_tone2', 'left_facing_fist_tone2', 'left_fist_tone2'),
            (b'\xf0\x9f\xa4\x9b\xf0\x9f\x8f\xbd', 'left_facing_fist_tone3', 'left_facing_fist_tone3', 'left_fist_tone3'),
            (b'\xf0\x9f\xa4\x9b\xf0\x9f\x8f\xbe', 'left_facing_fist_tone4', 'left_facing_fist_tone4', 'left_fist_tone4'),
            (b'\xf0\x9f\xa4\x9b\xf0\x9f\x8f\xbf', 'left_facing_fist_tone5', 'left_facing_fist_tone5', 'left_fist_tone5'),
            (b'\xf0\x9f\x9b\x85', 'left_luggage', 'left_luggage'),
            (b'\xe2\x86\x94', 'left_right_arrow', 'left_right_arrow_vs16'),
            (b'\xf0\x9f\x97\xa8', 'left_speech_bubble', 'left_speech_bubble_vs16'),
            (b'\xe2\x86\xa9', 'leftwards_arrow_with_hook', 'leftwards_arrow_with_hook_vs16'),
            (b'\xf0\x9f\x8d\x8b', 'lemon', 'lemon'),
            (b'\xe2\x99\x8c', 'leo', 'leo'),
            (b'\xf0\x9f\x90\x86', 'leopard', 'leopard'),
            (b'\xf0\x9f\x8e\x9a', 'level_slider', 'level_slider_vs16'),
            (b'\xf0\x9f\x95\xb4', 'levitate', 'levitate_vs16'),
            (b'\xf0\x9f\x95\xb4\xf0\x9f\x8f\xbb', 'levitate_tone1', 'levitate_tone1', 'man_in_business_suit_levitating_tone1'),
            (b'\xf0\x9f\x95\xb4\xf0\x9f\x8f\xbc', 'levitate_tone2', 'levitate_tone2', 'man_in_business_suit_levitating_tone2'),
            (b'\xf0\x9f\x95\xb4\xf0\x9f\x8f\xbd', 'levitate_tone3', 'levitate_tone3', 'man_in_business_suit_levitating_tone3'),
            (b'\xf0\x9f\x95\xb4\xf0\x9f\x8f\xbe', 'levitate_tone4', 'levitate_tone4', 'man_in_business_suit_levitating_tone4'),
            (b'\xf0\x9f\x95\xb4\xf0\x9f\x8f\xbf', 'levitate_tone5', 'levitate_tone5', 'man_in_business_suit_levitating_tone5'),
            (b'\xf0\x9f\xa4\xa5', 'liar', 'liar', 'lying_face'),
            (b'\xe2\x99\x8e', 'libra', 'libra'),
            (b'\xf0\x9f\x8f\x8b', 'lifter', 'lifter_vs16'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbb', 'lifter_tone1', 'lifter_tone1', 'weight_lifter_tone1', 'person_lifting_weights_tone1'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbc', 'lifter_tone2', 'lifter_tone2', 'weight_lifter_tone2', 'person_lifting_weights_tone2'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbd', 'lifter_tone3', 'lifter_tone3', 'weight_lifter_tone3', 'person_lifting_weights_tone3'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbe', 'lifter_tone4', 'lifter_tone4', 'weight_lifter_tone4', 'person_lifting_weights_tone4'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbf', 'lifter_tone5', 'lifter_tone5', 'weight_lifter_tone5', 'person_lifting_weights_tone5'),
            (b'\xf0\x9f\x9a\x88', 'light_rail', 'light_rail'),
            (b'\xf0\x9f\x94\x97', 'link', 'link'),
            (b'\xf0\x9f\x96\x87', 'linked_paperclips', 'linked_paperclips_vs16'),
            (b'\xf0\x9f\xa6\x81', 'lion', 'lion', 'lion_face'),
            (b'\xf0\x9f\x91\x84', 'lips', 'lips'),
            (b'\xf0\x9f\x92\x84', 'lipstick', 'lipstick'),
            (b'\xf0\x9f\xa6\x8e', 'lizard', 'lizard'),
            (b'\xf0\x9f\x94\x92', 'lock', 'lock'),
            (b'\xf0\x9f\x94\x8f', 'lock_with_ink_pen', 'lock_with_ink_pen'),
            (b'\xf0\x9f\x8d\xad', 'lollipop', 'lollipop'),
            (b'\xe2\x9e\xbf', 'loop', 'loop'),
            (b'\xf0\x9f\x94\x8a', 'loud_sound', 'loud_sound'),
            (b'\xf0\x9f\x93\xa2', 'loudspeaker', 'loudspeaker'),
            (b'\xf0\x9f\x8f\xa9', 'love_hotel', 'love_hotel'),
            (b'\xf0\x9f\x92\x8c', 'love_letter', 'love_letter'),
            (b'\xf0\x9f\x94\x85', 'low_brightness', 'low_brightness'),
            (b'\xf0\x9f\x96\x8a', 'lower_left_ballpoint_pen', 'lower_left_ballpoint_pen_vs16'),
            (b'\xf0\x9f\x96\x8b', 'lower_left_fountain_pen', 'lower_left_fountain_pen_vs16'),
            (b'\xf0\x9f\x96\x8c', 'lower_left_paintbrush', 'lower_left_paintbrush_vs16'),
            (b'\xe2\x93\x82', 'm', 'm_vs16'),
            (b'\xf0\x9f\x94\x8d', 'mag', 'mag'),
            (b'\xf0\x9f\x94\x8e', 'mag_right', 'mag_right'),
            (b'\xf0\x9f\x80\x84', 'mahjong', 'mahjong'),
            (b'\xf0\x9f\x93\xab', 'mailbox', 'mailbox'),
            (b'\xf0\x9f\x93\xaa', 'mailbox_closed', 'mailbox_closed'),
            (b'\xf0\x9f\x93\xac', 'mailbox_with_mail', 'mailbox_with_mail'),
            (b'\xf0\x9f\x93\xad', 'mailbox_with_no_mail', 'mailbox_with_no_mail'),
            (b'\xf0\x9f\x95\xba', 'male_dancer', 'male_dancer', 'man_dancing'),
            (b'\xf0\x9f\x95\xba\xf0\x9f\x8f\xbb', 'male_dancer_tone1', 'male_dancer_tone1', 'man_dancing_tone1'),
            (b'\xf0\x9f\x95\xba\xf0\x9f\x8f\xbc', 'male_dancer_tone2', 'male_dancer_tone2', 'man_dancing_tone2'),
            (b'\xf0\x9f\x95\xba\xf0\x9f\x8f\xbd', 'male_dancer_tone3', 'male_dancer_tone3', 'man_dancing_tone3'),
            (b'\xf0\x9f\x95\xba\xf0\x9f\x8f\xbe', 'male_dancer_tone4', 'male_dancer_tone4', 'man_dancing_tone4'),
            (b'\xf0\x9f\x95\xba\xf0\x9f\x8f\xbf', 'male_dancer_tone5', 'male_dancer_tone5', 'man_dancing_tone5'),
            (b'\xf0\x9f\x91\xa8', 'man', 'man'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb', 'man_tone1', 'man_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc', 'man_tone2', 'man_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd', 'man_tone3', 'man_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe', 'man_tone4', 'man_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf', 'man_tone5', 'man_tone5'),
            (b'\xf0\x9f\xa4\xb5', 'man_in_tuxedo', 'man_in_tuxedo', 'person_in_tuxedo'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbb', 'man_in_tuxedo_tone1', 'man_in_tuxedo_tone1', 'tuxedo_tone1', 'person_in_tuxedo_tone1'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbc', 'man_in_tuxedo_tone2', 'man_in_tuxedo_tone2', 'tuxedo_tone2', 'person_in_tuxedo_tone2'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbd', 'man_in_tuxedo_tone3', 'man_in_tuxedo_tone3', 'tuxedo_tone3', 'person_in_tuxedo_tone3'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbe', 'man_in_tuxedo_tone4', 'man_in_tuxedo_tone4', 'tuxedo_tone4', 'person_in_tuxedo_tone4'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbf', 'man_in_tuxedo_tone5', 'man_in_tuxedo_tone5', 'tuxedo_tone5', 'person_in_tuxedo_tone5'),
            (b'\xf0\x9f\x91\xb2', 'man_with_gua_pi_mao', 'man_with_gua_pi_mao', 'man_with_chinese_cap'),
            (b'\xf0\x9f\x91\xb2\xf0\x9f\x8f\xbb', 'man_with_gua_pi_mao_tone1', 'man_with_gua_pi_mao_tone1', 'man_with_chinese_cap_tone1'),
            (b'\xf0\x9f\x91\xb2\xf0\x9f\x8f\xbc', 'man_with_gua_pi_mao_tone2', 'man_with_gua_pi_mao_tone2', 'man_with_chinese_cap_tone2'),
            (b'\xf0\x9f\x91\xb2\xf0\x9f\x8f\xbd', 'man_with_gua_pi_mao_tone3', 'man_with_gua_pi_mao_tone3', 'man_with_chinese_cap_tone3'),
            (b'\xf0\x9f\x91\xb2\xf0\x9f\x8f\xbe', 'man_with_gua_pi_mao_tone4', 'man_with_gua_pi_mao_tone4', 'man_with_chinese_cap_tone4'),
            (b'\xf0\x9f\x91\xb2\xf0\x9f\x8f\xbf', 'man_with_gua_pi_mao_tone5', 'man_with_gua_pi_mao_tone5', 'man_with_chinese_cap_tone5'),
            (b'\xf0\x9f\x91\xb3', 'man_with_turban', 'man_with_turban', 'person_wearing_turban'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbb', 'man_with_turban_tone1', 'man_with_turban_tone1', 'person_wearing_turban_tone1'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbc', 'man_with_turban_tone2', 'man_with_turban_tone2', 'person_wearing_turban_tone2'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbd', 'man_with_turban_tone3', 'man_with_turban_tone3', 'person_wearing_turban_tone3'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbe', 'man_with_turban_tone4', 'man_with_turban_tone4', 'person_wearing_turban_tone4'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbf', 'man_with_turban_tone5', 'man_with_turban_tone5', 'person_wearing_turban_tone5'),
            (b'\xf0\x9f\x91\x9e', 'mans_shoe', 'mans_shoe'),
            (b'\xf0\x9f\x97\xba', 'map', 'map_vs16'),
            (b'\xf0\x9f\x8d\x81', 'maple_leaf', 'maple_leaf'),
            (b'\xf0\x9f\x98\xb7', 'mask', 'mask'),
            (b'\xf0\x9f\x92\x86', 'massage', 'massage', 'person_getting_massage'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbb', 'massage_tone1', 'massage_tone1', 'person_getting_massage_tone1'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbc', 'massage_tone2', 'massage_tone2', 'person_getting_massage_tone2'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbd', 'massage_tone3', 'massage_tone3', 'person_getting_massage_tone3'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbe', 'massage_tone4', 'massage_tone4', 'person_getting_massage_tone4'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbf', 'massage_tone5', 'massage_tone5', 'person_getting_massage_tone5'),
            (b'\xf0\x9f\x8d\x96', 'meat_on_bone', 'meat_on_bone'),
            (b'\xf0\x9f\x8f\x85', 'medal', 'medal', 'sports_medal'),
            (b'\xf0\x9f\x93\xa3', 'mega', 'mega'),
            (b'\xf0\x9f\x8d\x88', 'melon', 'melon'),
            (b'\xf0\x9f\x95\x8e', 'menorah', 'menorah'),
            (b'\xf0\x9f\x9a\xb9', 'mens', 'mens'),
            (b'\xf0\x9f\xa4\x98', 'metal', 'metal', 'sign_of_the_horns'),
            (b'\xf0\x9f\xa4\x98\xf0\x9f\x8f\xbb', 'metal_tone1', 'metal_tone1', 'sign_of_the_horns_tone1'),
            (b'\xf0\x9f\xa4\x98\xf0\x9f\x8f\xbc', 'metal_tone2', 'metal_tone2', 'sign_of_the_horns_tone2'),
            (b'\xf0\x9f\xa4\x98\xf0\x9f\x8f\xbd', 'metal_tone3', 'metal_tone3', 'sign_of_the_horns_tone3'),
            (b'\xf0\x9f\xa4\x98\xf0\x9f\x8f\xbe', 'metal_tone4', 'metal_tone4', 'sign_of_the_horns_tone4'),
            (b'\xf0\x9f\xa4\x98\xf0\x9f\x8f\xbf', 'metal_tone5', 'metal_tone5', 'sign_of_the_horns_tone5'),
            (b'\xf0\x9f\x9a\x87', 'metro', 'metro'),
            (b'\xf0\x9f\x8e\x99', 'microphone2', 'microphone2_vs16'),
            (b'\xf0\x9f\x8e\xa4', 'microphone', 'microphone'),
            (b'\xf0\x9f\x94\xac', 'microscope', 'microscope'),
            (b'\xf0\x9f\x96\x95', 'middle_finger', 'middle_finger', 'reversed_hand_with_middle_finger_extended'),
            (b'\xf0\x9f\x96\x95\xf0\x9f\x8f\xbb', 'middle_finger_tone1', 'middle_finger_tone1', 'reversed_hand_with_middle_finger_extended_tone1'),
            (b'\xf0\x9f\x96\x95\xf0\x9f\x8f\xbc', 'middle_finger_tone2', 'middle_finger_tone2', 'reversed_hand_with_middle_finger_extended_tone2'),
            (b'\xf0\x9f\x96\x95\xf0\x9f\x8f\xbd', 'middle_finger_tone3', 'middle_finger_tone3', 'reversed_hand_with_middle_finger_extended_tone3'),
            (b'\xf0\x9f\x96\x95\xf0\x9f\x8f\xbe', 'middle_finger_tone4', 'middle_finger_tone4', 'reversed_hand_with_middle_finger_extended_tone4'),
            (b'\xf0\x9f\x96\x95\xf0\x9f\x8f\xbf', 'middle_finger_tone5', 'middle_finger_tone5', 'reversed_hand_with_middle_finger_extended_tone5'),
            (b'\xf0\x9f\x8e\x96', 'military_medal', 'military_medal_vs16'),
            (b'\xf0\x9f\x8c\x8c', 'milky_way', 'milky_way'),
            (b'\xf0\x9f\x9a\x90', 'minibus', 'minibus'),
            (b'\xf0\x9f\x92\xbd', 'minidisc', 'minidisc'),
            (b'\xf0\x9f\x93\xb4', 'mobile_phone_off', 'mobile_phone_off'),
            (b'\xf0\x9f\xa4\x91', 'money_mouth', 'money_mouth', 'money_mouth_face'),
            (b'\xf0\x9f\x92\xb8', 'money_with_wings', 'money_with_wings'),
            (b'\xf0\x9f\x92\xb0', 'moneybag', 'moneybag'),
            (b'\xf0\x9f\x90\x92', 'monkey', 'monkey'),
            (b'\xf0\x9f\x90\xb5', 'monkey_face', 'monkey_face'),
            (b'\xf0\x9f\x9a\x9d', 'monorail', 'monorail'),
            (b'\xf0\x9f\x8e\x93', 'mortar_board', 'mortar_board'),
            (b'\xf0\x9f\x95\x8c', 'mosque', 'mosque'),
            (b'\xf0\x9f\xa4\xb6', 'mother_christmas', 'mother_christmas', 'mrs_claus'),
            (b'\xf0\x9f\xa4\xb6\xf0\x9f\x8f\xbb', 'mother_christmas_tone1', 'mother_christmas_tone1', 'mrs_claus_tone1'),
            (b'\xf0\x9f\xa4\xb6\xf0\x9f\x8f\xbc', 'mother_christmas_tone2', 'mother_christmas_tone2', 'mrs_claus_tone2'),
            (b'\xf0\x9f\xa4\xb6\xf0\x9f\x8f\xbd', 'mother_christmas_tone3', 'mother_christmas_tone3', 'mrs_claus_tone3'),
            (b'\xf0\x9f\xa4\xb6\xf0\x9f\x8f\xbe', 'mother_christmas_tone4', 'mother_christmas_tone4', 'mrs_claus_tone4'),
            (b'\xf0\x9f\xa4\xb6\xf0\x9f\x8f\xbf', 'mother_christmas_tone5', 'mother_christmas_tone5', 'mrs_claus_tone5'),
            (b'\xf0\x9f\x9b\xb5', 'motor_scooter', 'motor_scooter', 'motorbike'),
            (b'\xf0\x9f\x9b\xa5', 'motorboat', 'motorboat_vs16'),
            (b'\xf0\x9f\x8f\x8d', 'motorcycle', 'motorcycle_vs16'),
            (b'\xf0\x9f\x9b\xa3', 'motorway', 'motorway_vs16'),
            (b'\xf0\x9f\x97\xbb', 'mount_fuji', 'mount_fuji'),
            (b'\xe2\x9b\xb0', 'mountain', 'mountain_vs16'),
            (b'\xf0\x9f\x9a\xb5', 'mountain_bicyclist', 'mountain_bicyclist', 'person_mountain_biking'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbb', 'mountain_bicyclist_tone1', 'mountain_bicyclist_tone1', 'person_mountain_biking_tone1'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbc', 'mountain_bicyclist_tone2', 'mountain_bicyclist_tone2', 'person_mountain_biking_tone2'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbd', 'mountain_bicyclist_tone3', 'mountain_bicyclist_tone3', 'person_mountain_biking_tone3'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbe', 'mountain_bicyclist_tone4', 'mountain_bicyclist_tone4', 'person_mountain_biking_tone4'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbf', 'mountain_bicyclist_tone5', 'mountain_bicyclist_tone5', 'person_mountain_biking_tone5'),
            (b'\xf0\x9f\x9a\xa0', 'mountain_cableway', 'mountain_cableway'),
            (b'\xf0\x9f\x9a\x9e', 'mountain_railway', 'mountain_railway'),
            (b'\xf0\x9f\x8f\x94', 'mountain_snow', 'mountain_snow_vs16'),
            (b'\xf0\x9f\x90\x81', 'mouse2', 'mouse2'),
            (b'\xf0\x9f\x90\xad', 'mouse', 'mouse'),
            (b'\xf0\x9f\x96\xb1', 'mouse_three_button', 'mouse_three_button_vs16'),
            (b'\xf0\x9f\x8e\xa5', 'movie_camera', 'movie_camera'),
            (b'\xf0\x9f\x97\xbf', 'moyai', 'moyai'),
            (b'\xf0\x9f\x92\xaa', 'muscle', 'muscle'),
            (b'\xf0\x9f\x92\xaa\xf0\x9f\x8f\xbb', 'muscle_tone1', 'muscle_tone1'),
            (b'\xf0\x9f\x92\xaa\xf0\x9f\x8f\xbc', 'muscle_tone2', 'muscle_tone2'),
            (b'\xf0\x9f\x92\xaa\xf0\x9f\x8f\xbd', 'muscle_tone3', 'muscle_tone3'),
            (b'\xf0\x9f\x92\xaa\xf0\x9f\x8f\xbe', 'muscle_tone4', 'muscle_tone4'),
            (b'\xf0\x9f\x92\xaa\xf0\x9f\x8f\xbf', 'muscle_tone5', 'muscle_tone5'),
            (b'\xf0\x9f\x8d\x84', 'mushroom', 'mushroom'),
            (b'\xf0\x9f\x8e\xb9', 'musical_keyboard', 'musical_keyboard'),
            (b'\xf0\x9f\x8e\xb5', 'musical_note', 'musical_note'),
            (b'\xf0\x9f\x8e\xbc', 'musical_score', 'musical_score'),
            (b'\xf0\x9f\x94\x87', 'mute', 'mute'),
            (b'\xf0\x9f\x92\x85', 'nail_care', 'nail_care'),
            (b'\xf0\x9f\x92\x85\xf0\x9f\x8f\xbb', 'nail_care_tone1', 'nail_care_tone1'),
            (b'\xf0\x9f\x92\x85\xf0\x9f\x8f\xbc', 'nail_care_tone2', 'nail_care_tone2'),
            (b'\xf0\x9f\x92\x85\xf0\x9f\x8f\xbd', 'nail_care_tone3', 'nail_care_tone3'),
            (b'\xf0\x9f\x92\x85\xf0\x9f\x8f\xbe', 'nail_care_tone4', 'nail_care_tone4'),
            (b'\xf0\x9f\x92\x85\xf0\x9f\x8f\xbf', 'nail_care_tone5', 'nail_care_tone5'),
            (b'\xf0\x9f\x93\x9b', 'name_badge', 'name_badge'),
            (b'\xf0\x9f\x8f\x9e', 'national_park', 'national_park_vs16'),
            (b'\xf0\x9f\xa4\xa2', 'nauseated_face', 'nauseated_face', 'sick'),
            (b'\xf0\x9f\x91\x94', 'necktie', 'necktie'),
            (b'\xe2\x9d\x8e', 'negative_squared_cross_mark', 'negative_squared_cross_mark'),
            (b'\xf0\x9f\xa4\x93', 'nerd', 'nerd', 'nerd_face'),
            (b'\xf0\x9f\x86\x95', 'new', 'new'),
            (b'\xf0\x9f\x8c\x91', 'new_moon', 'new_moon'),
            (b'\xf0\x9f\x8c\x9a', 'new_moon_with_face', 'new_moon_with_face'),
            (b'\xf0\x9f\x97\x9e', 'newspaper2', 'newspaper2_vs16'),
            (b'\xf0\x9f\x93\xb0', 'newspaper', 'newspaper'),
            (b'\xe2\x8f\xad', 'next_track', 'next_track_vs16'),
            (b'\xf0\x9f\x86\x96', 'ng', 'ng'),
            (b'\xf0\x9f\x8c\x83', 'night_with_stars', 'night_with_stars'),
            (b'9\xe2\x83\xa3', 'nine', 'nine_vs16'),
            (b'\xf0\x9f\x94\x95', 'no_bell', 'no_bell'),
            (b'\xf0\x9f\x9a\xb3', 'no_bicycles', 'no_bicycles'),
            (b'\xe2\x9b\x94', 'no_entry', 'no_entry'),
            (b'\xf0\x9f\x9a\xab', 'no_entry_sign', 'no_entry_sign'),
            (b'\xf0\x9f\x99\x85', 'no_good', 'no_good', 'person_gesturing_no'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbb', 'no_good_tone1', 'no_good_tone1', 'person_gesturing_no_tone1'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbc', 'no_good_tone2', 'no_good_tone2', 'person_gesturing_no_tone2'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbd', 'no_good_tone3', 'no_good_tone3', 'person_gesturing_no_tone3'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbe', 'no_good_tone4', 'no_good_tone4', 'person_gesturing_no_tone4'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbf', 'no_good_tone5', 'no_good_tone5', 'person_gesturing_no_tone5'),
            (b'\xf0\x9f\x93\xb5', 'no_mobile_phones', 'no_mobile_phones'),
            (b'\xf0\x9f\x98\xb6', 'no_mouth', 'no_mouth'),
            (b'\xf0\x9f\x9a\xb7', 'no_pedestrians', 'no_pedestrians'),
            (b'\xf0\x9f\x9a\xad', 'no_smoking', 'no_smoking'),
            (b'\xf0\x9f\x9a\xb1', 'non_potable_water', 'non_potable_water'),
            (b'\xf0\x9f\x91\x83', 'nose', 'nose'),
            (b'\xf0\x9f\x91\x83\xf0\x9f\x8f\xbb', 'nose_tone1', 'nose_tone1'),
            (b'\xf0\x9f\x91\x83\xf0\x9f\x8f\xbc', 'nose_tone2', 'nose_tone2'),
            (b'\xf0\x9f\x91\x83\xf0\x9f\x8f\xbd', 'nose_tone3', 'nose_tone3'),
            (b'\xf0\x9f\x91\x83\xf0\x9f\x8f\xbe', 'nose_tone4', 'nose_tone4'),
            (b'\xf0\x9f\x91\x83\xf0\x9f\x8f\xbf', 'nose_tone5', 'nose_tone5'),
            (b'\xf0\x9f\x93\x93', 'notebook', 'notebook'),
            (b'\xf0\x9f\x93\x94', 'notebook_with_decorative_cover', 'notebook_with_decorative_cover'),
            (b'\xf0\x9f\x97\x92', 'notepad_spiral', 'notepad_spiral_vs16'),
            (b'\xf0\x9f\x8e\xb6', 'notes', 'notes'),
            (b'\xf0\x9f\x94\xa9', 'nut_and_bolt', 'nut_and_bolt'),
            (b'\xf0\x9f\x85\xbe', 'o2', 'o2_vs16'),
            (b'\xe2\xad\x95', 'o', 'o'),
            (b'\xf0\x9f\x8c\x8a', 'ocean', 'ocean'),
            (b'\xf0\x9f\x9b\x91', 'octagonal_sign', 'octagonal_sign', 'stop_sign'),
            (b'\xf0\x9f\x90\x99', 'octopus', 'octopus'),
            (b'\xf0\x9f\x8d\xa2', 'oden', 'oden'),
            (b'\xf0\x9f\x8f\xa2', 'office', 'office'),
            (b'\xf0\x9f\x9b\xa2', 'oil', 'oil_vs16'),
            (b'\xf0\x9f\x86\x97', 'ok', 'ok'),
            (b'\xf0\x9f\x91\x8c', 'ok_hand', 'ok_hand'),
            (b'\xf0\x9f\x91\x8c\xf0\x9f\x8f\xbb', 'ok_hand_tone1', 'ok_hand_tone1'),
            (b'\xf0\x9f\x91\x8c\xf0\x9f\x8f\xbc', 'ok_hand_tone2', 'ok_hand_tone2'),
            (b'\xf0\x9f\x91\x8c\xf0\x9f\x8f\xbd', 'ok_hand_tone3', 'ok_hand_tone3'),
            (b'\xf0\x9f\x91\x8c\xf0\x9f\x8f\xbe', 'ok_hand_tone4', 'ok_hand_tone4'),
            (b'\xf0\x9f\x91\x8c\xf0\x9f\x8f\xbf', 'ok_hand_tone5', 'ok_hand_tone5'),
            (b'\xf0\x9f\x99\x86', 'ok_woman', 'ok_woman', 'person_gesturing_ok'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbb', 'ok_woman_tone1', 'ok_woman_tone1', 'person_gesturing_ok_tone1'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbc', 'ok_woman_tone2', 'ok_woman_tone2', 'person_gesturing_ok_tone2'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbd', 'ok_woman_tone3', 'ok_woman_tone3', 'person_gesturing_ok_tone3'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbe', 'ok_woman_tone4', 'ok_woman_tone4', 'person_gesturing_ok_tone4'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbf', 'ok_woman_tone5', 'ok_woman_tone5', 'person_gesturing_ok_tone5'),
            (b'\xf0\x9f\x91\xb4', 'older_man', 'older_man'),
            (b'\xf0\x9f\x91\xb4\xf0\x9f\x8f\xbb', 'older_man_tone1', 'older_man_tone1'),
            (b'\xf0\x9f\x91\xb4\xf0\x9f\x8f\xbc', 'older_man_tone2', 'older_man_tone2'),
            (b'\xf0\x9f\x91\xb4\xf0\x9f\x8f\xbd', 'older_man_tone3', 'older_man_tone3'),
            (b'\xf0\x9f\x91\xb4\xf0\x9f\x8f\xbe', 'older_man_tone4', 'older_man_tone4'),
            (b'\xf0\x9f\x91\xb4\xf0\x9f\x8f\xbf', 'older_man_tone5', 'older_man_tone5'),
            (b'\xf0\x9f\x95\x89', 'om_symbol', 'om_symbol_vs16'),
            (b'\xf0\x9f\x94\x9b', 'on', 'on'),
            (b'\xf0\x9f\x9a\x98', 'oncoming_automobile', 'oncoming_automobile'),
            (b'\xf0\x9f\x9a\x8d', 'oncoming_bus', 'oncoming_bus'),
            (b'\xf0\x9f\x9a\x94', 'oncoming_police_car', 'oncoming_police_car'),
            (b'\xf0\x9f\x9a\x96', 'oncoming_taxi', 'oncoming_taxi'),
            (b'1\xe2\x83\xa3', 'one', 'one_vs16'),
            (b'\xf0\x9f\x93\x82', 'open_file_folder', 'open_file_folder'),
            (b'\xf0\x9f\x91\x90', 'open_hands', 'open_hands'),
            (b'\xf0\x9f\x91\x90\xf0\x9f\x8f\xbb', 'open_hands_tone1', 'open_hands_tone1'),
            (b'\xf0\x9f\x91\x90\xf0\x9f\x8f\xbc', 'open_hands_tone2', 'open_hands_tone2'),
            (b'\xf0\x9f\x91\x90\xf0\x9f\x8f\xbd', 'open_hands_tone3', 'open_hands_tone3'),
            (b'\xf0\x9f\x91\x90\xf0\x9f\x8f\xbe', 'open_hands_tone4', 'open_hands_tone4'),
            (b'\xf0\x9f\x91\x90\xf0\x9f\x8f\xbf', 'open_hands_tone5', 'open_hands_tone5'),
            (b'\xe2\x9b\x8e', 'ophiuchus', 'ophiuchus'),
            (b'\xf0\x9f\x93\x99', 'orange_book', 'orange_book'),
            (b'\xe2\x98\xa6', 'orthodox_cross', 'orthodox_cross_vs16'),
            (b'\xf0\x9f\x93\xa4', 'outbox_tray', 'outbox_tray'),
            (b'\xf0\x9f\xa6\x89', 'owl', 'owl'),
            (b'\xf0\x9f\x90\x82', 'ox', 'ox'),
            (b'\xf0\x9f\x93\xa6', 'package', 'package'),
            (b'\xf0\x9f\xa5\x98', 'paella', 'paella', 'shallow_pan_of_food'),
            (b'\xf0\x9f\x93\x84', 'page_facing_up', 'page_facing_up'),
            (b'\xf0\x9f\x93\x83', 'page_with_curl', 'page_with_curl'),
            (b'\xf0\x9f\x93\x9f', 'pager', 'pager'),
            (b'\xf0\x9f\x8c\xb4', 'palm_tree', 'palm_tree'),
            (b'\xf0\x9f\xa5\x9e', 'pancakes', 'pancakes'),
            (b'\xf0\x9f\x90\xbc', 'panda_face', 'panda_face'),
            (b'\xf0\x9f\x93\x8e', 'paperclip', 'paperclip'),
            (b'\xf0\x9f\x85\xbf', 'parking', 'parking_vs16'),
            (b'\xe3\x80\xbd', 'part_alternation_mark', 'part_alternation_mark_vs16'),
            (b'\xe2\x9b\x85', 'partly_sunny', 'partly_sunny'),
            (b'\xf0\x9f\x9b\x82', 'passport_control', 'passport_control'),
            (b'\xe2\x98\xae', 'peace', 'peace_vs16'),
            (b'\xf0\x9f\x8d\x91', 'peach', 'peach'),
            (b'\xf0\x9f\xa5\x9c', 'peanuts', 'peanuts', 'shelled_peanut'),
            (b'\xf0\x9f\x8d\x90', 'pear', 'pear'),
            (b'\xe2\x9c\x8f', 'pencil2', 'pencil2_vs16'),
            (b'\xf0\x9f\x93\x9d', 'pencil', 'pencil', 'memo'),
            (b'\xf0\x9f\x90\xa7', 'penguin', 'penguin'),
            (b'\xf0\x9f\x98\x94', 'pensive', 'pensive'),
            (b'\xf0\x9f\x8e\xad', 'performing_arts', 'performing_arts'),
            (b'\xf0\x9f\x98\xa3', 'persevere', 'persevere'),
            (b'\xf0\x9f\x99\x8d', 'person_frowning', 'person_frowning'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbb', 'person_frowning_tone1', 'person_frowning_tone1'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbc', 'person_frowning_tone2', 'person_frowning_tone2'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbd', 'person_frowning_tone3', 'person_frowning_tone3'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbe', 'person_frowning_tone4', 'person_frowning_tone4'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbf', 'person_frowning_tone5', 'person_frowning_tone5'),
            (b'\xf0\x9f\x91\xb1', 'person_with_blond_hair', 'person_with_blond_hair', 'blond_haired_person'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbb', 'person_with_blond_hair_tone1', 'person_with_blond_hair_tone1', 'blond_haired_person_tone1'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbc', 'person_with_blond_hair_tone2', 'person_with_blond_hair_tone2', 'blond_haired_person_tone2'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbd', 'person_with_blond_hair_tone3', 'person_with_blond_hair_tone3', 'blond_haired_person_tone3'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbe', 'person_with_blond_hair_tone4', 'person_with_blond_hair_tone4', 'blond_haired_person_tone4'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbf', 'person_with_blond_hair_tone5', 'person_with_blond_hair_tone5', 'blond_haired_person_tone5'),
            (b'\xf0\x9f\x99\x8e', 'person_with_pouting_face', 'person_with_pouting_face', 'person_pouting'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbb', 'person_with_pouting_face_tone1', 'person_with_pouting_face_tone1', 'person_pouting_tone1'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbc', 'person_with_pouting_face_tone2', 'person_with_pouting_face_tone2', 'person_pouting_tone2'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbd', 'person_with_pouting_face_tone3', 'person_with_pouting_face_tone3', 'person_pouting_tone3'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbe', 'person_with_pouting_face_tone4', 'person_with_pouting_face_tone4', 'person_pouting_tone4'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbf', 'person_with_pouting_face_tone5', 'person_with_pouting_face_tone5', 'person_pouting_tone5'),
            (b'\xe2\x9b\x8f', 'pick', 'pick_vs16'),
            (b'\xf0\x9f\x90\x96', 'pig2', 'pig2'),
            (b'\xf0\x9f\x90\xb7', 'pig', 'pig'),
            (b'\xf0\x9f\x90\xbd', 'pig_nose', 'pig_nose'),
            (b'\xf0\x9f\x92\x8a', 'pill', 'pill'),
            (b'\xf0\x9f\x8d\x8d', 'pineapple', 'pineapple'),
            (b'\xf0\x9f\x8f\x93', 'ping_pong', 'ping_pong', 'table_tennis'),
            (b'\xe2\x99\x93', 'pisces', 'pisces'),
            (b'\xf0\x9f\x8d\x95', 'pizza', 'pizza'),
            (b'\xf0\x9f\x9b\x90', 'place_of_worship', 'place_of_worship', 'worship_symbol'),
            (b'\xe2\x8f\xaf', 'play_pause', 'play_pause_vs16'),
            (b'\xf0\x9f\x91\x87', 'point_down', 'point_down'),
            (b'\xf0\x9f\x91\x87\xf0\x9f\x8f\xbb', 'point_down_tone1', 'point_down_tone1'),
            (b'\xf0\x9f\x91\x87\xf0\x9f\x8f\xbc', 'point_down_tone2', 'point_down_tone2'),
            (b'\xf0\x9f\x91\x87\xf0\x9f\x8f\xbd', 'point_down_tone3', 'point_down_tone3'),
            (b'\xf0\x9f\x91\x87\xf0\x9f\x8f\xbe', 'point_down_tone4', 'point_down_tone4'),
            (b'\xf0\x9f\x91\x87\xf0\x9f\x8f\xbf', 'point_down_tone5', 'point_down_tone5'),
            (b'\xf0\x9f\x91\x88', 'point_left', 'point_left'),
            (b'\xf0\x9f\x91\x88\xf0\x9f\x8f\xbb', 'point_left_tone1', 'point_left_tone1'),
            (b'\xf0\x9f\x91\x88\xf0\x9f\x8f\xbc', 'point_left_tone2', 'point_left_tone2'),
            (b'\xf0\x9f\x91\x88\xf0\x9f\x8f\xbd', 'point_left_tone3', 'point_left_tone3'),
            (b'\xf0\x9f\x91\x88\xf0\x9f\x8f\xbe', 'point_left_tone4', 'point_left_tone4'),
            (b'\xf0\x9f\x91\x88\xf0\x9f\x8f\xbf', 'point_left_tone5', 'point_left_tone5'),
            (b'\xf0\x9f\x91\x89', 'point_right', 'point_right'),
            (b'\xf0\x9f\x91\x89\xf0\x9f\x8f\xbb', 'point_right_tone1', 'point_right_tone1'),
            (b'\xf0\x9f\x91\x89\xf0\x9f\x8f\xbc', 'point_right_tone2', 'point_right_tone2'),
            (b'\xf0\x9f\x91\x89\xf0\x9f\x8f\xbd', 'point_right_tone3', 'point_right_tone3'),
            (b'\xf0\x9f\x91\x89\xf0\x9f\x8f\xbe', 'point_right_tone4', 'point_right_tone4'),
            (b'\xf0\x9f\x91\x89\xf0\x9f\x8f\xbf', 'point_right_tone5', 'point_right_tone5'),
            (b'\xe2\x98\x9d', 'point_up', 'point_up_vs16'),
            (b'\xe2\x98\x9d\xf0\x9f\x8f\xbb', 'point_up_tone1', 'point_up_tone1'),
            (b'\xe2\x98\x9d\xf0\x9f\x8f\xbc', 'point_up_tone2', 'point_up_tone2'),
            (b'\xe2\x98\x9d\xf0\x9f\x8f\xbd', 'point_up_tone3', 'point_up_tone3'),
            (b'\xe2\x98\x9d\xf0\x9f\x8f\xbe', 'point_up_tone4', 'point_up_tone4'),
            (b'\xe2\x98\x9d\xf0\x9f\x8f\xbf', 'point_up_tone5', 'point_up_tone5'),
            (b'\xf0\x9f\x91\x86', 'point_up_2', 'point_up_2'),
            (b'\xf0\x9f\x91\x86\xf0\x9f\x8f\xbb', 'point_up_2_tone1', 'point_up_2_tone1'),
            (b'\xf0\x9f\x91\x86\xf0\x9f\x8f\xbc', 'point_up_2_tone2', 'point_up_2_tone2'),
            (b'\xf0\x9f\x91\x86\xf0\x9f\x8f\xbd', 'point_up_2_tone3', 'point_up_2_tone3'),
            (b'\xf0\x9f\x91\x86\xf0\x9f\x8f\xbe', 'point_up_2_tone4', 'point_up_2_tone4'),
            (b'\xf0\x9f\x91\x86\xf0\x9f\x8f\xbf', 'point_up_2_tone5', 'point_up_2_tone5'),
            (b'\xf0\x9f\x9a\x93', 'police_car', 'police_car'),
            (b'\xf0\x9f\x90\xa9', 'poodle', 'poodle'),
            (b'\xf0\x9f\x8d\xbf', 'popcorn', 'popcorn'),
            (b'\xf0\x9f\x8f\xa3', 'post_office', 'post_office'),
            (b'\xf0\x9f\x93\xaf', 'postal_horn', 'postal_horn'),
            (b'\xf0\x9f\x93\xae', 'postbox', 'postbox'),
            (b'\xf0\x9f\x9a\xb0', 'potable_water', 'potable_water'),
            (b'\xf0\x9f\xa5\x94', 'potato', 'potato'),
            (b'\xf0\x9f\x91\x9d', 'pouch', 'pouch'),
            (b'\xf0\x9f\x8d\x97', 'poultry_leg', 'poultry_leg'),
            (b'\xf0\x9f\x92\xb7', 'pound', 'pound'),
            (b'\xf0\x9f\x98\xbe', 'pouting_cat', 'pouting_cat'),
            (b'\xf0\x9f\x99\x8f', 'pray', 'pray'),
            (b'\xf0\x9f\x99\x8f\xf0\x9f\x8f\xbb', 'pray_tone1', 'pray_tone1'),
            (b'\xf0\x9f\x99\x8f\xf0\x9f\x8f\xbc', 'pray_tone2', 'pray_tone2'),
            (b'\xf0\x9f\x99\x8f\xf0\x9f\x8f\xbd', 'pray_tone3', 'pray_tone3'),
            (b'\xf0\x9f\x99\x8f\xf0\x9f\x8f\xbe', 'pray_tone4', 'pray_tone4'),
            (b'\xf0\x9f\x99\x8f\xf0\x9f\x8f\xbf', 'pray_tone5', 'pray_tone5'),
            (b'\xf0\x9f\x93\xbf', 'prayer_beads', 'prayer_beads'),
            (b'\xe2\x8f\xae', 'previous_track', 'previous_track_vs16'),
            (b'\xf0\x9f\xa4\xb4', 'prince', 'prince'),
            (b'\xf0\x9f\xa4\xb4\xf0\x9f\x8f\xbb', 'prince_tone1', 'prince_tone1'),
            (b'\xf0\x9f\xa4\xb4\xf0\x9f\x8f\xbc', 'prince_tone2', 'prince_tone2'),
            (b'\xf0\x9f\xa4\xb4\xf0\x9f\x8f\xbd', 'prince_tone3', 'prince_tone3'),
            (b'\xf0\x9f\xa4\xb4\xf0\x9f\x8f\xbe', 'prince_tone4', 'prince_tone4'),
            (b'\xf0\x9f\xa4\xb4\xf0\x9f\x8f\xbf', 'prince_tone5', 'prince_tone5'),
            (b'\xf0\x9f\x91\xb8', 'princess', 'princess'),
            (b'\xf0\x9f\x91\xb8\xf0\x9f\x8f\xbb', 'princess_tone1', 'princess_tone1'),
            (b'\xf0\x9f\x91\xb8\xf0\x9f\x8f\xbc', 'princess_tone2', 'princess_tone2'),
            (b'\xf0\x9f\x91\xb8\xf0\x9f\x8f\xbd', 'princess_tone3', 'princess_tone3'),
            (b'\xf0\x9f\x91\xb8\xf0\x9f\x8f\xbe', 'princess_tone4', 'princess_tone4'),
            (b'\xf0\x9f\x91\xb8\xf0\x9f\x8f\xbf', 'princess_tone5', 'princess_tone5'),
            (b'\xf0\x9f\x96\xa8', 'printer', 'printer_vs16'),
            (b'\xf0\x9f\x91\x8a', 'punch', 'punch'),
            (b'\xf0\x9f\x91\x8a\xf0\x9f\x8f\xbb', 'punch_tone1', 'punch_tone1'),
            (b'\xf0\x9f\x91\x8a\xf0\x9f\x8f\xbc', 'punch_tone2', 'punch_tone2'),
            (b'\xf0\x9f\x91\x8a\xf0\x9f\x8f\xbd', 'punch_tone3', 'punch_tone3'),
            (b'\xf0\x9f\x91\x8a\xf0\x9f\x8f\xbe', 'punch_tone4', 'punch_tone4'),
            (b'\xf0\x9f\x91\x8a\xf0\x9f\x8f\xbf', 'punch_tone5', 'punch_tone5'),
            (b'\xf0\x9f\x92\x9c', 'purple_heart', 'purple_heart'),
            (b'\xf0\x9f\x91\x9b', 'purse', 'purse'),
            (b'\xf0\x9f\x93\x8c', 'pushpin', 'pushpin'),
            (b'\xf0\x9f\x9a\xae', 'put_litter_in_its_place', 'put_litter_in_its_place'),
            (b'\xe2\x9d\x93', 'question', 'question'),
            (b'\xf0\x9f\x90\x87', 'rabbit2', 'rabbit2'),
            (b'\xf0\x9f\x90\xb0', 'rabbit', 'rabbit'),
            (b'\xf0\x9f\x8f\x8e', 'race_car', 'race_car_vs16'),
            (b'\xf0\x9f\x90\x8e', 'racehorse', 'racehorse'),
            (b'\xf0\x9f\x93\xbb', 'radio', 'radio'),
            (b'\xf0\x9f\x94\x98', 'radio_button', 'radio_button'),
            (b'\xe2\x98\xa2', 'radioactive', 'radioactive_vs16'),
            (b'\xf0\x9f\x9b\xa4', 'railroad_track', 'railroad_track_vs16'),
            (b'\xf0\x9f\x9a\x83', 'railway_car', 'railway_car'),
            (b'\xf0\x9f\x8c\x88', 'rainbow', 'rainbow'),
            (b'\xe2\x9c\x8b', 'raised_hand', 'raised_hand'),
            (b'\xe2\x9c\x8b\xf0\x9f\x8f\xbb', 'raised_hand_tone1', 'raised_hand_tone1'),
            (b'\xe2\x9c\x8b\xf0\x9f\x8f\xbc', 'raised_hand_tone2', 'raised_hand_tone2'),
            (b'\xe2\x9c\x8b\xf0\x9f\x8f\xbd', 'raised_hand_tone3', 'raised_hand_tone3'),
            (b'\xe2\x9c\x8b\xf0\x9f\x8f\xbe', 'raised_hand_tone4', 'raised_hand_tone4'),
            (b'\xe2\x9c\x8b\xf0\x9f\x8f\xbf', 'raised_hand_tone5', 'raised_hand_tone5'),
            (b'\xf0\x9f\x96\x96', 'raised_hand_with_part_between_middle_and_ring_fingers', 'raised_hand_with_part_between_middle_and_ring_fingers', 'vulcan'),
            (b'\xf0\x9f\x96\x96\xf0\x9f\x8f\xbb', 'raised_hand_with_part_between_middle_and_ring_fingers_tone1', 'raised_hand_with_part_between_middle_and_ring_fingers_tone1', 'vulcan_tone1'),
            (b'\xf0\x9f\x96\x96\xf0\x9f\x8f\xbc', 'raised_hand_with_part_between_middle_and_ring_fingers_tone2', 'raised_hand_with_part_between_middle_and_ring_fingers_tone2', 'vulcan_tone2'),
            (b'\xf0\x9f\x96\x96\xf0\x9f\x8f\xbd', 'raised_hand_with_part_between_middle_and_ring_fingers_tone3', 'raised_hand_with_part_between_middle_and_ring_fingers_tone3', 'vulcan_tone3'),
            (b'\xf0\x9f\x96\x96\xf0\x9f\x8f\xbe', 'raised_hand_with_part_between_middle_and_ring_fingers_tone4', 'raised_hand_with_part_between_middle_and_ring_fingers_tone4', 'vulcan_tone4'),
            (b'\xf0\x9f\x96\x96\xf0\x9f\x8f\xbf', 'raised_hand_with_part_between_middle_and_ring_fingers_tone5', 'raised_hand_with_part_between_middle_and_ring_fingers_tone5', 'vulcan_tone5'),
            (b'\xf0\x9f\x99\x8c', 'raised_hands', 'raised_hands'),
            (b'\xf0\x9f\x99\x8c\xf0\x9f\x8f\xbb', 'raised_hands_tone1', 'raised_hands_tone1'),
            (b'\xf0\x9f\x99\x8c\xf0\x9f\x8f\xbc', 'raised_hands_tone2', 'raised_hands_tone2'),
            (b'\xf0\x9f\x99\x8c\xf0\x9f\x8f\xbd', 'raised_hands_tone3', 'raised_hands_tone3'),
            (b'\xf0\x9f\x99\x8c\xf0\x9f\x8f\xbe', 'raised_hands_tone4', 'raised_hands_tone4'),
            (b'\xf0\x9f\x99\x8c\xf0\x9f\x8f\xbf', 'raised_hands_tone5', 'raised_hands_tone5'),
            (b'\xf0\x9f\x99\x8b', 'raising_hand', 'raising_hand', 'person_raising_hand'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbb', 'raising_hand_tone1', 'raising_hand_tone1', 'person_raising_hand_tone1'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbc', 'raising_hand_tone2', 'raising_hand_tone2', 'person_raising_hand_tone2'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbd', 'raising_hand_tone3', 'raising_hand_tone3', 'person_raising_hand_tone3'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbe', 'raising_hand_tone4', 'raising_hand_tone4', 'person_raising_hand_tone4'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbf', 'raising_hand_tone5', 'raising_hand_tone5', 'person_raising_hand_tone5'),
            (b'\xf0\x9f\x90\x8f', 'ram', 'ram'),
            (b'\xf0\x9f\x8d\x9c', 'ramen', 'ramen'),
            (b'\xf0\x9f\x90\x80', 'rat', 'rat'),
            (b'\xe2\x8f\xba', 'record_button', 'record_button_vs16'),
            (b'\xe2\x99\xbb', 'recycle', 'recycle_vs16'),
            (b'\xf0\x9f\x9a\x97', 'red_car', 'red_car'),
            (b'\xf0\x9f\x94\xb4', 'red_circle', 'red_circle'),
            (b'\xf0\x9f\x87\xa6', 'regional_indicator_a', 'regional_indicator_a'),
            (b'\xf0\x9f\x87\xa7', 'regional_indicator_b', 'regional_indicator_b'),
            (b'\xf0\x9f\x87\xa8', 'regional_indicator_c', 'regional_indicator_c'),
            (b'\xf0\x9f\x87\xa9', 'regional_indicator_d', 'regional_indicator_d'),
            (b'\xf0\x9f\x87\xaa', 'regional_indicator_e', 'regional_indicator_e'),
            (b'\xf0\x9f\x87\xab', 'regional_indicator_f', 'regional_indicator_f'),
            (b'\xf0\x9f\x87\xac', 'regional_indicator_g', 'regional_indicator_g'),
            (b'\xf0\x9f\x87\xad', 'regional_indicator_h', 'regional_indicator_h'),
            (b'\xf0\x9f\x87\xae', 'regional_indicator_i', 'regional_indicator_i'),
            (b'\xf0\x9f\x87\xaf', 'regional_indicator_j', 'regional_indicator_j'),
            (b'\xf0\x9f\x87\xb0', 'regional_indicator_k', 'regional_indicator_k'),
            (b'\xf0\x9f\x87\xb1', 'regional_indicator_l', 'regional_indicator_l'),
            (b'\xf0\x9f\x87\xb2', 'regional_indicator_m', 'regional_indicator_m'),
            (b'\xf0\x9f\x87\xb3', 'regional_indicator_n', 'regional_indicator_n'),
            (b'\xf0\x9f\x87\xb4', 'regional_indicator_o', 'regional_indicator_o'),
            (b'\xf0\x9f\x87\xb5', 'regional_indicator_p', 'regional_indicator_p'),
            (b'\xf0\x9f\x87\xb6', 'regional_indicator_q', 'regional_indicator_q'),
            (b'\xf0\x9f\x87\xb7', 'regional_indicator_r', 'regional_indicator_r'),
            (b'\xf0\x9f\x87\xb8', 'regional_indicator_s', 'regional_indicator_s'),
            (b'\xf0\x9f\x87\xb9', 'regional_indicator_t', 'regional_indicator_t'),
            (b'\xf0\x9f\x87\xba', 'regional_indicator_u', 'regional_indicator_u'),
            (b'\xf0\x9f\x87\xbb', 'regional_indicator_v', 'regional_indicator_v'),
            (b'\xf0\x9f\x87\xbc', 'regional_indicator_w', 'regional_indicator_w'),
            (b'\xf0\x9f\x87\xbd', 'regional_indicator_x', 'regional_indicator_x'),
            (b'\xf0\x9f\x87\xbe', 'regional_indicator_y', 'regional_indicator_y'),
            (b'\xf0\x9f\x87\xbf', 'regional_indicator_z', 'regional_indicator_z'),
            (b'\xc2\xae', 'registered', 'registered_vs16'),
            (b'\xe2\x98\xba', 'relaxed', 'relaxed_vs16'),
            (b'\xf0\x9f\x98\x8c', 'relieved', 'relieved'),
            (b'\xf0\x9f\x8e\x97', 'reminder_ribbon', 'reminder_ribbon_vs16'),
            (b'\xf0\x9f\x94\x81', 'repeat', 'repeat'),
            (b'\xf0\x9f\x94\x82', 'repeat_one', 'repeat_one'),
            (b'\xf0\x9f\x9a\xbb', 'restroom', 'restroom'),
            (b'\xf0\x9f\x92\x9e', 'revolving_hearts', 'revolving_hearts'),
            (b'\xe2\x8f\xaa', 'rewind', 'rewind'),
            (b'\xf0\x9f\xa6\x8f', 'rhino', 'rhino', 'rhinoceros'),
            (b'\xf0\x9f\x8e\x80', 'ribbon', 'ribbon'),
            (b'\xf0\x9f\x8d\x9a', 'rice', 'rice'),
            (b'\xf0\x9f\x8d\x99', 'rice_ball', 'rice_ball'),
            (b'\xf0\x9f\x8d\x98', 'rice_cracker', 'rice_cracker'),
            (b'\xf0\x9f\x8e\x91', 'rice_scene', 'rice_scene'),
            (b'\xf0\x9f\xa4\x9c', 'right_facing_fist', 'right_facing_fist', 'right_fist'),
            (b'\xf0\x9f\xa4\x9c\xf0\x9f\x8f\xbb', 'right_facing_fist_tone1', 'right_facing_fist_tone1', 'right_fist_tone1'),
            (b'\xf0\x9f\xa4\x9c\xf0\x9f\x8f\xbc', 'right_facing_fist_tone2', 'right_facing_fist_tone2', 'right_fist_tone2'),
            (b'\xf0\x9f\xa4\x9c\xf0\x9f\x8f\xbd', 'right_facing_fist_tone3', 'right_facing_fist_tone3', 'right_fist_tone3'),
            (b'\xf0\x9f\xa4\x9c\xf0\x9f\x8f\xbe', 'right_facing_fist_tone4', 'right_facing_fist_tone4', 'right_fist_tone4'),
            (b'\xf0\x9f\xa4\x9c\xf0\x9f\x8f\xbf', 'right_facing_fist_tone5', 'right_facing_fist_tone5', 'right_fist_tone5'),
            (b'\xf0\x9f\x92\x8d', 'ring', 'ring'),
            (b'\xf0\x9f\xa4\x96', 'robot', 'robot', 'robot_face'),
            (b'\xf0\x9f\x9a\x80', 'rocket', 'rocket'),
            (b'\xf0\x9f\xa4\xa3', 'rofl', 'rofl', 'rolling_on_the_floor_laughing'),
            (b'\xf0\x9f\x8e\xa2', 'roller_coaster', 'roller_coaster'),
            (b'\xf0\x9f\x90\x93', 'rooster', 'rooster'),
            (b'\xf0\x9f\x8c\xb9', 'rose', 'rose'),
            (b'\xf0\x9f\x8f\xb5', 'rosette', 'rosette_vs16'),
            (b'\xf0\x9f\x9a\xa8', 'rotating_light', 'rotating_light'),
            (b'\xf0\x9f\x93\x8d', 'round_pushpin', 'round_pushpin'),
            (b'\xf0\x9f\x9a\xa3', 'rowboat', 'rowboat', 'person_rowing_boat'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbb', 'rowboat_tone1', 'rowboat_tone1', 'person_rowing_boat_tone1'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbc', 'rowboat_tone2', 'rowboat_tone2', 'person_rowing_boat_tone2'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbd', 'rowboat_tone3', 'rowboat_tone3', 'person_rowing_boat_tone3'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbe', 'rowboat_tone4', 'rowboat_tone4', 'person_rowing_boat_tone4'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbf', 'rowboat_tone5', 'rowboat_tone5', 'person_rowing_boat_tone5'),
            (b'\xf0\x9f\x8f\x89', 'rugby_football', 'rugby_football'),
            (b'\xf0\x9f\x8f\x83', 'runner', 'runner', 'person_running'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbb', 'runner_tone1', 'runner_tone1', 'person_running_tone1'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbc', 'runner_tone2', 'runner_tone2', 'person_running_tone2'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbd', 'runner_tone3', 'runner_tone3', 'person_running_tone3'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbe', 'runner_tone4', 'runner_tone4', 'person_running_tone4'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbf', 'runner_tone5', 'runner_tone5', 'person_running_tone5'),
            (b'\xf0\x9f\x8e\xbd', 'running_shirt_with_sash', 'running_shirt_with_sash'),
            (b'\xf0\x9f\x88\x82', 'sa', 'sa_vs16'),
            (b'\xe2\x99\x90', 'sagittarius', 'sagittarius'),
            (b'\xe2\x9b\xb5', 'sailboat', 'sailboat'),
            (b'\xf0\x9f\x8d\xb6', 'sake', 'sake'),
            (b'\xf0\x9f\x91\xa1', 'sandal', 'sandal'),
            (b'\xf0\x9f\x8e\x85', 'santa', 'santa'),
            (b'\xf0\x9f\x8e\x85\xf0\x9f\x8f\xbb', 'santa_tone1', 'santa_tone1'),
            (b'\xf0\x9f\x8e\x85\xf0\x9f\x8f\xbc', 'santa_tone2', 'santa_tone2'),
            (b'\xf0\x9f\x8e\x85\xf0\x9f\x8f\xbd', 'santa_tone3', 'santa_tone3'),
            (b'\xf0\x9f\x8e\x85\xf0\x9f\x8f\xbe', 'santa_tone4', 'santa_tone4'),
            (b'\xf0\x9f\x8e\x85\xf0\x9f\x8f\xbf', 'santa_tone5', 'santa_tone5'),
            (b'\xf0\x9f\x93\xa1', 'satellite', 'satellite'),
            (b'\xf0\x9f\x9b\xb0', 'satellite_orbital', 'satellite_orbital_vs16'),
            (b'\xf0\x9f\x8e\xb7', 'saxophone', 'saxophone'),
            (b'\xe2\x9a\x96', 'scales', 'scales_vs16'),
            (b'\xf0\x9f\x8f\xab', 'school', 'school'),
            (b'\xf0\x9f\x8e\x92', 'school_satchel', 'school_satchel'),
            (b'\xe2\x9c\x82', 'scissors', 'scissors_vs16'),
            (b'\xf0\x9f\x9b\xb4', 'scooter', 'scooter'),
            (b'\xf0\x9f\xa6\x82', 'scorpion', 'scorpion'),
            (b'\xe2\x99\x8f', 'scorpius', 'scorpius'),
            (b'\xf0\x9f\x98\xb1', 'scream', 'scream'),
            (b'\xf0\x9f\x99\x80', 'scream_cat', 'scream_cat'),
            (b'\xf0\x9f\x93\x9c', 'scroll', 'scroll'),
            (b'\xf0\x9f\x92\xba', 'seat', 'seat'),
            (b'\xf0\x9f\xa5\x88', 'second_place', 'second_place', 'second_place_medal'),
            (b'\xe3\x8a\x99', 'secret', 'secret_vs16'),
            (b'\xf0\x9f\x99\x88', 'see_no_evil', 'see_no_evil'),
            (b'\xf0\x9f\x8c\xb1', 'seedling', 'seedling'),
            (b'\xf0\x9f\xa4\xb3', 'selfie', 'selfie'),
            (b'\xf0\x9f\xa4\xb3\xf0\x9f\x8f\xbb', 'selfie_tone1', 'selfie_tone1'),
            (b'\xf0\x9f\xa4\xb3\xf0\x9f\x8f\xbc', 'selfie_tone2', 'selfie_tone2'),
            (b'\xf0\x9f\xa4\xb3\xf0\x9f\x8f\xbd', 'selfie_tone3', 'selfie_tone3'),
            (b'\xf0\x9f\xa4\xb3\xf0\x9f\x8f\xbe', 'selfie_tone4', 'selfie_tone4'),
            (b'\xf0\x9f\xa4\xb3\xf0\x9f\x8f\xbf', 'selfie_tone5', 'selfie_tone5'),
            (b'7\xe2\x83\xa3', 'seven', 'seven_vs16'),
            (b'\xe2\x98\x98', 'shamrock', 'shamrock_vs16'),
            (b'\xf0\x9f\xa6\x88', 'shark', 'shark'),
            (b'\xf0\x9f\x8d\xa7', 'shaved_ice', 'shaved_ice'),
            (b'\xf0\x9f\x90\x91', 'sheep', 'sheep'),
            (b'\xf0\x9f\x90\x9a', 'shell', 'shell'),
            (b'\xf0\x9f\x9b\xa1', 'shield', 'shield_vs16'),
            (b'\xe2\x9b\xa9', 'shinto_shrine', 'shinto_shrine_vs16'),
            (b'\xf0\x9f\x9a\xa2', 'ship', 'ship'),
            (b'\xf0\x9f\x91\x95', 'shirt', 'shirt'),
            (b'\xf0\x9f\x9b\x8d', 'shopping_bags', 'shopping_bags_vs16'),
            (b'\xf0\x9f\x9b\x92', 'shopping_cart', 'shopping_cart', 'shopping_trolley'),
            (b'\xf0\x9f\x9a\xbf', 'shower', 'shower'),
            (b'\xf0\x9f\xa6\x90', 'shrimp', 'shrimp'),
            (b'\xf0\x9f\xa4\xb7', 'shrug', 'shrug', 'person_shrugging'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbb', 'shrug_tone1', 'shrug_tone1', 'person_shrugging_tone1'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbc', 'shrug_tone2', 'shrug_tone2', 'person_shrugging_tone2'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbd', 'shrug_tone3', 'shrug_tone3', 'person_shrugging_tone3'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbe', 'shrug_tone4', 'shrug_tone4', 'person_shrugging_tone4'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbf', 'shrug_tone5', 'shrug_tone5', 'person_shrugging_tone5'),
            (b'\xf0\x9f\x93\xb6', 'signal_strength', 'signal_strength'),
            (b'6\xe2\x83\xa3', 'six', 'six_vs16'),
            (b'\xf0\x9f\x94\xaf', 'six_pointed_star', 'six_pointed_star'),
            (b'\xf0\x9f\x92\x80', 'skeleton', 'skeleton', 'skull'),
            (b'\xf0\x9f\x8e\xbf', 'ski', 'ski'),
            (b'\xe2\x9b\xb7', 'skier', 'skier_vs16'),
            (b'\xe2\x9b\xb7\xf0\x9f\x8f\xbb', 'skier_tone1', 'skier_tone1'),
            (b'\xe2\x9b\xb7\xf0\x9f\x8f\xbc', 'skier_tone2', 'skier_tone2'),
            (b'\xe2\x9b\xb7\xf0\x9f\x8f\xbd', 'skier_tone3', 'skier_tone3'),
            (b'\xe2\x9b\xb7\xf0\x9f\x8f\xbe', 'skier_tone4', 'skier_tone4'),
            (b'\xe2\x9b\xb7\xf0\x9f\x8f\xbf', 'skier_tone5', 'skier_tone5'),
            (b'\xe2\x98\xa0', 'skull_and_crossbones', 'skull_and_crossbones_vs16'),
            (b'\xf0\x9f\x98\xb4', 'sleeping', 'sleeping'),
            (b'\xf0\x9f\x9b\x8c', 'sleeping_accommodation', 'sleeping_accommodation'),
            (b'\xf0\x9f\x9b\x8c\xf0\x9f\x8f\xbb', 'sleeping_accommodation_tone1', 'sleeping_accommodation_tone1', 'person_in_bed_tone1'),
            (b'\xf0\x9f\x9b\x8c\xf0\x9f\x8f\xbc', 'sleeping_accommodation_tone2', 'sleeping_accommodation_tone2', 'person_in_bed_tone2'),
            (b'\xf0\x9f\x9b\x8c\xf0\x9f\x8f\xbd', 'sleeping_accommodation_tone3', 'sleeping_accommodation_tone3', 'person_in_bed_tone3'),
            (b'\xf0\x9f\x9b\x8c\xf0\x9f\x8f\xbe', 'sleeping_accommodation_tone4', 'sleeping_accommodation_tone4', 'person_in_bed_tone4'),
            (b'\xf0\x9f\x9b\x8c\xf0\x9f\x8f\xbf', 'sleeping_accommodation_tone5', 'sleeping_accommodation_tone5', 'person_in_bed_tone5'),
            (b'\xf0\x9f\x98\xaa', 'sleepy', 'sleepy'),
            (b'\xf0\x9f\x95\xb5', 'sleuth_or_spy', 'sleuth_or_spy', 'spy'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbb', 'sleuth_or_spy_tone1', 'sleuth_or_spy_tone1', 'spy_tone1', 'detective_tone1'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbc', 'sleuth_or_spy_tone2', 'sleuth_or_spy_tone2', 'spy_tone2', 'detective_tone2'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbd', 'sleuth_or_spy_tone3', 'sleuth_or_spy_tone3', 'spy_tone3', 'detective_tone3'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbe', 'sleuth_or_spy_tone4', 'sleuth_or_spy_tone4', 'spy_tone4', 'detective_tone4'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbf', 'sleuth_or_spy_tone5', 'sleuth_or_spy_tone5', 'spy_tone5', 'detective_tone5'),
            (b'\xf0\x9f\x99\x81', 'slight_frown', 'slight_frown', 'slightly_frowning_face'),
            (b'\xf0\x9f\x99\x82', 'slight_smile', 'slight_smile', 'slightly_smiling_face', ':)', ':-)', '=)', '=-)'),
            (b'\xf0\x9f\x8e\xb0', 'slot_machine', 'slot_machine'),
            (b'\xf0\x9f\x94\xb9', 'small_blue_diamond', 'small_blue_diamond'),
            (b'\xf0\x9f\x94\xb8', 'small_orange_diamond', 'small_orange_diamond'),
            (b'\xf0\x9f\x94\xba', 'small_red_triangle', 'small_red_triangle'),
            (b'\xf0\x9f\x94\xbb', 'small_red_triangle_down', 'small_red_triangle_down'),
            (b'\xf0\x9f\x98\xb8', 'smile_cat', 'smile_cat'),
            (b'\xf0\x9f\x98\xba', 'smiley_cat', 'smiley_cat'),
            (b'\xf0\x9f\x98\x88', 'smiling_imp', 'smiling_imp', ']:)', ']:-)', ']=)', ']=-)'),
            (b'\xf0\x9f\x98\x8f', 'smirk', 'smirk'),
            (b'\xf0\x9f\x98\xbc', 'smirk_cat', 'smirk_cat'),
            (b'\xf0\x9f\x9a\xac', 'smoking', 'smoking'),
            (b'\xf0\x9f\x90\x8c', 'snail', 'snail'),
            (b'\xf0\x9f\x90\x8d', 'snake', 'snake'),
            (b'\xf0\x9f\xa4\xa7', 'sneeze', 'sneeze', 'sneezing_face'),
            (b'\xf0\x9f\x8f\x82', 'snowboarder', 'snowboarder'),
            (b'\xf0\x9f\x8f\x82\xf0\x9f\x8f\xbb', 'snowboarder_tone1', 'snowboarder_tone1'),
            (b'\xf0\x9f\x8f\x82\xf0\x9f\x8f\xbc', 'snowboarder_tone2', 'snowboarder_tone2'),
            (b'\xf0\x9f\x8f\x82\xf0\x9f\x8f\xbd', 'snowboarder_tone3', 'snowboarder_tone3'),
            (b'\xf0\x9f\x8f\x82\xf0\x9f\x8f\xbe', 'snowboarder_tone4', 'snowboarder_tone4'),
            (b'\xf0\x9f\x8f\x82\xf0\x9f\x8f\xbf', 'snowboarder_tone5', 'snowboarder_tone5'),
            (b'\xe2\x9d\x84', 'snowflake', 'snowflake_vs16'),
            (b'\xe2\x98\x83', 'snowman2', 'snowman2_vs16'),
            (b'\xe2\x9b\x84', 'snowman', 'snowman'),
            (b'\xe2\x9a\xbd', 'soccer', 'soccer'),
            (b'\xf0\x9f\x94\x9c', 'soon', 'soon'),
            (b'\xf0\x9f\x86\x98', 'sos', 'sos'),
            (b'\xf0\x9f\x94\x89', 'sound', 'sound'),
            (b'\xf0\x9f\x91\xbe', 'space_invader', 'space_invader'),
            (b'\xe2\x99\xa0', 'spades', 'spades_vs16'),
            (b'\xf0\x9f\x8d\x9d', 'spaghetti', 'spaghetti'),
            (b'\xe2\x9d\x87', 'sparkle', 'sparkle_vs16'),
            (b'\xf0\x9f\x8e\x87', 'sparkler', 'sparkler'),
            (b'\xe2\x9c\xa8', 'sparkles', 'sparkles'),
            (b'\xf0\x9f\x92\x96', 'sparkling_heart', 'sparkling_heart'),
            (b'\xf0\x9f\x99\x8a', 'speak_no_evil', 'speak_no_evil'),
            (b'\xf0\x9f\x94\x88', 'speaker', 'speaker'),
            (b'\xf0\x9f\x97\xa3', 'speaking_head', 'speaking_head_vs16'),
            (b'\xf0\x9f\x92\xac', 'speech_balloon', 'speech_balloon'),
            (b'\xf0\x9f\x9a\xa4', 'speedboat', 'speedboat'),
            (b'\xf0\x9f\x95\xb7', 'spider', 'spider_vs16'),
            (b'\xf0\x9f\x95\xb8', 'spider_web', 'spider_web_vs16'),
            (b'\xf0\x9f\xa5\x84', 'spoon', 'spoon'),
            (b'\xf0\x9f\xa6\x91', 'squid', 'squid'),
            (b'\xf0\x9f\x8f\x9f', 'stadium', 'stadium_vs16'),
            (b'\xf0\x9f\x8c\x9f', 'star2', 'star2'),
            (b'\xe2\xad\x90', 'star', 'star'),
            (b'\xe2\x98\xaa', 'star_and_crescent', 'star_and_crescent_vs16'),
            (b'\xe2\x9c\xa1', 'star_of_david', 'star_of_david_vs16'),
            (b'\xf0\x9f\x8c\xa0', 'stars', 'stars'),
            (b'\xf0\x9f\x9a\x89', 'station', 'station'),
            (b'\xf0\x9f\x97\xbd', 'statue_of_liberty', 'statue_of_liberty'),
            (b'\xf0\x9f\x9a\x82', 'steam_locomotive', 'steam_locomotive'),
            (b'\xf0\x9f\x8d\xb2', 'stew', 'stew'),
            (b'\xe2\x8f\xb9', 'stop_button', 'stop_button_vs16'),
            (b'\xe2\x8f\xb1', 'stopwatch', 'stopwatch_vs16'),
            (b'\xf0\x9f\x93\x8f', 'straight_ruler', 'straight_ruler'),
            (b'\xf0\x9f\x8d\x93', 'strawberry', 'strawberry'),
            (b'\xf0\x9f\x98\x9d', 'stuck_out_tongue_closed_eyes', 'stuck_out_tongue_closed_eyes'),
            (b'\xf0\x9f\x98\x9c', 'stuck_out_tongue_winking_eye', 'stuck_out_tongue_winking_eye'),
            (b'\xf0\x9f\xa5\x99', 'stuffed_flatbread', 'stuffed_flatbread', 'stuffed_pita'),
            (b'\xf0\x9f\x8c\x9e', 'sun_with_face', 'sun_with_face'),
            (b'\xf0\x9f\x8c\xbb', 'sunflower', 'sunflower'),
            (b'\xe2\x98\x80', 'sunny', 'sunny_vs16'),
            (b'\xf0\x9f\x8c\x85', 'sunrise', 'sunrise'),
            (b'\xf0\x9f\x8c\x84', 'sunrise_over_mountains', 'sunrise_over_mountains'),
            (b'\xf0\x9f\x8f\x84', 'surfer', 'surfer', 'person_surfing'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbb', 'surfer_tone1', 'surfer_tone1', 'person_surfing_tone1'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbc', 'surfer_tone2', 'surfer_tone2', 'person_surfing_tone2'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbd', 'surfer_tone3', 'surfer_tone3', 'person_surfing_tone3'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbe', 'surfer_tone4', 'surfer_tone4', 'person_surfing_tone4'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbf', 'surfer_tone5', 'surfer_tone5', 'person_surfing_tone5'),
            (b'\xf0\x9f\x8d\xa3', 'sushi', 'sushi'),
            (b'\xf0\x9f\x9a\x9f', 'suspension_railway', 'suspension_railway'),
            (b'\xf0\x9f\x92\xa6', 'sweat_drops', 'sweat_drops'),
            (b'\xf0\x9f\x8d\xa0', 'sweet_potato', 'sweet_potato'),
            (b'\xf0\x9f\x8f\x8a', 'swimmer', 'swimmer', 'person_swimming'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbb', 'swimmer_tone1', 'swimmer_tone1', 'person_swimming_tone1'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbc', 'swimmer_tone2', 'swimmer_tone2', 'person_swimming_tone2'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbd', 'swimmer_tone3', 'swimmer_tone3', 'person_swimming_tone3'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbe', 'swimmer_tone4', 'swimmer_tone4', 'person_swimming_tone4'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbf', 'swimmer_tone5', 'swimmer_tone5', 'person_swimming_tone5'),
            (b'\xf0\x9f\x94\xa3', 'symbols', 'symbols'),
            (b'\xf0\x9f\x95\x8d', 'synagogue', 'synagogue'),
            (b'\xf0\x9f\x92\x89', 'syringe', 'syringe'),
            (b'\xf0\x9f\x8c\xae', 'taco', 'taco'),
            (b'\xf0\x9f\x8e\x89', 'tada', 'tada'),
            (b'\xf0\x9f\x8e\x8b', 'tanabata_tree', 'tanabata_tree'),
            (b'\xf0\x9f\x8d\x8a', 'tangerine', 'tangerine'),
            (b'\xe2\x99\x89', 'taurus', 'taurus'),
            (b'\xf0\x9f\x9a\x95', 'taxi', 'taxi'),
            (b'\xf0\x9f\x8d\xb5', 'tea', 'tea'),
            (b'\xe2\x98\x8e', 'telephone', 'telephone_vs16'),
            (b'\xf0\x9f\x93\x9e', 'telephone_receiver', 'telephone_receiver'),
            (b'\xf0\x9f\x94\xad', 'telescope', 'telescope'),
            (b'\xf0\x9f\x8e\xbe', 'tennis', 'tennis'),
            (b'\xe2\x9b\xba', 'tent', 'tent'),
            (b'\xf0\x9f\x8c\xa1', 'thermometer', 'thermometer_vs16'),
            (b'\xf0\x9f\xa4\x94', 'thinking', 'thinking', 'thinking_face'),
            (b'\xf0\x9f\xa5\x89', 'third_place', 'third_place', 'third_place_medal'),
            (b'\xf0\x9f\x92\xad', 'thought_balloon', 'thought_balloon'),
            (b'3\xe2\x83\xa3', 'three', 'three_vs16'),
            (b'\xe2\x9b\x88', 'thunder_cloud_and_rain', 'thunder_cloud_and_rain_vs16'),
            (b'\xf0\x9f\x8e\xab', 'ticket', 'ticket'),
            (b'\xf0\x9f\x90\x85', 'tiger2', 'tiger2'),
            (b'\xf0\x9f\x90\xaf', 'tiger', 'tiger'),
            (b'\xe2\x8f\xb2', 'timer', 'timer_vs16'),
            (b'\xf0\x9f\x98\xab', 'tired_face', 'tired_face'),
            (b'\xe2\x84\xa2', 'tm', 'tm_vs16'),
            (b'\xf0\x9f\x9a\xbd', 'toilet', 'toilet'),
            (b'\xf0\x9f\x97\xbc', 'tokyo_tower', 'tokyo_tower'),
            (b'\xf0\x9f\x8d\x85', 'tomato', 'tomato'),
            (b'\xf0\x9f\x91\x85', 'tongue', 'tongue'),
            (b'\xf0\x9f\x94\x9d', 'top', 'top'),
            (b'\xf0\x9f\x8e\xa9', 'tophat', 'tophat'),
            (b'\xf0\x9f\x96\xb2', 'trackball', 'trackball_vs16'),
            (b'\xf0\x9f\x9a\x9c', 'tractor', 'tractor'),
            (b'\xf0\x9f\x9a\xa5', 'traffic_light', 'traffic_light'),
            (b'\xf0\x9f\x9a\x86', 'train2', 'train2'),
            (b'\xf0\x9f\x9a\x8b', 'train', 'train'),
            (b'\xf0\x9f\x9a\x8a', 'tram', 'tram'),
            (b'\xf0\x9f\x9a\xa9', 'triangular_flag_on_post', 'triangular_flag_on_post'),
            (b'\xf0\x9f\x93\x90', 'triangular_ruler', 'triangular_ruler'),
            (b'\xf0\x9f\x94\xb1', 'trident', 'trident'),
            (b'\xf0\x9f\x98\xa4', 'triumph', 'triumph'),
            (b'\xf0\x9f\x9a\x8e', 'trolleybus', 'trolleybus'),
            (b'\xf0\x9f\x8f\x86', 'trophy', 'trophy'),
            (b'\xf0\x9f\x8d\xb9', 'tropical_drink', 'tropical_drink'),
            (b'\xf0\x9f\x90\xa0', 'tropical_fish', 'tropical_fish'),
            (b'\xf0\x9f\x9a\x9a', 'truck', 'truck'),
            (b'\xf0\x9f\x8e\xba', 'trumpet', 'trumpet'),
            (b'\xf0\x9f\x8c\xb7', 'tulip', 'tulip'),
            (b'\xf0\x9f\xa5\x83', 'tumbler_glass', 'tumbler_glass', 'whisky'),
            (b'\xf0\x9f\xa6\x83', 'turkey', 'turkey'),
            (b'\xf0\x9f\x90\xa2', 'turtle', 'turtle'),
            (b'\xf0\x9f\x93\xba', 'tv', 'tv'),
            (b'\xf0\x9f\x94\x80', 'twisted_rightwards_arrows', 'twisted_rightwards_arrows'),
            (b'2\xe2\x83\xa3', 'two', 'two_vs16'),
            (b'\xf0\x9f\x92\x95', 'two_hearts', 'two_hearts'),
            (b'\xf0\x9f\x91\xac', 'two_men_holding_hands', 'two_men_holding_hands'),
            (b'\xf0\x9f\x91\xad', 'two_women_holding_hands', 'two_women_holding_hands'),
            (b'\xf0\x9f\x88\xb9', 'u5272', 'u5272'),
            (b'\xf0\x9f\x88\xb4', 'u5408', 'u5408'),
            (b'\xf0\x9f\x88\xba', 'u55b6', 'u55b6'),
            (b'\xf0\x9f\x88\xaf', 'u6307', 'u6307'),
            (b'\xf0\x9f\x88\xb7', 'u6708', 'u6708_vs16'),
            (b'\xf0\x9f\x88\xb6', 'u6709', 'u6709'),
            (b'\xf0\x9f\x88\xb5', 'u6e80', 'u6e80'),
            (b'\xf0\x9f\x88\x9a', 'u7121', 'u7121'),
            (b'\xf0\x9f\x88\xb8', 'u7533', 'u7533'),
            (b'\xf0\x9f\x88\xb2', 'u7981', 'u7981'),
            (b'\xf0\x9f\x88\xb3', 'u7a7a', 'u7a7a'),
            (b'\xe2\x98\x82', 'umbrella2', 'umbrella2_vs16'),
            (b'\xe2\x98\x94', 'umbrella', 'umbrella'),
            (b'\xf0\x9f\x94\x9e', 'underage', 'underage'),
            (b'\xf0\x9f\xa6\x84', 'unicorn', 'unicorn', 'unicorn_face'),
            (b'\xf0\x9f\x94\x93', 'unlock', 'unlock'),
            (b'\xf0\x9f\x86\x99', 'up', 'up'),
            (b'\xf0\x9f\x99\x83', 'upside_down', 'upside_down', 'upside_down_face'),
            (b'\xe2\x9c\x8c', 'v', 'v_vs16'),
            (b'\xe2\x9c\x8c\xf0\x9f\x8f\xbb', 'v_tone1', 'v_tone1'),
            (b'\xe2\x9c\x8c\xf0\x9f\x8f\xbc', 'v_tone2', 'v_tone2'),
            (b'\xe2\x9c\x8c\xf0\x9f\x8f\xbd', 'v_tone3', 'v_tone3'),
            (b'\xe2\x9c\x8c\xf0\x9f\x8f\xbe', 'v_tone4', 'v_tone4'),
            (b'\xe2\x9c\x8c\xf0\x9f\x8f\xbf', 'v_tone5', 'v_tone5'),
            (b'\xf0\x9f\x9a\xa6', 'vertical_traffic_light', 'vertical_traffic_light'),
            (b'\xf0\x9f\x93\xbc', 'vhs', 'vhs'),
            (b'\xf0\x9f\x93\xb3', 'vibration_mode', 'vibration_mode'),
            (b'\xf0\x9f\x93\xb9', 'video_camera', 'video_camera'),
            (b'\xf0\x9f\x8e\xae', 'video_game', 'video_game'),
            (b'\xf0\x9f\x8e\xbb', 'violin', 'violin'),
            (b'\xe2\x99\x8d', 'virgo', 'virgo'),
            (b'\xf0\x9f\x8c\x8b', 'volcano', 'volcano'),
            (b'\xf0\x9f\x8f\x90', 'volleyball', 'volleyball'),
            (b'\xf0\x9f\x86\x9a', 'vs', 'vs'),
            (b'\xf0\x9f\x9a\xb6', 'walking', 'walking', 'person_walking'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbb', 'walking_tone1', 'walking_tone1', 'person_walking_tone1'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbc', 'walking_tone2', 'walking_tone2', 'person_walking_tone2'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbd', 'walking_tone3', 'walking_tone3', 'person_walking_tone3'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbe', 'walking_tone4', 'walking_tone4', 'person_walking_tone4'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbf', 'walking_tone5', 'walking_tone5', 'person_walking_tone5'),
            (b'\xf0\x9f\x8c\x98', 'waning_crescent_moon', 'waning_crescent_moon'),
            (b'\xf0\x9f\x8c\x96', 'waning_gibbous_moon', 'waning_gibbous_moon'),
            (b'\xe2\x9a\xa0', 'warning', 'warning_vs16'),
            (b'\xf0\x9f\x97\x91', 'wastebasket', 'wastebasket_vs16'),
            (b'\xe2\x8c\x9a', 'watch', 'watch'),
            (b'\xf0\x9f\x90\x83', 'water_buffalo', 'water_buffalo'),
            (b'\xf0\x9f\xa4\xbd', 'water_polo', 'water_polo', 'person_playing_water_polo'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbb', 'water_polo_tone1', 'water_polo_tone1', 'person_playing_water_polo_tone1'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbc', 'water_polo_tone2', 'water_polo_tone2', 'person_playing_water_polo_tone2'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbd', 'water_polo_tone3', 'water_polo_tone3', 'person_playing_water_polo_tone3'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbe', 'water_polo_tone4', 'water_polo_tone4', 'person_playing_water_polo_tone4'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbf', 'water_polo_tone5', 'water_polo_tone5', 'person_playing_water_polo_tone5'),
            (b'\xf0\x9f\x8d\x89', 'watermelon', 'watermelon'),
            (b'\xf0\x9f\x91\x8b', 'wave', 'wave'),
            (b'\xf0\x9f\x91\x8b\xf0\x9f\x8f\xbb', 'wave_tone1', 'wave_tone1'),
            (b'\xf0\x9f\x91\x8b\xf0\x9f\x8f\xbc', 'wave_tone2', 'wave_tone2'),
            (b'\xf0\x9f\x91\x8b\xf0\x9f\x8f\xbd', 'wave_tone3', 'wave_tone3'),
            (b'\xf0\x9f\x91\x8b\xf0\x9f\x8f\xbe', 'wave_tone4', 'wave_tone4'),
            (b'\xf0\x9f\x91\x8b\xf0\x9f\x8f\xbf', 'wave_tone5', 'wave_tone5'),
            (b'\xe3\x80\xb0', 'wavy_dash', 'wavy_dash_vs16'),
            (b'\xf0\x9f\x8c\x92', 'waxing_crescent_moon', 'waxing_crescent_moon'),
            (b'\xf0\x9f\x8c\x94', 'waxing_gibbous_moon', 'waxing_gibbous_moon'),
            (b'\xf0\x9f\x9a\xbe', 'wc', 'wc'),
            (b'\xf0\x9f\x98\xa9', 'weary', 'weary'),
            (b'\xf0\x9f\x92\x92', 'wedding', 'wedding'),
            (b'\xf0\x9f\x90\x8b', 'whale2', 'whale2'),
            (b'\xf0\x9f\x90\xb3', 'whale', 'whale'),
            (b'\xe2\x98\xb8', 'wheel_of_dharma', 'wheel_of_dharma_vs16'),
            (b'\xe2\x99\xbf', 'wheelchair', 'wheelchair'),
            (b'\xe2\x9c\x85', 'white_check_mark', 'white_check_mark'),
            (b'\xe2\x9a\xaa', 'white_circle', 'white_circle'),
            (b'\xf0\x9f\x92\xae', 'white_flower', 'white_flower'),
            (b'\xe2\xac\x9c', 'white_large_square', 'white_large_square'),
            (b'\xe2\x97\xbd', 'white_medium_small_square', 'white_medium_small_square'),
            (b'\xe2\x97\xbb', 'white_medium_square', 'white_medium_square_vs16'),
            (b'\xe2\x96\xab', 'white_small_square', 'white_small_square_vs16'),
            (b'\xf0\x9f\x94\xb3', 'white_square_button', 'white_square_button'),
            (b'\xf0\x9f\x8c\xa5', 'white_sun_behind_cloud', 'white_sun_behind_cloud_vs16'),
            (b'\xf0\x9f\x8c\xa6', 'white_sun_behind_cloud_with_rain', 'white_sun_behind_cloud_with_rain_vs16'),
            (b'\xf0\x9f\x8c\xa4', 'white_sun_small_cloud', 'white_sun_small_cloud_vs16'),
            (b'\xf0\x9f\xa5\x80', 'wilted_flower', 'wilted_flower', 'wilted_rose'),
            (b'\xf0\x9f\x8c\xac', 'wind_blowing_face', 'wind_blowing_face_vs16'),
            (b'\xf0\x9f\x8e\x90', 'wind_chime', 'wind_chime'),
            (b'\xf0\x9f\x8d\xb7', 'wine_glass', 'wine_glass'),
            (b'\xf0\x9f\x98\x89', 'wink', 'wink', ';)', ';-)'),
            (b'\xf0\x9f\x90\xba', 'wolf', 'wolf'),
            (b'\xf0\x9f\x91\xa9', 'woman', 'woman'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb', 'woman_tone1', 'woman_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc', 'woman_tone2', 'woman_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd', 'woman_tone3', 'woman_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe', 'woman_tone4', 'woman_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf', 'woman_tone5', 'woman_tone5'),
            (b'\xf0\x9f\x91\x9a', 'womans_clothes', 'womans_clothes'),
            (b'\xf0\x9f\x91\x92', 'womans_hat', 'womans_hat'),
            (b'\xf0\x9f\x9a\xba', 'womens', 'womens'),
            (b'\xf0\x9f\x98\x9f', 'worried', 'worried'),
            (b'\xf0\x9f\x94\xa7', 'wrench', 'wrench'),
            (b'\xf0\x9f\xa4\xbc', 'wrestlers', 'wrestlers', 'wrestling', 'people_wrestling'),
            (b'\xe2\x9c\x8d', 'writing_hand', 'writing_hand_vs16'),
            (b'\xe2\x9c\x8d\xf0\x9f\x8f\xbb', 'writing_hand_tone1', 'writing_hand_tone1'),
            (b'\xe2\x9c\x8d\xf0\x9f\x8f\xbc', 'writing_hand_tone2', 'writing_hand_tone2'),
            (b'\xe2\x9c\x8d\xf0\x9f\x8f\xbd', 'writing_hand_tone3', 'writing_hand_tone3'),
            (b'\xe2\x9c\x8d\xf0\x9f\x8f\xbe', 'writing_hand_tone4', 'writing_hand_tone4'),
            (b'\xe2\x9c\x8d\xf0\x9f\x8f\xbf', 'writing_hand_tone5', 'writing_hand_tone5'),
            (b'\xe2\x9d\x8c', 'x', 'x'),
            (b'\xf0\x9f\x92\x9b', 'yellow_heart', 'yellow_heart'),
            (b'\xf0\x9f\x92\xb4', 'yen', 'yen'),
            (b'\xe2\x98\xaf', 'yin_yang', 'yin_yang_vs16'),
            (b'\xf0\x9f\x98\x8b', 'yum', 'yum'),
            (b'\xe2\x9a\xa1', 'zap', 'zap'),
            (b'0\xe2\x83\xa3', 'zero', 'zero_vs16'),
            (b'\xf0\x9f\xa4\x90', 'zipper_mouth', 'zipper_mouth', 'zipper_mouth_face'),
            (b'\xf0\x9f\x92\xa4', 'zzz', 'zzz'),
            (b'\xf0\x9f\x85\xb0\xef\xb8\x8f', 'a', 'a'),
            (b'\xf0\x9f\xa7\xae', 'abacus', 'abacus'),
            (b'\xf0\x9f\xa9\xb9', 'adhesive_bandage', 'adhesive_bandage'),
            (b'\xf0\x9f\x8e\x9f\xef\xb8\x8f', 'admission_tickets', 'admission_tickets', 'tickets'),
            (b'\xf0\x9f\xa7\x91', 'adult', 'adult'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb', 'adult_tone1', 'adult_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc', 'adult_tone2', 'adult_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd', 'adult_tone3', 'adult_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe', 'adult_tone4', 'adult_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf', 'adult_tone5', 'adult_tone5'),
            (b'\xe2\x9c\x88\xef\xb8\x8f', 'airplane', 'airplane'),
            (b'\xf0\x9f\x9b\xa9\xef\xb8\x8f', 'airplane_small', 'airplane_small', 'small_airplane'),
            (b'\xe2\x9a\x97\xef\xb8\x8f', 'alembic', 'alembic'),
            (b'\xf0\x9f\x97\xaf\xef\xb8\x8f', 'anger_right', 'anger_right', 'right_anger_bubble'),
            (b'\xe2\x97\x80\xef\xb8\x8f', 'arrow_backward', 'arrow_backward'),
            (b'\xe2\xac\x87\xef\xb8\x8f', 'arrow_down', 'arrow_down'),
            (b'\xe2\x96\xb6\xef\xb8\x8f', 'arrow_forward', 'arrow_forward'),
            (b'\xe2\xa4\xb5\xef\xb8\x8f', 'arrow_heading_down', 'arrow_heading_down'),
            (b'\xe2\xa4\xb4\xef\xb8\x8f', 'arrow_heading_up', 'arrow_heading_up'),
            (b'\xe2\xac\x85\xef\xb8\x8f', 'arrow_left', 'arrow_left'),
            (b'\xe2\x86\x99\xef\xb8\x8f', 'arrow_lower_left', 'arrow_lower_left'),
            (b'\xe2\x86\x98\xef\xb8\x8f', 'arrow_lower_right', 'arrow_lower_right'),
            (b'\xe2\x9e\xa1\xef\xb8\x8f', 'arrow_right', 'arrow_right'),
            (b'\xe2\x86\xaa\xef\xb8\x8f', 'arrow_right_hook', 'arrow_right_hook'),
            (b'\xe2\xac\x86\xef\xb8\x8f', 'arrow_up', 'arrow_up'),
            (b'\xe2\x86\x95\xef\xb8\x8f', 'arrow_up_down', 'arrow_up_down'),
            (b'\xe2\x86\x96\xef\xb8\x8f', 'arrow_upper_left', 'arrow_upper_left'),
            (b'\xe2\x86\x97\xef\xb8\x8f', 'arrow_upper_right', 'arrow_upper_right'),
            (b'*\xef\xb8\x8f\xe2\x83\xa3', 'asterisk', 'asterisk', 'keycap_asterisk'),
            (b'\xe2\x9a\x9b\xef\xb8\x8f', 'atom', 'atom', 'atom_symbol'),
            (b'\xf0\x9f\x9b\xba', 'auto_rickshaw', 'auto_rickshaw'),
            (b'\xf0\x9f\xaa\x93', 'axe', 'axe'),
            (b'\xf0\x9f\x85\xb1\xef\xb8\x8f', 'b', 'b'),
            (b'\xf0\x9f\xa6\xa1', 'badger', 'badger'),
            (b'\xf0\x9f\xa5\xaf', 'bagel', 'bagel'),
            (b'\xf0\x9f\xa9\xb0', 'ballet_shoes', 'ballet_shoes'),
            (b'\xf0\x9f\x97\xb3\xef\xb8\x8f', 'ballot_box', 'ballot_box', 'ballot_box_with_ballot'),
            (b'\xe2\x98\x91\xef\xb8\x8f', 'ballot_box_with_check', 'ballot_box_with_check'),
            (b'\xe2\x80\xbc\xef\xb8\x8f', 'bangbang', 'bangbang'),
            (b'\xf0\x9f\xaa\x95', 'banjo', 'banjo'),
            (b'\xf0\x9f\xa7\xba', 'basket', 'basket'),
            (b'\xe2\x9b\xb9\xef\xb8\x8f', 'basketball_player', 'basketball_player', 'person_bouncing_ball', 'person_with_ball'),
            (b'\xf0\x9f\x8f\x96\xef\xb8\x8f', 'beach', 'beach', 'beach_with_umbrella'),
            (b'\xe2\x9b\xb1\xef\xb8\x8f', 'beach_umbrella', 'beach_umbrella', 'umbrella_on_ground'),
            (b'\xf0\x9f\xa7\x94', 'bearded_person', 'bearded_person'),
            (b'\xf0\x9f\xa7\x94\xf0\x9f\x8f\xbb', 'bearded_person_tone1', 'bearded_person_tone1'),
            (b'\xf0\x9f\xa7\x94\xf0\x9f\x8f\xbc', 'bearded_person_tone2', 'bearded_person_tone2'),
            (b'\xf0\x9f\xa7\x94\xf0\x9f\x8f\xbd', 'bearded_person_tone3', 'bearded_person_tone3'),
            (b'\xf0\x9f\xa7\x94\xf0\x9f\x8f\xbe', 'bearded_person_tone4', 'bearded_person_tone4'),
            (b'\xf0\x9f\xa7\x94\xf0\x9f\x8f\xbf', 'bearded_person_tone5', 'bearded_person_tone5'),
            (b'\xf0\x9f\x9b\x8f\xef\xb8\x8f', 'bed', 'bed'),
            (b'\xf0\x9f\x9b\x8e\xef\xb8\x8f', 'bellhop', 'bellhop', 'bellhop_bell'),
            (b'\xf0\x9f\xa7\x83', 'beverage_box', 'beverage_box'),
            (b'\xf0\x9f\xa7\xa2', 'billed_cap', 'billed_cap'),
            (b'\xe2\x98\xa3\xef\xb8\x8f', 'biohazard', 'biohazard', 'biohazard_sign'),
            (b'\xe2\x97\xbc\xef\xb8\x8f', 'black_medium_square', 'black_medium_square'),
            (b'\xe2\x9c\x92\xef\xb8\x8f', 'black_nib', 'black_nib'),
            (b'\xe2\x96\xaa\xef\xb8\x8f', 'black_small_square', 'black_small_square'),
            (b'\xf0\x9f\x91\xb1\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'blond_haired_man', 'blond_haired_man'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'blond_haired_man_tone1', 'blond_haired_man_tone1'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'blond_haired_man_tone2', 'blond_haired_man_tone2'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'blond_haired_man_tone3', 'blond_haired_man_tone3'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'blond_haired_man_tone4', 'blond_haired_man_tone4'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'blond_haired_man_tone5', 'blond_haired_man_tone5'),
            (b'\xf0\x9f\x91\xb1\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'blond_haired_woman', 'blond_haired_woman'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'blond_haired_woman_tone1', 'blond_haired_woman_tone1'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'blond_haired_woman_tone2', 'blond_haired_woman_tone2'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'blond_haired_woman_tone3', 'blond_haired_woman_tone3'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'blond_haired_woman_tone4', 'blond_haired_woman_tone4'),
            (b'\xf0\x9f\x91\xb1\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'blond_haired_woman_tone5', 'blond_haired_woman_tone5'),
            (b'\xf0\x9f\x9f\xa6', 'blue_square', 'blue_square'),
            (b'\xf0\x9f\xa6\xb4', 'bone', 'bone'),
            (b'\xf0\x9f\xa5\xa3', 'bowl_with_spoon', 'bowl_with_spoon'),
            (b'\xf0\x9f\xa7\xa0', 'brain', 'brain'),
            (b'\xf0\x9f\xa4\xb1', 'breast_feeding', 'breast_feeding'),
            (b'\xf0\x9f\xa4\xb1\xf0\x9f\x8f\xbb', 'breast_feeding_tone1', 'breast_feeding_tone1'),
            (b'\xf0\x9f\xa4\xb1\xf0\x9f\x8f\xbc', 'breast_feeding_tone2', 'breast_feeding_tone2'),
            (b'\xf0\x9f\xa4\xb1\xf0\x9f\x8f\xbd', 'breast_feeding_tone3', 'breast_feeding_tone3'),
            (b'\xf0\x9f\xa4\xb1\xf0\x9f\x8f\xbe', 'breast_feeding_tone4', 'breast_feeding_tone4'),
            (b'\xf0\x9f\xa4\xb1\xf0\x9f\x8f\xbf', 'breast_feeding_tone5', 'breast_feeding_tone5'),
            (b'\xf0\x9f\xa7\xb1', 'bricks', 'bricks'),
            (b'\xf0\x9f\xa9\xb2', 'briefs', 'briefs'),
            (b'\xf0\x9f\xa5\xa6', 'broccoli', 'broccoli'),
            (b'\xf0\x9f\xa7\xb9', 'broom', 'broom'),
            (b'\xf0\x9f\x9f\xa4', 'brown_circle', 'brown_circle'),
            (b'\xf0\x9f\xa4\x8e', 'brown_heart', 'brown_heart'),
            (b'\xf0\x9f\x9f\xab', 'brown_square', 'brown_square'),
            (b'\xf0\x9f\x8f\x97\xef\xb8\x8f', 'building_construction', 'building_construction', 'construction_site'),
            (b'\xf0\x9f\xa7\x88', 'butter', 'butter'),
            (b'\xf0\x9f\x97\x93\xef\xb8\x8f', 'calendar_spiral', 'calendar_spiral', 'spiral_calendar_pad'),
            (b'\xf0\x9f\x8f\x95\xef\xb8\x8f', 'camping', 'camping'),
            (b'\xf0\x9f\x95\xaf\xef\xb8\x8f', 'candle', 'candle'),
            (b'\xf0\x9f\xa5\xab', 'canned_food', 'canned_food'),
            (b'\xf0\x9f\x97\x83\xef\xb8\x8f', 'card_box', 'card_box', 'card_file_box'),
            (b'\xf0\x9f\x97\x82\xef\xb8\x8f', 'card_index_dividers', 'card_index_dividers', 'dividers'),
            (b'\xe2\x9b\x93\xef\xb8\x8f', 'chains', 'chains'),
            (b'\xf0\x9f\xaa\x91', 'chair', 'chair'),
            (b'\xe2\x99\x9f\xef\xb8\x8f', 'chess_pawn', 'chess_pawn'),
            (b'\xf0\x9f\xa7\x92', 'child', 'child'),
            (b'\xf0\x9f\xa7\x92\xf0\x9f\x8f\xbb', 'child_tone1', 'child_tone1'),
            (b'\xf0\x9f\xa7\x92\xf0\x9f\x8f\xbc', 'child_tone2', 'child_tone2'),
            (b'\xf0\x9f\xa7\x92\xf0\x9f\x8f\xbd', 'child_tone3', 'child_tone3'),
            (b'\xf0\x9f\xa7\x92\xf0\x9f\x8f\xbe', 'child_tone4', 'child_tone4'),
            (b'\xf0\x9f\xa7\x92\xf0\x9f\x8f\xbf', 'child_tone5', 'child_tone5'),
            (b'\xf0\x9f\x90\xbf\xef\xb8\x8f', 'chipmunk', 'chipmunk'),
            (b'\xf0\x9f\xa5\xa2', 'chopsticks', 'chopsticks'),
            (b'\xf0\x9f\x8f\x99\xef\xb8\x8f', 'cityscape', 'cityscape'),
            (b'\xf0\x9f\x8f\x9b\xef\xb8\x8f', 'classical_building', 'classical_building'),
            (b'\xf0\x9f\x95\xb0\xef\xb8\x8f', 'clock', 'clock', 'mantlepiece_clock'),
            (b'\xe2\x98\x81\xef\xb8\x8f', 'cloud', 'cloud'),
            (b'\xf0\x9f\x8c\xa9\xef\xb8\x8f', 'cloud_lightning', 'cloud_lightning', 'cloud_with_lightning'),
            (b'\xf0\x9f\x8c\xa7\xef\xb8\x8f', 'cloud_rain', 'cloud_rain', 'cloud_with_rain'),
            (b'\xf0\x9f\x8c\xa8\xef\xb8\x8f', 'cloud_snow', 'cloud_snow', 'cloud_with_snow'),
            (b'\xf0\x9f\x8c\xaa\xef\xb8\x8f', 'cloud_tornado', 'cloud_tornado', 'cloud_with_tornado'),
            (b'\xe2\x99\xa3\xef\xb8\x8f', 'clubs', 'clubs'),
            (b'\xf0\x9f\xa7\xa5', 'coat', 'coat'),
            (b'\xf0\x9f\xa5\xa5', 'coconut', 'coconut'),
            (b'\xe2\x9a\xb0\xef\xb8\x8f', 'coffin', 'coffin'),
            (b'\xf0\x9f\xa5\xb6', 'cold_face', 'cold_face'),
            (b'\xe2\x98\x84\xef\xb8\x8f', 'comet', 'comet'),
            (b'\xf0\x9f\xa7\xad', 'compass', 'compass'),
            (b'\xf0\x9f\x97\x9c\xef\xb8\x8f', 'compression', 'compression'),
            (b'\xe3\x8a\x97\xef\xb8\x8f', 'congratulations', 'congratulations'),
            (b'\xf0\x9f\x8e\x9b\xef\xb8\x8f', 'control_knobs', 'control_knobs'),
            (b'\xc2\xa9\xef\xb8\x8f', 'copyright', 'copyright'),
            (b'\xf0\x9f\x9b\x8b\xef\xb8\x8f', 'couch', 'couch', 'couch_and_lamp'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xe2\x9d\xa4\xef\xb8\x8f\xe2\x80\x8d\xf0\x9f\x91\xa8', 'couple_with_heart_woman_man', 'couple_with_heart_woman_man'),
            (b'\xf0\x9f\x96\x8d\xef\xb8\x8f', 'crayon', 'crayon', 'lower_left_crayon'),
            (b'\xf0\x9f\xa6\x97', 'cricket', 'cricket', 'cricket_game', 'cricket_bat_ball'),
            (b'\xe2\x9c\x9d\xef\xb8\x8f', 'cross', 'cross', 'latin_cross'),
            (b'\xe2\x9a\x94\xef\xb8\x8f', 'crossed_swords', 'crossed_swords'),
            (b'\xf0\x9f\x9b\xb3\xef\xb8\x8f', 'cruise_ship', 'cruise_ship', 'passenger_ship'),
            (b'\xf0\x9f\xa5\xa4', 'cup_with_straw', 'cup_with_straw'),
            (b'\xf0\x9f\xa7\x81', 'cupcake', 'cupcake'),
            (b'\xf0\x9f\xa5\x8c', 'curling_stone', 'curling_stone'),
            (b'\xf0\x9f\xa5\xa9', 'cut_of_meat', 'cut_of_meat'),
            (b'\xf0\x9f\x97\xa1\xef\xb8\x8f', 'dagger', 'dagger', 'dagger_knife'),
            (b'\xf0\x9f\x95\xb6\xef\xb8\x8f', 'dark_sunglasses', 'dark_sunglasses'),
            (b'\xf0\x9f\xa7\x8f\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'deaf_man', 'deaf_man'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'deaf_man_tone1', 'deaf_man_tone1'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'deaf_man_tone2', 'deaf_man_tone2'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'deaf_man_tone3', 'deaf_man_tone3'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'deaf_man_tone4', 'deaf_man_tone4'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'deaf_man_tone5', 'deaf_man_tone5'),
            (b'\xf0\x9f\xa7\x8f', 'deaf_person', 'deaf_person'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbb', 'deaf_person_tone1', 'deaf_person_tone1'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbc', 'deaf_person_tone2', 'deaf_person_tone2'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbd', 'deaf_person_tone3', 'deaf_person_tone3'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbe', 'deaf_person_tone4', 'deaf_person_tone4'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbf', 'deaf_person_tone5', 'deaf_person_tone5'),
            (b'\xf0\x9f\xa7\x8f\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'deaf_woman', 'deaf_woman'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'deaf_woman_tone1', 'deaf_woman_tone1'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'deaf_woman_tone2', 'deaf_woman_tone2'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'deaf_woman_tone3', 'deaf_woman_tone3'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'deaf_woman_tone4', 'deaf_woman_tone4'),
            (b'\xf0\x9f\xa7\x8f\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'deaf_woman_tone5', 'deaf_woman_tone5'),
            (b'\xf0\x9f\x8f\x9a\xef\xb8\x8f', 'derelict_house_building', 'derelict_house_building', 'house_abandoned'),
            (b'\xf0\x9f\x8f\x9c\xef\xb8\x8f', 'desert', 'desert'),
            (b'\xf0\x9f\x8f\x9d\xef\xb8\x8f', 'desert_island', 'desert_island', 'island'),
            (b'\xf0\x9f\x96\xa5\xef\xb8\x8f', 'desktop', 'desktop', 'desktop_computer'),
            (b'\xf0\x9f\x95\xb5\xef\xb8\x8f', 'detective', 'detective', 'sleuth_or_spy', 'spy'),
            (b'\xe2\x99\xa6\xef\xb8\x8f', 'diamonds', 'diamonds'),
            (b'\xf0\x9f\xa4\xbf', 'diving_mask', 'diving_mask'),
            (b'\xf0\x9f\xaa\x94', 'diya_lamp', 'diya_lamp'),
            (b'\xf0\x9f\xa7\xac', 'dna', 'dna'),
            (b'\xe2\x8f\xb8\xef\xb8\x8f', 'double_vertical_bar', 'double_vertical_bar', 'pause_button'),
            (b'\xf0\x9f\x95\x8a\xef\xb8\x8f', 'dove', 'dove', 'dove_of_peace'),
            (b'\xf0\x9f\xa9\xb8', 'drop_of_blood', 'drop_of_blood'),
            (b'\xf0\x9f\xa5\x9f', 'dumpling', 'dumpling'),
            (b'\xf0\x9f\xa6\xbb', 'ear_with_hearing_aid', 'ear_with_hearing_aid'),
            (b'\xf0\x9f\xa6\xbb\xf0\x9f\x8f\xbb', 'ear_with_hearing_aid_tone1', 'ear_with_hearing_aid_tone1'),
            (b'\xf0\x9f\xa6\xbb\xf0\x9f\x8f\xbc', 'ear_with_hearing_aid_tone2', 'ear_with_hearing_aid_tone2'),
            (b'\xf0\x9f\xa6\xbb\xf0\x9f\x8f\xbd', 'ear_with_hearing_aid_tone3', 'ear_with_hearing_aid_tone3'),
            (b'\xf0\x9f\xa6\xbb\xf0\x9f\x8f\xbe', 'ear_with_hearing_aid_tone4', 'ear_with_hearing_aid_tone4'),
            (b'\xf0\x9f\xa6\xbb\xf0\x9f\x8f\xbf', 'ear_with_hearing_aid_tone5', 'ear_with_hearing_aid_tone5'),
            (b'8\xef\xb8\x8f\xe2\x83\xa3', 'eight', 'eight'),
            (b'\xe2\x9c\xb4\xef\xb8\x8f', 'eight_pointed_black_star', 'eight_pointed_black_star'),
            (b'\xe2\x9c\xb3\xef\xb8\x8f', 'eight_spoked_asterisk', 'eight_spoked_asterisk'),
            (b'\xe2\x8f\x8f\xef\xb8\x8f', 'eject', 'eject', 'eject_symbol'),
            (b'\xf0\x9f\xa7\x9d', 'elf', 'elf'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbb', 'elf_tone1', 'elf_tone1'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbc', 'elf_tone2', 'elf_tone2'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbd', 'elf_tone3', 'elf_tone3'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbe', 'elf_tone4', 'elf_tone4'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbf', 'elf_tone5', 'elf_tone5'),
            (b'\xf0\x9f\x8f\xb4\xf3\xa0\x81\xa7\xf3\xa0\x81\xa2\xf3\xa0\x81\xa5\xf3\xa0\x81\xae\xf3\xa0\x81\xa7\xf3\xa0\x81\xbf', 'england', 'england'),
            (b'\xe2\x9c\x89\xef\xb8\x8f', 'envelope', 'envelope'),
            (b'\xf0\x9f\xa4\xaf', 'exploding_head', 'exploding_head'),
            (b'\xf0\x9f\x91\x81\xef\xb8\x8f', 'eye', 'eye'),
            (b'\xf0\x9f\xa4\xae', 'face_vomiting', 'face_vomiting'),
            (b'\xf0\x9f\xa4\xad', 'face_with_hand_over_mouth', 'face_with_hand_over_mouth'),
            (b'\xf0\x9f\xa7\x90', 'face_with_monocle', 'face_with_monocle'),
            (b'\xf0\x9f\xa4\xa8', 'face_with_raised_eyebrow', 'face_with_raised_eyebrow'),
            (b'\xf0\x9f\xa4\xac', 'face_with_symbols_over_mouth', 'face_with_symbols_over_mouth'),
            (b'\xf0\x9f\xa7\x9a', 'fairy', 'fairy'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbb', 'fairy_tone1', 'fairy_tone1'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbc', 'fairy_tone2', 'fairy_tone2'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbd', 'fairy_tone3', 'fairy_tone3'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbe', 'fairy_tone4', 'fairy_tone4'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbf', 'fairy_tone5', 'fairy_tone5'),
            (b'\xf0\x9f\xa7\x86', 'falafel', 'falafel'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_man_boy', 'family_man_boy'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa6\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_man_boy_boy', 'family_man_boy_boy'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa7', 'family_man_girl', 'family_man_girl'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa7\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_man_girl_boy', 'family_man_girl_boy'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa7\xe2\x80\x8d\xf0\x9f\x91\xa7', 'family_man_girl_girl', 'family_man_girl_girl'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_man_woman_boy', 'family_man_woman_boy'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_woman_boy', 'family_woman_boy'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa6\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_woman_boy_boy', 'family_woman_boy_boy'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa7', 'family_woman_girl', 'family_woman_girl'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa7\xe2\x80\x8d\xf0\x9f\x91\xa6', 'family_woman_girl_boy', 'family_woman_girl_boy'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x91\xa7\xe2\x80\x8d\xf0\x9f\x91\xa7', 'family_woman_girl_girl', 'family_woman_girl_girl'),
            (b'\xe2\x99\x80\xef\xb8\x8f', 'female_sign', 'female_sign'),
            (b'\xe2\x9b\xb4\xef\xb8\x8f', 'ferry', 'ferry'),
            (b'\xf0\x9f\x97\x84\xef\xb8\x8f', 'file_cabinet', 'file_cabinet'),
            (b'\xf0\x9f\x8e\x9e\xef\xb8\x8f', 'film_frames', 'film_frames'),
            (b'\xf0\x9f\x93\xbd\xef\xb8\x8f', 'film_projector', 'film_projector', 'projector'),
            (b'\xf0\x9f\xa7\xaf', 'fire_extinguisher', 'fire_extinguisher'),
            (b'\xf0\x9f\xa7\xa8', 'firecracker', 'firecracker'),
            (b'5\xef\xb8\x8f\xe2\x83\xa3', 'five', 'five'),
            (b'\xf0\x9f\x8f\xb3\xef\xb8\x8f', 'flag_white', 'flag_white'),
            (b'\xf0\x9f\xa6\xa9', 'flamingo', 'flamingo'),
            (b'\xe2\x9a\x9c\xef\xb8\x8f', 'fleur_de_lis', 'fleur_de_lis'),
            (b'\xf0\x9f\xa5\x8f', 'flying_disc', 'flying_disc'),
            (b'\xf0\x9f\x9b\xb8', 'flying_saucer', 'flying_saucer'),
            (b'\xf0\x9f\x8c\xab\xef\xb8\x8f', 'fog', 'fog'),
            (b'\xf0\x9f\xa6\xb6', 'foot', 'foot'),
            (b'\xf0\x9f\xa6\xb6\xf0\x9f\x8f\xbb', 'foot_tone1', 'foot_tone1'),
            (b'\xf0\x9f\xa6\xb6\xf0\x9f\x8f\xbc', 'foot_tone2', 'foot_tone2'),
            (b'\xf0\x9f\xa6\xb6\xf0\x9f\x8f\xbd', 'foot_tone3', 'foot_tone3'),
            (b'\xf0\x9f\xa6\xb6\xf0\x9f\x8f\xbe', 'foot_tone4', 'foot_tone4'),
            (b'\xf0\x9f\xa6\xb6\xf0\x9f\x8f\xbf', 'foot_tone5', 'foot_tone5'),
            (b'\xf0\x9f\x8d\xbd\xef\xb8\x8f', 'fork_and_knife_with_plate', 'fork_and_knife_with_plate', 'fork_knife_plate'),
            (b'\xf0\x9f\xa5\xa0', 'fortune_cookie', 'fortune_cookie'),
            (b'4\xef\xb8\x8f\xe2\x83\xa3', 'four', 'four'),
            (b'\xf0\x9f\x96\xbc\xef\xb8\x8f', 'frame_photo', 'frame_photo', 'frame_with_picture'),
            (b'\xe2\x98\xb9\xef\xb8\x8f', 'frowning2', 'frowning2', 'white_frowning_face'),
            (b'\xe2\x9a\xb1\xef\xb8\x8f', 'funeral_urn', 'funeral_urn', 'urn'),
            (b'\xf0\x9f\xa7\x84', 'garlic', 'garlic'),
            (b'\xe2\x9a\x99\xef\xb8\x8f', 'gear', 'gear'),
            (b'\xf0\x9f\xa7\x9e', 'genie', 'genie'),
            (b'\xf0\x9f\xa6\x92', 'giraffe', 'giraffe'),
            (b'\xf0\x9f\xa7\xa4', 'gloves', 'gloves'),
            (b'\xf0\x9f\xa5\xbd', 'goggles', 'goggles'),
            (b'\xf0\x9f\x8f\x8c\xef\xb8\x8f', 'golfer', 'golfer', 'person_golfing'),
            (b'\xf0\x9f\x9f\xa2', 'green_circle', 'green_circle'),
            (b'\xf0\x9f\x9f\xa9', 'green_square', 'green_square'),
            (b'\xf0\x9f\xa6\xae', 'guide_dog', 'guide_dog'),
            (b'\xe2\x9a\x92\xef\xb8\x8f', 'hammer_and_pick', 'hammer_and_pick', 'hammer_pick'),
            (b'\xf0\x9f\x9b\xa0\xef\xb8\x8f', 'hammer_and_wrench', 'hammer_and_wrench', 'tools'),
            (b'\xf0\x9f\x96\x90\xef\xb8\x8f', 'hand_splayed', 'hand_splayed', 'raised_hand_with_fingers_splayed'),
            (b'#\xef\xb8\x8f\xe2\x83\xa3', 'hash', 'hash'),
            (b'\xe2\x9d\xa4\xef\xb8\x8f', 'heart', 'heart', '<3', '♡'),
            (b'\xe2\x9d\xa3\xef\xb8\x8f', 'heart_exclamation', 'heart_exclamation', 'heavy_heart_exclamation_mark_ornament'),
            (b'\xe2\x99\xa5\xef\xb8\x8f', 'hearts', 'hearts'),
            (b'\xe2\x9c\x94\xef\xb8\x8f', 'heavy_check_mark', 'heavy_check_mark'),
            (b'\xe2\x9c\x96\xef\xb8\x8f', 'heavy_multiplication_x', 'heavy_multiplication_x'),
            (b'\xf0\x9f\xa6\x94', 'hedgehog', 'hedgehog'),
            (b'\xe2\x9b\x91\xef\xb8\x8f', 'helmet_with_cross', 'helmet_with_cross', 'helmet_with_white_cross'),
            (b'\xf0\x9f\xa5\xbe', 'hiking_boot', 'hiking_boot'),
            (b'\xf0\x9f\x9b\x95', 'hindu_temple', 'hindu_temple'),
            (b'\xf0\x9f\xa6\x9b', 'hippopotamus', 'hippopotamus'),
            (b'\xf0\x9f\x95\xb3\xef\xb8\x8f', 'hole', 'hole'),
            (b'\xf0\x9f\x8f\x98\xef\xb8\x8f', 'homes', 'homes', 'house_buildings'),
            (b'\xf0\x9f\xa5\xb5', 'hot_face', 'hot_face'),
            (b'\xf0\x9f\x8c\xb6\xef\xb8\x8f', 'hot_pepper', 'hot_pepper'),
            (b'\xe2\x99\xa8\xef\xb8\x8f', 'hotsprings', 'hotsprings'),
            (b'\xf0\x9f\xa7\x8a', 'ice_cube', 'ice_cube'),
            (b'\xe2\x9b\xb8\xef\xb8\x8f', 'ice_skate', 'ice_skate'),
            (b'\xe2\x99\xbe\xef\xb8\x8f', 'infinity', 'infinity'),
            (b'\xe2\x84\xb9\xef\xb8\x8f', 'information_source', 'information_source'),
            (b'\xe2\x81\x89\xef\xb8\x8f', 'interrobang', 'interrobang'),
            (b'\xf0\x9f\xa7\xa9', 'jigsaw', 'jigsaw'),
            (b'\xf0\x9f\x95\xb9\xef\xb8\x8f', 'joystick', 'joystick'),
            (b'\xf0\x9f\xa6\x98', 'kangaroo', 'kangaroo'),
            (b'\xf0\x9f\x97\x9d\xef\xb8\x8f', 'key2', 'key2', 'key_vs16'),
            (b'\xe2\x8c\xa8\xef\xb8\x8f', 'keyboard', 'keyboard'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xe2\x9d\xa4\xef\xb8\x8f\xe2\x80\x8d\xf0\x9f\x92\x8b\xe2\x80\x8d\xf0\x9f\x91\xa8', 'kiss_woman_man', 'kiss_woman_man'),
            (b'\xf0\x9f\xaa\x81', 'kite', 'kite'),
            (b'\xf0\x9f\xa5\xbc', 'lab_coat', 'lab_coat'),
            (b'\xf0\x9f\x8f\xb7\xef\xb8\x8f', 'label', 'label'),
            (b'\xf0\x9f\xa5\x8d', 'lacrosse', 'lacrosse'),
            (b'\xf0\x9f\xa5\xac', 'leafy_green', 'leafy_green'),
            (b'\xe2\x86\x94\xef\xb8\x8f', 'left_right_arrow', 'left_right_arrow'),
            (b'\xf0\x9f\x97\xa8\xef\xb8\x8f', 'left_speech_bubble', 'left_speech_bubble', 'speech_left'),
            (b'\xe2\x86\xa9\xef\xb8\x8f', 'leftwards_arrow_with_hook', 'leftwards_arrow_with_hook'),
            (b'\xf0\x9f\xa6\xb5', 'leg', 'leg'),
            (b'\xf0\x9f\xa6\xb5\xf0\x9f\x8f\xbb', 'leg_tone1', 'leg_tone1'),
            (b'\xf0\x9f\xa6\xb5\xf0\x9f\x8f\xbc', 'leg_tone2', 'leg_tone2'),
            (b'\xf0\x9f\xa6\xb5\xf0\x9f\x8f\xbd', 'leg_tone3', 'leg_tone3'),
            (b'\xf0\x9f\xa6\xb5\xf0\x9f\x8f\xbe', 'leg_tone4', 'leg_tone4'),
            (b'\xf0\x9f\xa6\xb5\xf0\x9f\x8f\xbf', 'leg_tone5', 'leg_tone5'),
            (b'\xf0\x9f\x8e\x9a\xef\xb8\x8f', 'level_slider', 'level_slider'),
            (b'\xf0\x9f\x95\xb4\xef\xb8\x8f', 'levitate', 'levitate', 'man_in_business_suit_levitating'),
            (b'\xf0\x9f\x8f\x8b\xef\xb8\x8f', 'lifter', 'lifter', 'person_lifting_weights', 'weight_lifter'),
            (b'\xf0\x9f\x96\x87\xef\xb8\x8f', 'linked_paperclips', 'linked_paperclips', 'paperclips'),
            (b'\xf0\x9f\xa6\x99', 'llama', 'llama'),
            (b'\xf0\x9f\xa6\x9e', 'lobster', 'lobster'),
            (b'\xf0\x9f\xa4\x9f', 'love_you_gesture', 'love_you_gesture'),
            (b'\xf0\x9f\xa4\x9f\xf0\x9f\x8f\xbb', 'love_you_gesture_tone1', 'love_you_gesture_tone1'),
            (b'\xf0\x9f\xa4\x9f\xf0\x9f\x8f\xbc', 'love_you_gesture_tone2', 'love_you_gesture_tone2'),
            (b'\xf0\x9f\xa4\x9f\xf0\x9f\x8f\xbd', 'love_you_gesture_tone3', 'love_you_gesture_tone3'),
            (b'\xf0\x9f\xa4\x9f\xf0\x9f\x8f\xbe', 'love_you_gesture_tone4', 'love_you_gesture_tone4'),
            (b'\xf0\x9f\xa4\x9f\xf0\x9f\x8f\xbf', 'love_you_gesture_tone5', 'love_you_gesture_tone5'),
            (b'\xf0\x9f\x96\x8a\xef\xb8\x8f', 'lower_left_ballpoint_pen', 'lower_left_ballpoint_pen', 'pen_ballpoint'),
            (b'\xf0\x9f\x96\x8b\xef\xb8\x8f', 'lower_left_fountain_pen', 'lower_left_fountain_pen', 'pen_fountain'),
            (b'\xf0\x9f\x96\x8c\xef\xb8\x8f', 'lower_left_paintbrush', 'lower_left_paintbrush', 'paintbrush'),
            (b'\xf0\x9f\xa7\xb3', 'luggage', 'luggage'),
            (b'\xe2\x93\x82\xef\xb8\x8f', 'm', 'm'),
            (b'\xf0\x9f\xa7\x99', 'mage', 'mage'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbb', 'mage_tone1', 'mage_tone1'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbc', 'mage_tone2', 'mage_tone2'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbd', 'mage_tone3', 'mage_tone3'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbe', 'mage_tone4', 'mage_tone4'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbf', 'mage_tone5', 'mage_tone5'),
            (b'\xf0\x9f\xa7\xb2', 'magnet', 'magnet'),
            (b'\xe2\x99\x82\xef\xb8\x8f', 'male_sign', 'male_sign'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'man_artist', 'man_artist'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'man_artist_tone1', 'man_artist_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'man_artist_tone2', 'man_artist_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'man_artist_tone3', 'man_artist_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'man_artist_tone4', 'man_artist_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'man_artist_tone5', 'man_artist_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x9a\x80', 'man_astronaut', 'man_astronaut'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x9a\x80', 'man_astronaut_tone1', 'man_astronaut_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x9a\x80', 'man_astronaut_tone2', 'man_astronaut_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x9a\x80', 'man_astronaut_tone3', 'man_astronaut_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x9a\x80', 'man_astronaut_tone4', 'man_astronaut_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x9a\x80', 'man_astronaut_tone5', 'man_astronaut_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'man_bald', 'man_bald'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'man_bald_tone1', 'man_bald_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'man_bald_tone2', 'man_bald_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'man_bald_tone3', 'man_bald_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'man_bald_tone4', 'man_bald_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'man_bald_tone5', 'man_bald_tone5'),
            (b'\xf0\x9f\x9a\xb4\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_biking', 'man_biking'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_biking_tone1', 'man_biking_tone1'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_biking_tone2', 'man_biking_tone2'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_biking_tone3', 'man_biking_tone3'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_biking_tone4', 'man_biking_tone4'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_biking_tone5', 'man_biking_tone5'),
            (b'\xe2\x9b\xb9\xef\xb8\x8f\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_bouncing_ball', 'man_bouncing_ball'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_bouncing_ball_tone1', 'man_bouncing_ball_tone1'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_bouncing_ball_tone2', 'man_bouncing_ball_tone2'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_bouncing_ball_tone3', 'man_bouncing_ball_tone3'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_bouncing_ball_tone4', 'man_bouncing_ball_tone4'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_bouncing_ball_tone5', 'man_bouncing_ball_tone5'),
            (b'\xf0\x9f\x99\x87\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_bowing', 'man_bowing'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_bowing_tone1', 'man_bowing_tone1'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_bowing_tone2', 'man_bowing_tone2'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_bowing_tone3', 'man_bowing_tone3'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_bowing_tone4', 'man_bowing_tone4'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_bowing_tone5', 'man_bowing_tone5'),
            (b'\xf0\x9f\xa4\xb8\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_cartwheeling', 'man_cartwheeling'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_cartwheeling_tone1', 'man_cartwheeling_tone1'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_cartwheeling_tone2', 'man_cartwheeling_tone2'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_cartwheeling_tone3', 'man_cartwheeling_tone3'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_cartwheeling_tone4', 'man_cartwheeling_tone4'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_cartwheeling_tone5', 'man_cartwheeling_tone5'),
            (b'\xf0\x9f\xa7\x97\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_climbing', 'man_climbing'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_climbing_tone1', 'man_climbing_tone1'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_climbing_tone2', 'man_climbing_tone2'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_climbing_tone3', 'man_climbing_tone3'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_climbing_tone4', 'man_climbing_tone4'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_climbing_tone5', 'man_climbing_tone5'),
            (b'\xf0\x9f\x91\xb7\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_construction_worker', 'man_construction_worker'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_construction_worker_tone1', 'man_construction_worker_tone1'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_construction_worker_tone2', 'man_construction_worker_tone2'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_construction_worker_tone3', 'man_construction_worker_tone3'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_construction_worker_tone4', 'man_construction_worker_tone4'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_construction_worker_tone5', 'man_construction_worker_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'man_cook', 'man_cook'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'man_cook_tone1', 'man_cook_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'man_cook_tone2', 'man_cook_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'man_cook_tone3', 'man_cook_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'man_cook_tone4', 'man_cook_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'man_cook_tone5', 'man_cook_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'man_curly_haired', 'man_curly_haired'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'man_curly_haired_tone1', 'man_curly_haired_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'man_curly_haired_tone2', 'man_curly_haired_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'man_curly_haired_tone3', 'man_curly_haired_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'man_curly_haired_tone4', 'man_curly_haired_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'man_curly_haired_tone5', 'man_curly_haired_tone5'),
            (b'\xf0\x9f\x95\xb5\xef\xb8\x8f\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_detective', 'man_detective'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_detective_tone1', 'man_detective_tone1'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_detective_tone2', 'man_detective_tone2'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_detective_tone3', 'man_detective_tone3'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_detective_tone4', 'man_detective_tone4'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_detective_tone5', 'man_detective_tone5'),
            (b'\xf0\x9f\xa7\x9d\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_elf', 'man_elf'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_elf_tone1', 'man_elf_tone1'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_elf_tone2', 'man_elf_tone2'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_elf_tone3', 'man_elf_tone3'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_elf_tone4', 'man_elf_tone4'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_elf_tone5', 'man_elf_tone5'),
            (b'\xf0\x9f\xa4\xa6\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_facepalming', 'man_facepalming'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_facepalming_tone1', 'man_facepalming_tone1'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_facepalming_tone2', 'man_facepalming_tone2'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_facepalming_tone3', 'man_facepalming_tone3'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_facepalming_tone4', 'man_facepalming_tone4'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_facepalming_tone5', 'man_facepalming_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x8f\xad', 'man_factory_worker', 'man_factory_worker'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8f\xad', 'man_factory_worker_tone1', 'man_factory_worker_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8f\xad', 'man_factory_worker_tone2', 'man_factory_worker_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8f\xad', 'man_factory_worker_tone3', 'man_factory_worker_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8f\xad', 'man_factory_worker_tone4', 'man_factory_worker_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8f\xad', 'man_factory_worker_tone5', 'man_factory_worker_tone5'),
            (b'\xf0\x9f\xa7\x9a\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_fairy', 'man_fairy'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_fairy_tone1', 'man_fairy_tone1'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_fairy_tone2', 'man_fairy_tone2'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_fairy_tone3', 'man_fairy_tone3'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_fairy_tone4', 'man_fairy_tone4'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_fairy_tone5', 'man_fairy_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'man_farmer', 'man_farmer'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'man_farmer_tone1', 'man_farmer_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'man_farmer_tone2', 'man_farmer_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'man_farmer_tone3', 'man_farmer_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'man_farmer_tone4', 'man_farmer_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'man_farmer_tone5', 'man_farmer_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x9a\x92', 'man_firefighter', 'man_firefighter'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x9a\x92', 'man_firefighter_tone1', 'man_firefighter_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x9a\x92', 'man_firefighter_tone2', 'man_firefighter_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x9a\x92', 'man_firefighter_tone3', 'man_firefighter_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x9a\x92', 'man_firefighter_tone4', 'man_firefighter_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x9a\x92', 'man_firefighter_tone5', 'man_firefighter_tone5'),
            (b'\xf0\x9f\x99\x8d\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_frowning', 'man_frowning'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_frowning_tone1', 'man_frowning_tone1'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_frowning_tone2', 'man_frowning_tone2'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_frowning_tone3', 'man_frowning_tone3'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_frowning_tone4', 'man_frowning_tone4'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_frowning_tone5', 'man_frowning_tone5'),
            (b'\xf0\x9f\xa7\x9e\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_genie', 'man_genie'),
            (b'\xf0\x9f\x99\x85\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_gesturing_no', 'man_gesturing_no'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_gesturing_no_tone1', 'man_gesturing_no_tone1'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_gesturing_no_tone2', 'man_gesturing_no_tone2'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_gesturing_no_tone3', 'man_gesturing_no_tone3'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_gesturing_no_tone4', 'man_gesturing_no_tone4'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_gesturing_no_tone5', 'man_gesturing_no_tone5'),
            (b'\xf0\x9f\x99\x86\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_gesturing_ok', 'man_gesturing_ok'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_gesturing_ok_tone1', 'man_gesturing_ok_tone1'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_gesturing_ok_tone2', 'man_gesturing_ok_tone2'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_gesturing_ok_tone3', 'man_gesturing_ok_tone3'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_gesturing_ok_tone4', 'man_gesturing_ok_tone4'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_gesturing_ok_tone5', 'man_gesturing_ok_tone5'),
            (b'\xf0\x9f\x92\x86\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_getting_face_massage', 'man_getting_face_massage'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_getting_face_massage_tone1', 'man_getting_face_massage_tone1'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_getting_face_massage_tone2', 'man_getting_face_massage_tone2'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_getting_face_massage_tone3', 'man_getting_face_massage_tone3'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_getting_face_massage_tone4', 'man_getting_face_massage_tone4'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_getting_face_massage_tone5', 'man_getting_face_massage_tone5'),
            (b'\xf0\x9f\x92\x87\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_getting_haircut', 'man_getting_haircut'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_getting_haircut_tone1', 'man_getting_haircut_tone1'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_getting_haircut_tone2', 'man_getting_haircut_tone2'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_getting_haircut_tone3', 'man_getting_haircut_tone3'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_getting_haircut_tone4', 'man_getting_haircut_tone4'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_getting_haircut_tone5', 'man_getting_haircut_tone5'),
            (b'\xf0\x9f\x8f\x8c\xef\xb8\x8f\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_golfing', 'man_golfing'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_golfing_tone1', 'man_golfing_tone1'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_golfing_tone2', 'man_golfing_tone2'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_golfing_tone3', 'man_golfing_tone3'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_golfing_tone4', 'man_golfing_tone4'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_golfing_tone5', 'man_golfing_tone5'),
            (b'\xf0\x9f\x92\x82\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_guard', 'man_guard'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_guard_tone1', 'man_guard_tone1'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_guard_tone2', 'man_guard_tone2'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_guard_tone3', 'man_guard_tone3'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_guard_tone4', 'man_guard_tone4'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_guard_tone5', 'man_guard_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'man_health_worker', 'man_health_worker'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'man_health_worker_tone1', 'man_health_worker_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'man_health_worker_tone2', 'man_health_worker_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'man_health_worker_tone3', 'man_health_worker_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'man_health_worker_tone4', 'man_health_worker_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'man_health_worker_tone5', 'man_health_worker_tone5'),
            (b'\xf0\x9f\xa7\x98\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_lotus_position', 'man_in_lotus_position'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_lotus_position_tone1', 'man_in_lotus_position_tone1'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_lotus_position_tone2', 'man_in_lotus_position_tone2'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_lotus_position_tone3', 'man_in_lotus_position_tone3'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_lotus_position_tone4', 'man_in_lotus_position_tone4'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_lotus_position_tone5', 'man_in_lotus_position_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'man_in_manual_wheelchair', 'man_in_manual_wheelchair'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'man_in_manual_wheelchair_tone1', 'man_in_manual_wheelchair_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'man_in_manual_wheelchair_tone2', 'man_in_manual_wheelchair_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'man_in_manual_wheelchair_tone3', 'man_in_manual_wheelchair_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'man_in_manual_wheelchair_tone4', 'man_in_manual_wheelchair_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'man_in_manual_wheelchair_tone5', 'man_in_manual_wheelchair_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'man_in_motorized_wheelchair', 'man_in_motorized_wheelchair'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'man_in_motorized_wheelchair_tone1', 'man_in_motorized_wheelchair_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'man_in_motorized_wheelchair_tone2', 'man_in_motorized_wheelchair_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'man_in_motorized_wheelchair_tone3', 'man_in_motorized_wheelchair_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'man_in_motorized_wheelchair_tone4', 'man_in_motorized_wheelchair_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'man_in_motorized_wheelchair_tone5', 'man_in_motorized_wheelchair_tone5'),
            (b'\xf0\x9f\xa7\x96\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_steamy_room', 'man_in_steamy_room'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_steamy_room_tone1', 'man_in_steamy_room_tone1'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_steamy_room_tone2', 'man_in_steamy_room_tone2'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_steamy_room_tone3', 'man_in_steamy_room_tone3'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_steamy_room_tone4', 'man_in_steamy_room_tone4'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_steamy_room_tone5', 'man_in_steamy_room_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'man_judge', 'man_judge'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'man_judge_tone1', 'man_judge_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'man_judge_tone2', 'man_judge_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'man_judge_tone3', 'man_judge_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'man_judge_tone4', 'man_judge_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'man_judge_tone5', 'man_judge_tone5'),
            (b'\xf0\x9f\xa4\xb9\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_juggling', 'man_juggling'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_juggling_tone1', 'man_juggling_tone1'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_juggling_tone2', 'man_juggling_tone2'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_juggling_tone3', 'man_juggling_tone3'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_juggling_tone4', 'man_juggling_tone4'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_juggling_tone5', 'man_juggling_tone5'),
            (b'\xf0\x9f\xa7\x8e\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_kneeling', 'man_kneeling'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_kneeling_tone1', 'man_kneeling_tone1'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_kneeling_tone2', 'man_kneeling_tone2'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_kneeling_tone3', 'man_kneeling_tone3'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_kneeling_tone4', 'man_kneeling_tone4'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_kneeling_tone5', 'man_kneeling_tone5'),
            (b'\xf0\x9f\x8f\x8b\xef\xb8\x8f\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_lifting_weights', 'man_lifting_weights'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_lifting_weights_tone1', 'man_lifting_weights_tone1'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_lifting_weights_tone2', 'man_lifting_weights_tone2'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_lifting_weights_tone3', 'man_lifting_weights_tone3'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_lifting_weights_tone4', 'man_lifting_weights_tone4'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_lifting_weights_tone5', 'man_lifting_weights_tone5'),
            (b'\xf0\x9f\xa7\x99\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_mage', 'man_mage'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_mage_tone1', 'man_mage_tone1'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_mage_tone2', 'man_mage_tone2'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_mage_tone3', 'man_mage_tone3'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_mage_tone4', 'man_mage_tone4'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_mage_tone5', 'man_mage_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x94\xa7', 'man_mechanic', 'man_mechanic'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x94\xa7', 'man_mechanic_tone1', 'man_mechanic_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x94\xa7', 'man_mechanic_tone2', 'man_mechanic_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x94\xa7', 'man_mechanic_tone3', 'man_mechanic_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x94\xa7', 'man_mechanic_tone4', 'man_mechanic_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x94\xa7', 'man_mechanic_tone5', 'man_mechanic_tone5'),
            (b'\xf0\x9f\x9a\xb5\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_mountain_biking', 'man_mountain_biking'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_mountain_biking_tone1', 'man_mountain_biking_tone1'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_mountain_biking_tone2', 'man_mountain_biking_tone2'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_mountain_biking_tone3', 'man_mountain_biking_tone3'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_mountain_biking_tone4', 'man_mountain_biking_tone4'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_mountain_biking_tone5', 'man_mountain_biking_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x92\xbc', 'man_office_worker', 'man_office_worker'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x92\xbc', 'man_office_worker_tone1', 'man_office_worker_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x92\xbc', 'man_office_worker_tone2', 'man_office_worker_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x92\xbc', 'man_office_worker_tone3', 'man_office_worker_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x92\xbc', 'man_office_worker_tone4', 'man_office_worker_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x92\xbc', 'man_office_worker_tone5', 'man_office_worker_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'man_pilot', 'man_pilot'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'man_pilot_tone1', 'man_pilot_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'man_pilot_tone2', 'man_pilot_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'man_pilot_tone3', 'man_pilot_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'man_pilot_tone4', 'man_pilot_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'man_pilot_tone5', 'man_pilot_tone5'),
            (b'\xf0\x9f\xa4\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_playing_handball', 'man_playing_handball'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_playing_handball_tone1', 'man_playing_handball_tone1'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_playing_handball_tone2', 'man_playing_handball_tone2'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_playing_handball_tone3', 'man_playing_handball_tone3'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_playing_handball_tone4', 'man_playing_handball_tone4'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_playing_handball_tone5', 'man_playing_handball_tone5'),
            (b'\xf0\x9f\xa4\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_playing_water_polo', 'man_playing_water_polo'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_playing_water_polo_tone1', 'man_playing_water_polo_tone1'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_playing_water_polo_tone2', 'man_playing_water_polo_tone2'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_playing_water_polo_tone3', 'man_playing_water_polo_tone3'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_playing_water_polo_tone4', 'man_playing_water_polo_tone4'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_playing_water_polo_tone5', 'man_playing_water_polo_tone5'),
            (b'\xf0\x9f\x91\xae\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_police_officer', 'man_police_officer'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_police_officer_tone1', 'man_police_officer_tone1'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_police_officer_tone2', 'man_police_officer_tone2'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_police_officer_tone3', 'man_police_officer_tone3'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_police_officer_tone4', 'man_police_officer_tone4'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_police_officer_tone5', 'man_police_officer_tone5'),
            (b'\xf0\x9f\x99\x8e\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_pouting', 'man_pouting'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_pouting_tone1', 'man_pouting_tone1'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_pouting_tone2', 'man_pouting_tone2'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_pouting_tone3', 'man_pouting_tone3'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_pouting_tone4', 'man_pouting_tone4'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_pouting_tone5', 'man_pouting_tone5'),
            (b'\xf0\x9f\x99\x8b\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_raising_hand', 'man_raising_hand'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_raising_hand_tone1', 'man_raising_hand_tone1'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_raising_hand_tone2', 'man_raising_hand_tone2'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_raising_hand_tone3', 'man_raising_hand_tone3'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_raising_hand_tone4', 'man_raising_hand_tone4'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_raising_hand_tone5', 'man_raising_hand_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'man_red_haired', 'man_red_haired'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'man_red_haired_tone1', 'man_red_haired_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'man_red_haired_tone2', 'man_red_haired_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'man_red_haired_tone3', 'man_red_haired_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'man_red_haired_tone4', 'man_red_haired_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'man_red_haired_tone5', 'man_red_haired_tone5'),
            (b'\xf0\x9f\x9a\xa3\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_rowing_boat', 'man_rowing_boat'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_rowing_boat_tone1', 'man_rowing_boat_tone1'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_rowing_boat_tone2', 'man_rowing_boat_tone2'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_rowing_boat_tone3', 'man_rowing_boat_tone3'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_rowing_boat_tone4', 'man_rowing_boat_tone4'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_rowing_boat_tone5', 'man_rowing_boat_tone5'),
            (b'\xf0\x9f\x8f\x83\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_running', 'man_running'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_running_tone1', 'man_running_tone1'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_running_tone2', 'man_running_tone2'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_running_tone3', 'man_running_tone3'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_running_tone4', 'man_running_tone4'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_running_tone5', 'man_running_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x94\xac', 'man_scientist', 'man_scientist'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x94\xac', 'man_scientist_tone1', 'man_scientist_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x94\xac', 'man_scientist_tone2', 'man_scientist_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x94\xac', 'man_scientist_tone3', 'man_scientist_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x94\xac', 'man_scientist_tone4', 'man_scientist_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x94\xac', 'man_scientist_tone5', 'man_scientist_tone5'),
            (b'\xf0\x9f\xa4\xb7\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_shrugging', 'man_shrugging'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_shrugging_tone1', 'man_shrugging_tone1'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_shrugging_tone2', 'man_shrugging_tone2'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_shrugging_tone3', 'man_shrugging_tone3'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_shrugging_tone4', 'man_shrugging_tone4'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_shrugging_tone5', 'man_shrugging_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'man_singer', 'man_singer'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'man_singer_tone1', 'man_singer_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'man_singer_tone2', 'man_singer_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'man_singer_tone3', 'man_singer_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'man_singer_tone4', 'man_singer_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'man_singer_tone5', 'man_singer_tone5'),
            (b'\xf0\x9f\xa7\x8d\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_standing', 'man_standing'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_standing_tone1', 'man_standing_tone1'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_standing_tone2', 'man_standing_tone2'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_standing_tone3', 'man_standing_tone3'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_standing_tone4', 'man_standing_tone4'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_standing_tone5', 'man_standing_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x8e\x93', 'man_student', 'man_student'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8e\x93', 'man_student_tone1', 'man_student_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8e\x93', 'man_student_tone2', 'man_student_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8e\x93', 'man_student_tone3', 'man_student_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8e\x93', 'man_student_tone4', 'man_student_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8e\x93', 'man_student_tone5', 'man_student_tone5'),
            (b'\xf0\x9f\xa6\xb8\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_superhero', 'man_superhero'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_superhero_tone1', 'man_superhero_tone1'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_superhero_tone2', 'man_superhero_tone2'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_superhero_tone3', 'man_superhero_tone3'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_superhero_tone4', 'man_superhero_tone4'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_superhero_tone5', 'man_superhero_tone5'),
            (b'\xf0\x9f\xa6\xb9\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_supervillain', 'man_supervillain'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_supervillain_tone1', 'man_supervillain_tone1'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_supervillain_tone2', 'man_supervillain_tone2'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_supervillain_tone3', 'man_supervillain_tone3'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_supervillain_tone4', 'man_supervillain_tone4'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_supervillain_tone5', 'man_supervillain_tone5'),
            (b'\xf0\x9f\x8f\x84\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_surfing', 'man_surfing'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_surfing_tone1', 'man_surfing_tone1'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_surfing_tone2', 'man_surfing_tone2'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_surfing_tone3', 'man_surfing_tone3'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_surfing_tone4', 'man_surfing_tone4'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_surfing_tone5', 'man_surfing_tone5'),
            (b'\xf0\x9f\x8f\x8a\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_swimming', 'man_swimming'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_swimming_tone1', 'man_swimming_tone1'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_swimming_tone2', 'man_swimming_tone2'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_swimming_tone3', 'man_swimming_tone3'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_swimming_tone4', 'man_swimming_tone4'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_swimming_tone5', 'man_swimming_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x8f\xab', 'man_teacher', 'man_teacher'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8f\xab', 'man_teacher_tone1', 'man_teacher_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8f\xab', 'man_teacher_tone2', 'man_teacher_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8f\xab', 'man_teacher_tone3', 'man_teacher_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8f\xab', 'man_teacher_tone4', 'man_teacher_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8f\xab', 'man_teacher_tone5', 'man_teacher_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x92\xbb', 'man_technologist', 'man_technologist'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x92\xbb', 'man_technologist_tone1', 'man_technologist_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x92\xbb', 'man_technologist_tone2', 'man_technologist_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x92\xbb', 'man_technologist_tone3', 'man_technologist_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x92\xbb', 'man_technologist_tone4', 'man_technologist_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x92\xbb', 'man_technologist_tone5', 'man_technologist_tone5'),
            (b'\xf0\x9f\x92\x81\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_tipping_hand', 'man_tipping_hand'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_tipping_hand_tone1', 'man_tipping_hand_tone1'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_tipping_hand_tone2', 'man_tipping_hand_tone2'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_tipping_hand_tone3', 'man_tipping_hand_tone3'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_tipping_hand_tone4', 'man_tipping_hand_tone4'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_tipping_hand_tone5', 'man_tipping_hand_tone5'),
            (b'\xf0\x9f\xa7\x9b\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_vampire', 'man_vampire'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_vampire_tone1', 'man_vampire_tone1'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_vampire_tone2', 'man_vampire_tone2'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_vampire_tone3', 'man_vampire_tone3'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_vampire_tone4', 'man_vampire_tone4'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_vampire_tone5', 'man_vampire_tone5'),
            (b'\xf0\x9f\x9a\xb6\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_walking', 'man_walking'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_walking_tone1', 'man_walking_tone1'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_walking_tone2', 'man_walking_tone2'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_walking_tone3', 'man_walking_tone3'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_walking_tone4', 'man_walking_tone4'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_walking_tone5', 'man_walking_tone5'),
            (b'\xf0\x9f\x91\xb3\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_wearing_turban', 'man_wearing_turban'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_wearing_turban_tone1', 'man_wearing_turban_tone1'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_wearing_turban_tone2', 'man_wearing_turban_tone2'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_wearing_turban_tone3', 'man_wearing_turban_tone3'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_wearing_turban_tone4', 'man_wearing_turban_tone4'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_wearing_turban_tone5', 'man_wearing_turban_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'man_white_haired', 'man_white_haired'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'man_white_haired_tone1', 'man_white_haired_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'man_white_haired_tone2', 'man_white_haired_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'man_white_haired_tone3', 'man_white_haired_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'man_white_haired_tone4', 'man_white_haired_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'man_white_haired_tone5', 'man_white_haired_tone5'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'man_with_probing_cane', 'man_with_probing_cane'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'man_with_probing_cane_tone1', 'man_with_probing_cane_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'man_with_probing_cane_tone2', 'man_with_probing_cane_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'man_with_probing_cane_tone3', 'man_with_probing_cane_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'man_with_probing_cane_tone4', 'man_with_probing_cane_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'man_with_probing_cane_tone5', 'man_with_probing_cane_tone5'),
            (b'\xf0\x9f\xa7\x9f\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_zombie', 'man_zombie'),
            (b'\xf0\x9f\xa5\xad', 'mango', 'mango'),
            (b'\xf0\x9f\xa6\xbd', 'manual_wheelchair', 'manual_wheelchair'),
            (b'\xf0\x9f\x97\xba\xef\xb8\x8f', 'map', 'map', 'world_map'),
            (b'\xf0\x9f\xa7\x89', 'mate', 'mate'),
            (b'\xf0\x9f\xa6\xbe', 'mechanical_arm', 'mechanical_arm'),
            (b'\xf0\x9f\xa6\xbf', 'mechanical_leg', 'mechanical_leg'),
            (b'\xe2\x9a\x95\xef\xb8\x8f', 'medical_symbol', 'medical_symbol'),
            (b'\xf0\x9f\x91\xaf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'men_with_bunny_ears_partying', 'men_with_bunny_ears_partying'),
            (b'\xf0\x9f\xa4\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'men_wrestling', 'men_wrestling'),
            (b'\xf0\x9f\xa7\x9c\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'mermaid', 'mermaid'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'mermaid_tone1', 'mermaid_tone1'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'mermaid_tone2', 'mermaid_tone2'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'mermaid_tone3', 'mermaid_tone3'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'mermaid_tone4', 'mermaid_tone4'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'mermaid_tone5', 'mermaid_tone5'),
            (b'\xf0\x9f\xa7\x9c\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'merman', 'merman'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'merman_tone1', 'merman_tone1'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'merman_tone2', 'merman_tone2'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'merman_tone3', 'merman_tone3'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'merman_tone4', 'merman_tone4'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'merman_tone5', 'merman_tone5'),
            (b'\xf0\x9f\xa7\x9c', 'merperson', 'merperson'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbb', 'merperson_tone1', 'merperson_tone1'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbc', 'merperson_tone2', 'merperson_tone2'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbd', 'merperson_tone3', 'merperson_tone3'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbe', 'merperson_tone4', 'merperson_tone4'),
            (b'\xf0\x9f\xa7\x9c\xf0\x9f\x8f\xbf', 'merperson_tone5', 'merperson_tone5'),
            (b'\xf0\x9f\xa6\xa0', 'microbe', 'microbe'),
            (b'\xf0\x9f\x8e\x99\xef\xb8\x8f', 'microphone2', 'microphone2', 'studio_microphone'),
            (b'\xf0\x9f\x8e\x96\xef\xb8\x8f', 'military_medal', 'military_medal'),
            (b'\xf0\x9f\xa5\xae', 'moon_cake', 'moon_cake'),
            (b'\xf0\x9f\xa6\x9f', 'mosquito', 'mosquito'),
            (b'\xf0\x9f\x9b\xa5\xef\xb8\x8f', 'motorboat', 'motorboat'),
            (b'\xf0\x9f\x8f\x8d\xef\xb8\x8f', 'motorcycle', 'motorcycle', 'racing_motorcycle'),
            (b'\xf0\x9f\xa6\xbc', 'motorized_wheelchair', 'motorized_wheelchair'),
            (b'\xf0\x9f\x9b\xa3\xef\xb8\x8f', 'motorway', 'motorway'),
            (b'\xe2\x9b\xb0\xef\xb8\x8f', 'mountain', 'mountain'),
            (b'\xf0\x9f\x8f\x94\xef\xb8\x8f', 'mountain_snow', 'mountain_snow', 'snow_capped_mountain'),
            (b'\xf0\x9f\x96\xb1\xef\xb8\x8f', 'mouse_three_button', 'mouse_three_button', 'three_button_mouse'),
            (b'\xf0\x9f\x8f\x9e\xef\xb8\x8f', 'national_park', 'national_park', 'park'),
            (b'\xf0\x9f\xa7\xbf', 'nazar_amulet', 'nazar_amulet'),
            (b'\xf0\x9f\x97\x9e\xef\xb8\x8f', 'newspaper2', 'newspaper2', 'rolled_up_newspaper'),
            (b'\xe2\x8f\xad\xef\xb8\x8f', 'next_track', 'next_track', 'track_next'),
            (b'9\xef\xb8\x8f\xe2\x83\xa3', 'nine', 'nine'),
            (b'\xf0\x9f\x97\x92\xef\xb8\x8f', 'notepad_spiral', 'notepad_spiral', 'spiral_note_pad'),
            (b'\xf0\x9f\x85\xbe\xef\xb8\x8f', 'o2', 'o2'),
            (b'\xf0\x9f\x9b\xa2\xef\xb8\x8f', 'oil', 'oil', 'oil_drum'),
            (b'\xf0\x9f\xa7\x93', 'older_adult', 'older_adult'),
            (b'\xf0\x9f\xa7\x93\xf0\x9f\x8f\xbb', 'older_adult_tone1', 'older_adult_tone1'),
            (b'\xf0\x9f\xa7\x93\xf0\x9f\x8f\xbc', 'older_adult_tone2', 'older_adult_tone2'),
            (b'\xf0\x9f\xa7\x93\xf0\x9f\x8f\xbd', 'older_adult_tone3', 'older_adult_tone3'),
            (b'\xf0\x9f\xa7\x93\xf0\x9f\x8f\xbe', 'older_adult_tone4', 'older_adult_tone4'),
            (b'\xf0\x9f\xa7\x93\xf0\x9f\x8f\xbf', 'older_adult_tone5', 'older_adult_tone5'),
            (b'\xf0\x9f\x95\x89\xef\xb8\x8f', 'om_symbol', 'om_symbol'),
            (b'1\xef\xb8\x8f\xe2\x83\xa3', 'one', 'one'),
            (b'\xf0\x9f\xa9\xb1', 'one_piece_swimsuit', 'one_piece_swimsuit'),
            (b'\xf0\x9f\xa7\x85', 'onion', 'onion'),
            (b'\xf0\x9f\x9f\xa0', 'orange_circle', 'orange_circle'),
            (b'\xf0\x9f\xa7\xa1', 'orange_heart', 'orange_heart'),
            (b'\xf0\x9f\x9f\xa7', 'orange_square', 'orange_square'),
            (b'\xf0\x9f\xa6\xa7', 'orangutan', 'orangutan'),
            (b'\xe2\x98\xa6\xef\xb8\x8f', 'orthodox_cross', 'orthodox_cross'),
            (b'\xf0\x9f\xa6\xa6', 'otter', 'otter'),
            (b'\xf0\x9f\xa6\xaa', 'oyster', 'oyster'),
            (b'\xf0\x9f\xa4\xb2', 'palms_up_together', 'palms_up_together'),
            (b'\xf0\x9f\xa4\xb2\xf0\x9f\x8f\xbb', 'palms_up_together_tone1', 'palms_up_together_tone1'),
            (b'\xf0\x9f\xa4\xb2\xf0\x9f\x8f\xbc', 'palms_up_together_tone2', 'palms_up_together_tone2'),
            (b'\xf0\x9f\xa4\xb2\xf0\x9f\x8f\xbd', 'palms_up_together_tone3', 'palms_up_together_tone3'),
            (b'\xf0\x9f\xa4\xb2\xf0\x9f\x8f\xbe', 'palms_up_together_tone4', 'palms_up_together_tone4'),
            (b'\xf0\x9f\xa4\xb2\xf0\x9f\x8f\xbf', 'palms_up_together_tone5', 'palms_up_together_tone5'),
            (b'\xf0\x9f\xaa\x82', 'parachute', 'parachute'),
            (b'\xf0\x9f\x85\xbf\xef\xb8\x8f', 'parking', 'parking'),
            (b'\xf0\x9f\xa6\x9c', 'parrot', 'parrot'),
            (b'\xe3\x80\xbd\xef\xb8\x8f', 'part_alternation_mark', 'part_alternation_mark'),
            (b'\xf0\x9f\xa5\xb3', 'partying_face', 'partying_face'),
            (b'\xe2\x98\xae\xef\xb8\x8f', 'peace', 'peace', 'peace_symbol'),
            (b'\xf0\x9f\xa6\x9a', 'peacock', 'peacock'),
            (b'\xe2\x9c\x8f\xef\xb8\x8f', 'pencil2', 'pencil2'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91', 'people_holding_hands', 'people_holding_hands'),
            (b'\xf0\x9f\xa7\x97', 'person_climbing', 'person_climbing'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbb', 'person_climbing_tone1', 'person_climbing_tone1'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbc', 'person_climbing_tone2', 'person_climbing_tone2'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbd', 'person_climbing_tone3', 'person_climbing_tone3'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbe', 'person_climbing_tone4', 'person_climbing_tone4'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbf', 'person_climbing_tone5', 'person_climbing_tone5'),
            (b'\xf0\x9f\xa7\x98', 'person_in_lotus_position', 'person_in_lotus_position'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbb', 'person_in_lotus_position_tone1', 'person_in_lotus_position_tone1'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbc', 'person_in_lotus_position_tone2', 'person_in_lotus_position_tone2'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbd', 'person_in_lotus_position_tone3', 'person_in_lotus_position_tone3'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbe', 'person_in_lotus_position_tone4', 'person_in_lotus_position_tone4'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbf', 'person_in_lotus_position_tone5', 'person_in_lotus_position_tone5'),
            (b'\xf0\x9f\xa7\x96', 'person_in_steamy_room', 'person_in_steamy_room'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbb', 'person_in_steamy_room_tone1', 'person_in_steamy_room_tone1'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbc', 'person_in_steamy_room_tone2', 'person_in_steamy_room_tone2'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbd', 'person_in_steamy_room_tone3', 'person_in_steamy_room_tone3'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbe', 'person_in_steamy_room_tone4', 'person_in_steamy_room_tone4'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbf', 'person_in_steamy_room_tone5', 'person_in_steamy_room_tone5'),
            (b'\xf0\x9f\xa7\x8e', 'person_kneeling', 'person_kneeling'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbb', 'person_kneeling_tone1', 'person_kneeling_tone1'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbc', 'person_kneeling_tone2', 'person_kneeling_tone2'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbd', 'person_kneeling_tone3', 'person_kneeling_tone3'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbe', 'person_kneeling_tone4', 'person_kneeling_tone4'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbf', 'person_kneeling_tone5', 'person_kneeling_tone5'),
            (b'\xf0\x9f\xa7\x8d', 'person_standing', 'person_standing'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbb', 'person_standing_tone1', 'person_standing_tone1'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbc', 'person_standing_tone2', 'person_standing_tone2'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbd', 'person_standing_tone3', 'person_standing_tone3'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbe', 'person_standing_tone4', 'person_standing_tone4'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbf', 'person_standing_tone5', 'person_standing_tone5'),
            (b'\xf0\x9f\xa7\xab', 'petri_dish', 'petri_dish'),
            (b'\xe2\x9b\x8f\xef\xb8\x8f', 'pick', 'pick'),
            (b'\xf0\x9f\xa5\xa7', 'pie', 'pie'),
            (b'\xf0\x9f\xa4\x8f', 'pinching_hand', 'pinching_hand'),
            (b'\xf0\x9f\xa4\x8f\xf0\x9f\x8f\xbb', 'pinching_hand_tone1', 'pinching_hand_tone1'),
            (b'\xf0\x9f\xa4\x8f\xf0\x9f\x8f\xbc', 'pinching_hand_tone2', 'pinching_hand_tone2'),
            (b'\xf0\x9f\xa4\x8f\xf0\x9f\x8f\xbd', 'pinching_hand_tone3', 'pinching_hand_tone3'),
            (b'\xf0\x9f\xa4\x8f\xf0\x9f\x8f\xbe', 'pinching_hand_tone4', 'pinching_hand_tone4'),
            (b'\xf0\x9f\xa4\x8f\xf0\x9f\x8f\xbf', 'pinching_hand_tone5', 'pinching_hand_tone5'),
            (b'\xf0\x9f\x8f\xb4\xe2\x80\x8d\xe2\x98\xa0\xef\xb8\x8f', 'pirate_flag', 'pirate_flag'),
            (b'\xe2\x8f\xaf\xef\xb8\x8f', 'play_pause', 'play_pause'),
            (b'\xf0\x9f\xa5\xba', 'pleading_face', 'pleading_face'),
            (b'\xe2\x98\x9d\xef\xb8\x8f', 'point_up', 'point_up'),
            (b'\xf0\x9f\xa5\xa8', 'pretzel', 'pretzel'),
            (b'\xe2\x8f\xae\xef\xb8\x8f', 'previous_track', 'previous_track', 'track_previous'),
            (b'\xf0\x9f\x96\xa8\xef\xb8\x8f', 'printer', 'printer'),
            (b'\xf0\x9f\xa6\xaf', 'probing_cane', 'probing_cane'),
            (b'\xf0\x9f\x9f\xa3', 'purple_circle', 'purple_circle'),
            (b'\xf0\x9f\x9f\xaa', 'purple_square', 'purple_square'),
            (b'\xf0\x9f\xa6\x9d', 'raccoon', 'raccoon'),
            (b'\xf0\x9f\x8f\x8e\xef\xb8\x8f', 'race_car', 'race_car', 'racing_car'),
            (b'\xe2\x98\xa2\xef\xb8\x8f', 'radioactive', 'radioactive', 'radioactive_sign'),
            (b'\xf0\x9f\x9b\xa4\xef\xb8\x8f', 'railroad_track', 'railroad_track', 'railway_track'),
            (b'\xf0\x9f\xaa\x92', 'razor', 'razor'),
            (b'\xf0\x9f\xa7\xbe', 'receipt', 'receipt'),
            (b'\xe2\x8f\xba\xef\xb8\x8f', 'record_button', 'record_button'),
            (b'\xe2\x99\xbb\xef\xb8\x8f', 'recycle', 'recycle'),
            (b'\xf0\x9f\xa7\xa7', 'red_envelope', 'red_envelope'),
            (b'\xf0\x9f\x9f\xa5', 'red_square', 'red_square'),
            (b'\xc2\xae\xef\xb8\x8f', 'registered', 'registered'),
            (b'\xe2\x98\xba\xef\xb8\x8f', 'relaxed', 'relaxed'),
            (b'\xf0\x9f\x8e\x97\xef\xb8\x8f', 'reminder_ribbon', 'reminder_ribbon'),
            (b'\xf0\x9f\xaa\x90', 'ringed_planet', 'ringed_planet'),
            (b'\xf0\x9f\xa7\xbb', 'roll_of_paper', 'roll_of_paper'),
            (b'\xf0\x9f\x8f\xb5\xef\xb8\x8f', 'rosette', 'rosette'),
            (b'\xf0\x9f\x88\x82\xef\xb8\x8f', 'sa', 'sa'),
            (b'\xf0\x9f\xa7\xb7', 'safety_pin', 'safety_pin'),
            (b'\xf0\x9f\xa6\xba', 'safety_vest', 'safety_vest'),
            (b'\xf0\x9f\xa7\x82', 'salt', 'salt'),
            (b'\xf0\x9f\xa5\xaa', 'sandwich', 'sandwich'),
            (b'\xf0\x9f\xa5\xbb', 'sari', 'sari'),
            (b'\xf0\x9f\x9b\xb0\xef\xb8\x8f', 'satellite_orbital', 'satellite_orbital'),
            (b'\xf0\x9f\xa6\x95', 'sauropod', 'sauropod'),
            (b'\xe2\x9a\x96\xef\xb8\x8f', 'scales', 'scales'),
            (b'\xf0\x9f\xa7\xa3', 'scarf', 'scarf'),
            (b'\xe2\x9c\x82\xef\xb8\x8f', 'scissors', 'scissors'),
            (b'\xf0\x9f\x8f\xb4\xf3\xa0\x81\xa7\xf3\xa0\x81\xa2\xf3\xa0\x81\xb3\xf3\xa0\x81\xa3\xf3\xa0\x81\xb4\xf3\xa0\x81\xbf', 'scotland', 'scotland'),
            (b'\xe3\x8a\x99\xef\xb8\x8f', 'secret', 'secret'),
            (b'\xf0\x9f\x90\x95\xe2\x80\x8d\xf0\x9f\xa6\xba', 'service_dog', 'service_dog'),
            (b'7\xef\xb8\x8f\xe2\x83\xa3', 'seven', 'seven'),
            (b'\xe2\x98\x98\xef\xb8\x8f', 'shamrock', 'shamrock'),
            (b'\xf0\x9f\x9b\xa1\xef\xb8\x8f', 'shield', 'shield'),
            (b'\xe2\x9b\xa9\xef\xb8\x8f', 'shinto_shrine', 'shinto_shrine'),
            (b'\xf0\x9f\x9b\x8d\xef\xb8\x8f', 'shopping_bags', 'shopping_bags'),
            (b'\xf0\x9f\xa9\xb3', 'shorts', 'shorts'),
            (b'\xf0\x9f\xa4\xab', 'shushing_face', 'shushing_face'),
            (b'6\xef\xb8\x8f\xe2\x83\xa3', 'six', 'six'),
            (b'\xf0\x9f\x9b\xb9', 'skateboard', 'skateboard'),
            (b'\xe2\x9b\xb7\xef\xb8\x8f', 'skier', 'skier'),
            (b'\xe2\x98\xa0\xef\xb8\x8f', 'skull_and_crossbones', 'skull_and_crossbones', 'skull_crossbones'),
            (b'\xf0\x9f\xa6\xa8', 'skunk', 'skunk'),
            (b'\xf0\x9f\x9b\xb7', 'sled', 'sled'),
            (b'\xf0\x9f\xa6\xa5', 'sloth', 'sloth'),
            (b'\xf0\x9f\xa5\xb0', 'smiling_face_with_3_hearts', 'smiling_face_with_3_hearts'),
            (b'\xe2\x9d\x84\xef\xb8\x8f', 'snowflake', 'snowflake'),
            (b'\xe2\x98\x83\xef\xb8\x8f', 'snowman2', 'snowman2'),
            (b'\xf0\x9f\xa7\xbc', 'soap', 'soap'),
            (b'\xf0\x9f\xa7\xa6', 'socks', 'socks'),
            (b'\xf0\x9f\xa5\x8e', 'softball', 'softball'),
            (b'\xe2\x99\xa0\xef\xb8\x8f', 'spades', 'spades'),
            (b'\xe2\x9d\x87\xef\xb8\x8f', 'sparkle', 'sparkle'),
            (b'\xf0\x9f\x97\xa3\xef\xb8\x8f', 'speaking_head', 'speaking_head', 'speaking_head_in_silhouette'),
            (b'\xf0\x9f\x95\xb7\xef\xb8\x8f', 'spider', 'spider'),
            (b'\xf0\x9f\x95\xb8\xef\xb8\x8f', 'spider_web', 'spider_web'),
            (b'\xf0\x9f\xa7\xbd', 'sponge', 'sponge'),
            (b'\xf0\x9f\xa7\xb4', 'squeeze_bottle', 'squeeze_bottle'),
            (b'\xf0\x9f\x8f\x9f\xef\xb8\x8f', 'stadium', 'stadium'),
            (b'\xe2\x98\xaa\xef\xb8\x8f', 'star_and_crescent', 'star_and_crescent'),
            (b'\xe2\x9c\xa1\xef\xb8\x8f', 'star_of_david', 'star_of_david'),
            (b'\xf0\x9f\xa4\xa9', 'star_struck', 'star_struck'),
            (b'\xf0\x9f\xa9\xba', 'stethoscope', 'stethoscope'),
            (b'\xe2\x8f\xb9\xef\xb8\x8f', 'stop_button', 'stop_button'),
            (b'\xe2\x8f\xb1\xef\xb8\x8f', 'stopwatch', 'stopwatch'),
            (b'\xe2\x98\x80\xef\xb8\x8f', 'sunny', 'sunny'),
            (b'\xf0\x9f\xa6\xb8', 'superhero', 'superhero'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbb', 'superhero_tone1', 'superhero_tone1'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbc', 'superhero_tone2', 'superhero_tone2'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbd', 'superhero_tone3', 'superhero_tone3'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbe', 'superhero_tone4', 'superhero_tone4'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbf', 'superhero_tone5', 'superhero_tone5'),
            (b'\xf0\x9f\xa6\xb9', 'supervillain', 'supervillain'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbb', 'supervillain_tone1', 'supervillain_tone1'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbc', 'supervillain_tone2', 'supervillain_tone2'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbd', 'supervillain_tone3', 'supervillain_tone3'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbe', 'supervillain_tone4', 'supervillain_tone4'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbf', 'supervillain_tone5', 'supervillain_tone5'),
            (b'\xf0\x9f\xa6\xa2', 'swan', 'swan'),
            (b'\xf0\x9f\xa6\x96', 't_rex', 't_rex'),
            (b'\xf0\x9f\xa5\xa1', 'takeout_box', 'takeout_box'),
            (b'\xf0\x9f\xa7\xb8', 'teddy_bear', 'teddy_bear'),
            (b'\xe2\x98\x8e\xef\xb8\x8f', 'telephone', 'telephone'),
            (b'\xf0\x9f\xa7\xaa', 'test_tube', 'test_tube'),
            (b'\xf0\x9f\x8c\xa1\xef\xb8\x8f', 'thermometer', 'thermometer'),
            (b'\xf0\x9f\xa7\xb5', 'thread', 'thread'),
            (b'3\xef\xb8\x8f\xe2\x83\xa3', 'three', 'three'),
            (b'\xe2\x9b\x88\xef\xb8\x8f', 'thunder_cloud_and_rain', 'thunder_cloud_and_rain', 'thunder_cloud_rain'),
            (b'\xe2\x8f\xb2\xef\xb8\x8f', 'timer', 'timer', 'timer_clock'),
            (b'\xe2\x84\xa2\xef\xb8\x8f', 'tm', 'tm'),
            (b'\xf0\x9f\xa7\xb0', 'toolbox', 'toolbox'),
            (b'\xf0\x9f\xa6\xb7', 'tooth', 'tooth'),
            (b'\xf0\x9f\x96\xb2\xef\xb8\x8f', 'trackball', 'trackball'),
            (b'2\xef\xb8\x8f\xe2\x83\xa3', 'two', 'two'),
            (b'\xf0\x9f\x88\xb7\xef\xb8\x8f', 'u6708', 'u6708'),
            (b'\xe2\x98\x82\xef\xb8\x8f', 'umbrella2', 'umbrella2'),
            (b'\xf0\x9f\x87\xba\xf0\x9f\x87\xb3', 'united_nations', 'united_nations'),
            (b'\xe2\x9c\x8c\xef\xb8\x8f', 'v', 'v'),
            (b'\xf0\x9f\xa7\x9b', 'vampire', 'vampire'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbb', 'vampire_tone1', 'vampire_tone1'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbc', 'vampire_tone2', 'vampire_tone2'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbd', 'vampire_tone3', 'vampire_tone3'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbe', 'vampire_tone4', 'vampire_tone4'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbf', 'vampire_tone5', 'vampire_tone5'),
            (b'\xf0\x9f\xa7\x87', 'waffle', 'waffle'),
            (b'\xf0\x9f\x8f\xb4\xf3\xa0\x81\xa7\xf3\xa0\x81\xa2\xf3\xa0\x81\xb7\xf3\xa0\x81\xac\xf3\xa0\x81\xb3\xf3\xa0\x81\xbf', 'wales', 'wales'),
            (b'\xe2\x9a\xa0\xef\xb8\x8f', 'warning', 'warning'),
            (b'\xf0\x9f\x97\x91\xef\xb8\x8f', 'wastebasket', 'wastebasket'),
            (b'\xe3\x80\xb0\xef\xb8\x8f', 'wavy_dash', 'wavy_dash'),
            (b'\xe2\x98\xb8\xef\xb8\x8f', 'wheel_of_dharma', 'wheel_of_dharma'),
            (b'\xf0\x9f\xa4\x8d', 'white_heart', 'white_heart'),
            (b'\xe2\x97\xbb\xef\xb8\x8f', 'white_medium_square', 'white_medium_square'),
            (b'\xe2\x96\xab\xef\xb8\x8f', 'white_small_square', 'white_small_square'),
            (b'\xf0\x9f\x8c\xa5\xef\xb8\x8f', 'white_sun_behind_cloud', 'white_sun_behind_cloud', 'white_sun_cloud'),
            (b'\xf0\x9f\x8c\xa6\xef\xb8\x8f', 'white_sun_behind_cloud_with_rain', 'white_sun_behind_cloud_with_rain', 'white_sun_rain_cloud'),
            (b'\xf0\x9f\x8c\xa4\xef\xb8\x8f', 'white_sun_small_cloud', 'white_sun_small_cloud', 'white_sun_with_small_cloud'),
            (b'\xf0\x9f\x8c\xac\xef\xb8\x8f', 'wind_blowing_face', 'wind_blowing_face'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'woman_artist', 'woman_artist'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'woman_artist_tone1', 'woman_artist_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'woman_artist_tone2', 'woman_artist_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'woman_artist_tone3', 'woman_artist_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'woman_artist_tone4', 'woman_artist_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'woman_artist_tone5', 'woman_artist_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x9a\x80', 'woman_astronaut', 'woman_astronaut'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x9a\x80', 'woman_astronaut_tone1', 'woman_astronaut_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x9a\x80', 'woman_astronaut_tone2', 'woman_astronaut_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x9a\x80', 'woman_astronaut_tone3', 'woman_astronaut_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x9a\x80', 'woman_astronaut_tone4', 'woman_astronaut_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x9a\x80', 'woman_astronaut_tone5', 'woman_astronaut_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'woman_bald', 'woman_bald'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'woman_bald_tone1', 'woman_bald_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'woman_bald_tone2', 'woman_bald_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'woman_bald_tone3', 'woman_bald_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'woman_bald_tone4', 'woman_bald_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'woman_bald_tone5', 'woman_bald_tone5'),
            (b'\xf0\x9f\x9a\xb4\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_biking', 'woman_biking'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_biking_tone1', 'woman_biking_tone1'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_biking_tone2', 'woman_biking_tone2'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_biking_tone3', 'woman_biking_tone3'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_biking_tone4', 'woman_biking_tone4'),
            (b'\xf0\x9f\x9a\xb4\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_biking_tone5', 'woman_biking_tone5'),
            (b'\xe2\x9b\xb9\xef\xb8\x8f\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_bouncing_ball', 'woman_bouncing_ball'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_bouncing_ball_tone1', 'woman_bouncing_ball_tone1'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_bouncing_ball_tone2', 'woman_bouncing_ball_tone2'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_bouncing_ball_tone3', 'woman_bouncing_ball_tone3'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_bouncing_ball_tone4', 'woman_bouncing_ball_tone4'),
            (b'\xe2\x9b\xb9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_bouncing_ball_tone5', 'woman_bouncing_ball_tone5'),
            (b'\xf0\x9f\x99\x87\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_bowing', 'woman_bowing'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_bowing_tone1', 'woman_bowing_tone1'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_bowing_tone2', 'woman_bowing_tone2'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_bowing_tone3', 'woman_bowing_tone3'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_bowing_tone4', 'woman_bowing_tone4'),
            (b'\xf0\x9f\x99\x87\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_bowing_tone5', 'woman_bowing_tone5'),
            (b'\xf0\x9f\xa4\xb8\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_cartwheeling', 'woman_cartwheeling'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_cartwheeling_tone1', 'woman_cartwheeling_tone1'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_cartwheeling_tone2', 'woman_cartwheeling_tone2'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_cartwheeling_tone3', 'woman_cartwheeling_tone3'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_cartwheeling_tone4', 'woman_cartwheeling_tone4'),
            (b'\xf0\x9f\xa4\xb8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_cartwheeling_tone5', 'woman_cartwheeling_tone5'),
            (b'\xf0\x9f\xa7\x97\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_climbing', 'woman_climbing'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_climbing_tone1', 'woman_climbing_tone1'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_climbing_tone2', 'woman_climbing_tone2'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_climbing_tone3', 'woman_climbing_tone3'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_climbing_tone4', 'woman_climbing_tone4'),
            (b'\xf0\x9f\xa7\x97\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_climbing_tone5', 'woman_climbing_tone5'),
            (b'\xf0\x9f\x91\xb7\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_construction_worker', 'woman_construction_worker'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_construction_worker_tone1', 'woman_construction_worker_tone1'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_construction_worker_tone2', 'woman_construction_worker_tone2'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_construction_worker_tone3', 'woman_construction_worker_tone3'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_construction_worker_tone4', 'woman_construction_worker_tone4'),
            (b'\xf0\x9f\x91\xb7\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_construction_worker_tone5', 'woman_construction_worker_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'woman_cook', 'woman_cook'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'woman_cook_tone1', 'woman_cook_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'woman_cook_tone2', 'woman_cook_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'woman_cook_tone3', 'woman_cook_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'woman_cook_tone4', 'woman_cook_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'woman_cook_tone5', 'woman_cook_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'woman_curly_haired', 'woman_curly_haired'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'woman_curly_haired_tone1', 'woman_curly_haired_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'woman_curly_haired_tone2', 'woman_curly_haired_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'woman_curly_haired_tone3', 'woman_curly_haired_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'woman_curly_haired_tone4', 'woman_curly_haired_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'woman_curly_haired_tone5', 'woman_curly_haired_tone5'),
            (b'\xf0\x9f\x95\xb5\xef\xb8\x8f\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_detective', 'woman_detective'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_detective_tone1', 'woman_detective_tone1'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_detective_tone2', 'woman_detective_tone2'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_detective_tone3', 'woman_detective_tone3'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_detective_tone4', 'woman_detective_tone4'),
            (b'\xf0\x9f\x95\xb5\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_detective_tone5', 'woman_detective_tone5'),
            (b'\xf0\x9f\xa7\x9d\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_elf', 'woman_elf'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_elf_tone1', 'woman_elf_tone1'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_elf_tone2', 'woman_elf_tone2'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_elf_tone3', 'woman_elf_tone3'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_elf_tone4', 'woman_elf_tone4'),
            (b'\xf0\x9f\xa7\x9d\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_elf_tone5', 'woman_elf_tone5'),
            (b'\xf0\x9f\xa4\xa6\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_facepalming', 'woman_facepalming'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_facepalming_tone1', 'woman_facepalming_tone1'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_facepalming_tone2', 'woman_facepalming_tone2'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_facepalming_tone3', 'woman_facepalming_tone3'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_facepalming_tone4', 'woman_facepalming_tone4'),
            (b'\xf0\x9f\xa4\xa6\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_facepalming_tone5', 'woman_facepalming_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x8f\xad', 'woman_factory_worker', 'woman_factory_worker'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8f\xad', 'woman_factory_worker_tone1', 'woman_factory_worker_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8f\xad', 'woman_factory_worker_tone2', 'woman_factory_worker_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8f\xad', 'woman_factory_worker_tone3', 'woman_factory_worker_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8f\xad', 'woman_factory_worker_tone4', 'woman_factory_worker_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8f\xad', 'woman_factory_worker_tone5', 'woman_factory_worker_tone5'),
            (b'\xf0\x9f\xa7\x9a\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_fairy', 'woman_fairy'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_fairy_tone1', 'woman_fairy_tone1'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_fairy_tone2', 'woman_fairy_tone2'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_fairy_tone3', 'woman_fairy_tone3'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_fairy_tone4', 'woman_fairy_tone4'),
            (b'\xf0\x9f\xa7\x9a\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_fairy_tone5', 'woman_fairy_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'woman_farmer', 'woman_farmer'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'woman_farmer_tone1', 'woman_farmer_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'woman_farmer_tone2', 'woman_farmer_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'woman_farmer_tone3', 'woman_farmer_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'woman_farmer_tone4', 'woman_farmer_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'woman_farmer_tone5', 'woman_farmer_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x9a\x92', 'woman_firefighter', 'woman_firefighter'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x9a\x92', 'woman_firefighter_tone1', 'woman_firefighter_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x9a\x92', 'woman_firefighter_tone2', 'woman_firefighter_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x9a\x92', 'woman_firefighter_tone3', 'woman_firefighter_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x9a\x92', 'woman_firefighter_tone4', 'woman_firefighter_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x9a\x92', 'woman_firefighter_tone5', 'woman_firefighter_tone5'),
            (b'\xf0\x9f\x99\x8d\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_frowning', 'woman_frowning'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_frowning_tone1', 'woman_frowning_tone1'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_frowning_tone2', 'woman_frowning_tone2'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_frowning_tone3', 'woman_frowning_tone3'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_frowning_tone4', 'woman_frowning_tone4'),
            (b'\xf0\x9f\x99\x8d\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_frowning_tone5', 'woman_frowning_tone5'),
            (b'\xf0\x9f\xa7\x9e\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_genie', 'woman_genie'),
            (b'\xf0\x9f\x99\x85\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_gesturing_no', 'woman_gesturing_no'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_gesturing_no_tone1', 'woman_gesturing_no_tone1'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_gesturing_no_tone2', 'woman_gesturing_no_tone2'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_gesturing_no_tone3', 'woman_gesturing_no_tone3'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_gesturing_no_tone4', 'woman_gesturing_no_tone4'),
            (b'\xf0\x9f\x99\x85\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_gesturing_no_tone5', 'woman_gesturing_no_tone5'),
            (b'\xf0\x9f\x99\x86\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_gesturing_ok', 'woman_gesturing_ok'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_gesturing_ok_tone1', 'woman_gesturing_ok_tone1'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_gesturing_ok_tone2', 'woman_gesturing_ok_tone2'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_gesturing_ok_tone3', 'woman_gesturing_ok_tone3'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_gesturing_ok_tone4', 'woman_gesturing_ok_tone4'),
            (b'\xf0\x9f\x99\x86\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_gesturing_ok_tone5', 'woman_gesturing_ok_tone5'),
            (b'\xf0\x9f\x92\x86\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_getting_face_massage', 'woman_getting_face_massage'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_getting_face_massage_tone1', 'woman_getting_face_massage_tone1'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_getting_face_massage_tone2', 'woman_getting_face_massage_tone2'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_getting_face_massage_tone3', 'woman_getting_face_massage_tone3'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_getting_face_massage_tone4', 'woman_getting_face_massage_tone4'),
            (b'\xf0\x9f\x92\x86\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_getting_face_massage_tone5', 'woman_getting_face_massage_tone5'),
            (b'\xf0\x9f\x92\x87\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_getting_haircut', 'woman_getting_haircut'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_getting_haircut_tone1', 'woman_getting_haircut_tone1'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_getting_haircut_tone2', 'woman_getting_haircut_tone2'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_getting_haircut_tone3', 'woman_getting_haircut_tone3'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_getting_haircut_tone4', 'woman_getting_haircut_tone4'),
            (b'\xf0\x9f\x92\x87\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_getting_haircut_tone5', 'woman_getting_haircut_tone5'),
            (b'\xf0\x9f\x8f\x8c\xef\xb8\x8f\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_golfing', 'woman_golfing'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_golfing_tone1', 'woman_golfing_tone1'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_golfing_tone2', 'woman_golfing_tone2'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_golfing_tone3', 'woman_golfing_tone3'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_golfing_tone4', 'woman_golfing_tone4'),
            (b'\xf0\x9f\x8f\x8c\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_golfing_tone5', 'woman_golfing_tone5'),
            (b'\xf0\x9f\x92\x82\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_guard', 'woman_guard'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_guard_tone1', 'woman_guard_tone1'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_guard_tone2', 'woman_guard_tone2'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_guard_tone3', 'woman_guard_tone3'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_guard_tone4', 'woman_guard_tone4'),
            (b'\xf0\x9f\x92\x82\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_guard_tone5', 'woman_guard_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'woman_health_worker', 'woman_health_worker'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'woman_health_worker_tone1', 'woman_health_worker_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'woman_health_worker_tone2', 'woman_health_worker_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'woman_health_worker_tone3', 'woman_health_worker_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'woman_health_worker_tone4', 'woman_health_worker_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'woman_health_worker_tone5', 'woman_health_worker_tone5'),
            (b'\xf0\x9f\xa7\x98\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_lotus_position', 'woman_in_lotus_position'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_lotus_position_tone1', 'woman_in_lotus_position_tone1'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_lotus_position_tone2', 'woman_in_lotus_position_tone2'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_lotus_position_tone3', 'woman_in_lotus_position_tone3'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_lotus_position_tone4', 'woman_in_lotus_position_tone4'),
            (b'\xf0\x9f\xa7\x98\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_lotus_position_tone5', 'woman_in_lotus_position_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'woman_in_manual_wheelchair', 'woman_in_manual_wheelchair'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'woman_in_manual_wheelchair_tone1', 'woman_in_manual_wheelchair_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'woman_in_manual_wheelchair_tone2', 'woman_in_manual_wheelchair_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'woman_in_manual_wheelchair_tone3', 'woman_in_manual_wheelchair_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'woman_in_manual_wheelchair_tone4', 'woman_in_manual_wheelchair_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'woman_in_manual_wheelchair_tone5', 'woman_in_manual_wheelchair_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'woman_in_motorized_wheelchair', 'woman_in_motorized_wheelchair'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'woman_in_motorized_wheelchair_tone1', 'woman_in_motorized_wheelchair_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'woman_in_motorized_wheelchair_tone2', 'woman_in_motorized_wheelchair_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'woman_in_motorized_wheelchair_tone3', 'woman_in_motorized_wheelchair_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'woman_in_motorized_wheelchair_tone4', 'woman_in_motorized_wheelchair_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'woman_in_motorized_wheelchair_tone5', 'woman_in_motorized_wheelchair_tone5'),
            (b'\xf0\x9f\xa7\x96\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_steamy_room', 'woman_in_steamy_room'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_steamy_room_tone1', 'woman_in_steamy_room_tone1'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_steamy_room_tone2', 'woman_in_steamy_room_tone2'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_steamy_room_tone3', 'woman_in_steamy_room_tone3'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_steamy_room_tone4', 'woman_in_steamy_room_tone4'),
            (b'\xf0\x9f\xa7\x96\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_steamy_room_tone5', 'woman_in_steamy_room_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'woman_judge', 'woman_judge'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'woman_judge_tone1', 'woman_judge_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'woman_judge_tone2', 'woman_judge_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'woman_judge_tone3', 'woman_judge_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'woman_judge_tone4', 'woman_judge_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'woman_judge_tone5', 'woman_judge_tone5'),
            (b'\xf0\x9f\xa4\xb9\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_juggling', 'woman_juggling'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_juggling_tone1', 'woman_juggling_tone1'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_juggling_tone2', 'woman_juggling_tone2'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_juggling_tone3', 'woman_juggling_tone3'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_juggling_tone4', 'woman_juggling_tone4'),
            (b'\xf0\x9f\xa4\xb9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_juggling_tone5', 'woman_juggling_tone5'),
            (b'\xf0\x9f\xa7\x8e\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_kneeling', 'woman_kneeling'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_kneeling_tone1', 'woman_kneeling_tone1'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_kneeling_tone2', 'woman_kneeling_tone2'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_kneeling_tone3', 'woman_kneeling_tone3'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_kneeling_tone4', 'woman_kneeling_tone4'),
            (b'\xf0\x9f\xa7\x8e\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_kneeling_tone5', 'woman_kneeling_tone5'),
            (b'\xf0\x9f\x8f\x8b\xef\xb8\x8f\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_lifting_weights', 'woman_lifting_weights'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_lifting_weights_tone1', 'woman_lifting_weights_tone1'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_lifting_weights_tone2', 'woman_lifting_weights_tone2'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_lifting_weights_tone3', 'woman_lifting_weights_tone3'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_lifting_weights_tone4', 'woman_lifting_weights_tone4'),
            (b'\xf0\x9f\x8f\x8b\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_lifting_weights_tone5', 'woman_lifting_weights_tone5'),
            (b'\xf0\x9f\xa7\x99\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_mage', 'woman_mage'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_mage_tone1', 'woman_mage_tone1'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_mage_tone2', 'woman_mage_tone2'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_mage_tone3', 'woman_mage_tone3'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_mage_tone4', 'woman_mage_tone4'),
            (b'\xf0\x9f\xa7\x99\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_mage_tone5', 'woman_mage_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x94\xa7', 'woman_mechanic', 'woman_mechanic'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x94\xa7', 'woman_mechanic_tone1', 'woman_mechanic_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x94\xa7', 'woman_mechanic_tone2', 'woman_mechanic_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x94\xa7', 'woman_mechanic_tone3', 'woman_mechanic_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x94\xa7', 'woman_mechanic_tone4', 'woman_mechanic_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x94\xa7', 'woman_mechanic_tone5', 'woman_mechanic_tone5'),
            (b'\xf0\x9f\x9a\xb5\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_mountain_biking', 'woman_mountain_biking'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_mountain_biking_tone1', 'woman_mountain_biking_tone1'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_mountain_biking_tone2', 'woman_mountain_biking_tone2'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_mountain_biking_tone3', 'woman_mountain_biking_tone3'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_mountain_biking_tone4', 'woman_mountain_biking_tone4'),
            (b'\xf0\x9f\x9a\xb5\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_mountain_biking_tone5', 'woman_mountain_biking_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x92\xbc', 'woman_office_worker', 'woman_office_worker'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x92\xbc', 'woman_office_worker_tone1', 'woman_office_worker_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x92\xbc', 'woman_office_worker_tone2', 'woman_office_worker_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x92\xbc', 'woman_office_worker_tone3', 'woman_office_worker_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x92\xbc', 'woman_office_worker_tone4', 'woman_office_worker_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x92\xbc', 'woman_office_worker_tone5', 'woman_office_worker_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'woman_pilot', 'woman_pilot'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'woman_pilot_tone1', 'woman_pilot_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'woman_pilot_tone2', 'woman_pilot_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'woman_pilot_tone3', 'woman_pilot_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'woman_pilot_tone4', 'woman_pilot_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'woman_pilot_tone5', 'woman_pilot_tone5'),
            (b'\xf0\x9f\xa4\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_playing_handball', 'woman_playing_handball'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_playing_handball_tone1', 'woman_playing_handball_tone1'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_playing_handball_tone2', 'woman_playing_handball_tone2'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_playing_handball_tone3', 'woman_playing_handball_tone3'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_playing_handball_tone4', 'woman_playing_handball_tone4'),
            (b'\xf0\x9f\xa4\xbe\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_playing_handball_tone5', 'woman_playing_handball_tone5'),
            (b'\xf0\x9f\xa4\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_playing_water_polo', 'woman_playing_water_polo'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_playing_water_polo_tone1', 'woman_playing_water_polo_tone1'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_playing_water_polo_tone2', 'woman_playing_water_polo_tone2'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_playing_water_polo_tone3', 'woman_playing_water_polo_tone3'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_playing_water_polo_tone4', 'woman_playing_water_polo_tone4'),
            (b'\xf0\x9f\xa4\xbd\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_playing_water_polo_tone5', 'woman_playing_water_polo_tone5'),
            (b'\xf0\x9f\x91\xae\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_police_officer', 'woman_police_officer'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_police_officer_tone1', 'woman_police_officer_tone1'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_police_officer_tone2', 'woman_police_officer_tone2'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_police_officer_tone3', 'woman_police_officer_tone3'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_police_officer_tone4', 'woman_police_officer_tone4'),
            (b'\xf0\x9f\x91\xae\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_police_officer_tone5', 'woman_police_officer_tone5'),
            (b'\xf0\x9f\x99\x8e\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_pouting', 'woman_pouting'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_pouting_tone1', 'woman_pouting_tone1'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_pouting_tone2', 'woman_pouting_tone2'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_pouting_tone3', 'woman_pouting_tone3'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_pouting_tone4', 'woman_pouting_tone4'),
            (b'\xf0\x9f\x99\x8e\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_pouting_tone5', 'woman_pouting_tone5'),
            (b'\xf0\x9f\x99\x8b\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_raising_hand', 'woman_raising_hand'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_raising_hand_tone1', 'woman_raising_hand_tone1'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_raising_hand_tone2', 'woman_raising_hand_tone2'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_raising_hand_tone3', 'woman_raising_hand_tone3'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_raising_hand_tone4', 'woman_raising_hand_tone4'),
            (b'\xf0\x9f\x99\x8b\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_raising_hand_tone5', 'woman_raising_hand_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'woman_red_haired', 'woman_red_haired'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'woman_red_haired_tone1', 'woman_red_haired_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'woman_red_haired_tone2', 'woman_red_haired_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'woman_red_haired_tone3', 'woman_red_haired_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'woman_red_haired_tone4', 'woman_red_haired_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'woman_red_haired_tone5', 'woman_red_haired_tone5'),
            (b'\xf0\x9f\x9a\xa3\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_rowing_boat', 'woman_rowing_boat'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_rowing_boat_tone1', 'woman_rowing_boat_tone1'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_rowing_boat_tone2', 'woman_rowing_boat_tone2'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_rowing_boat_tone3', 'woman_rowing_boat_tone3'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_rowing_boat_tone4', 'woman_rowing_boat_tone4'),
            (b'\xf0\x9f\x9a\xa3\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_rowing_boat_tone5', 'woman_rowing_boat_tone5'),
            (b'\xf0\x9f\x8f\x83\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_running', 'woman_running'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_running_tone1', 'woman_running_tone1'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_running_tone2', 'woman_running_tone2'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_running_tone3', 'woman_running_tone3'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_running_tone4', 'woman_running_tone4'),
            (b'\xf0\x9f\x8f\x83\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_running_tone5', 'woman_running_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x94\xac', 'woman_scientist', 'woman_scientist'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x94\xac', 'woman_scientist_tone1', 'woman_scientist_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x94\xac', 'woman_scientist_tone2', 'woman_scientist_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x94\xac', 'woman_scientist_tone3', 'woman_scientist_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x94\xac', 'woman_scientist_tone4', 'woman_scientist_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x94\xac', 'woman_scientist_tone5', 'woman_scientist_tone5'),
            (b'\xf0\x9f\xa4\xb7\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_shrugging', 'woman_shrugging'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_shrugging_tone1', 'woman_shrugging_tone1'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_shrugging_tone2', 'woman_shrugging_tone2'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_shrugging_tone3', 'woman_shrugging_tone3'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_shrugging_tone4', 'woman_shrugging_tone4'),
            (b'\xf0\x9f\xa4\xb7\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_shrugging_tone5', 'woman_shrugging_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'woman_singer', 'woman_singer'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'woman_singer_tone1', 'woman_singer_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'woman_singer_tone2', 'woman_singer_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'woman_singer_tone3', 'woman_singer_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'woman_singer_tone4', 'woman_singer_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'woman_singer_tone5', 'woman_singer_tone5'),
            (b'\xf0\x9f\xa7\x8d\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_standing', 'woman_standing'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_standing_tone1', 'woman_standing_tone1'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_standing_tone2', 'woman_standing_tone2'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_standing_tone3', 'woman_standing_tone3'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_standing_tone4', 'woman_standing_tone4'),
            (b'\xf0\x9f\xa7\x8d\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_standing_tone5', 'woman_standing_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x8e\x93', 'woman_student', 'woman_student'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8e\x93', 'woman_student_tone1', 'woman_student_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8e\x93', 'woman_student_tone2', 'woman_student_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8e\x93', 'woman_student_tone3', 'woman_student_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8e\x93', 'woman_student_tone4', 'woman_student_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8e\x93', 'woman_student_tone5', 'woman_student_tone5'),
            (b'\xf0\x9f\xa6\xb8\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_superhero', 'woman_superhero'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_superhero_tone1', 'woman_superhero_tone1'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_superhero_tone2', 'woman_superhero_tone2'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_superhero_tone3', 'woman_superhero_tone3'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_superhero_tone4', 'woman_superhero_tone4'),
            (b'\xf0\x9f\xa6\xb8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_superhero_tone5', 'woman_superhero_tone5'),
            (b'\xf0\x9f\xa6\xb9\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_supervillain', 'woman_supervillain'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_supervillain_tone1', 'woman_supervillain_tone1'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_supervillain_tone2', 'woman_supervillain_tone2'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_supervillain_tone3', 'woman_supervillain_tone3'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_supervillain_tone4', 'woman_supervillain_tone4'),
            (b'\xf0\x9f\xa6\xb9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_supervillain_tone5', 'woman_supervillain_tone5'),
            (b'\xf0\x9f\x8f\x84\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_surfing', 'woman_surfing'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_surfing_tone1', 'woman_surfing_tone1'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_surfing_tone2', 'woman_surfing_tone2'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_surfing_tone3', 'woman_surfing_tone3'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_surfing_tone4', 'woman_surfing_tone4'),
            (b'\xf0\x9f\x8f\x84\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_surfing_tone5', 'woman_surfing_tone5'),
            (b'\xf0\x9f\x8f\x8a\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_swimming', 'woman_swimming'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_swimming_tone1', 'woman_swimming_tone1'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_swimming_tone2', 'woman_swimming_tone2'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_swimming_tone3', 'woman_swimming_tone3'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_swimming_tone4', 'woman_swimming_tone4'),
            (b'\xf0\x9f\x8f\x8a\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_swimming_tone5', 'woman_swimming_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x8f\xab', 'woman_teacher', 'woman_teacher'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8f\xab', 'woman_teacher_tone1', 'woman_teacher_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8f\xab', 'woman_teacher_tone2', 'woman_teacher_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8f\xab', 'woman_teacher_tone3', 'woman_teacher_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8f\xab', 'woman_teacher_tone4', 'woman_teacher_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8f\xab', 'woman_teacher_tone5', 'woman_teacher_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x92\xbb', 'woman_technologist', 'woman_technologist'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x92\xbb', 'woman_technologist_tone1', 'woman_technologist_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x92\xbb', 'woman_technologist_tone2', 'woman_technologist_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x92\xbb', 'woman_technologist_tone3', 'woman_technologist_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x92\xbb', 'woman_technologist_tone4', 'woman_technologist_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x92\xbb', 'woman_technologist_tone5', 'woman_technologist_tone5'),
            (b'\xf0\x9f\x92\x81\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_tipping_hand', 'woman_tipping_hand'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_tipping_hand_tone1', 'woman_tipping_hand_tone1'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_tipping_hand_tone2', 'woman_tipping_hand_tone2'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_tipping_hand_tone3', 'woman_tipping_hand_tone3'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_tipping_hand_tone4', 'woman_tipping_hand_tone4'),
            (b'\xf0\x9f\x92\x81\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_tipping_hand_tone5', 'woman_tipping_hand_tone5'),
            (b'\xf0\x9f\xa7\x9b\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_vampire', 'woman_vampire'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_vampire_tone1', 'woman_vampire_tone1'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_vampire_tone2', 'woman_vampire_tone2'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_vampire_tone3', 'woman_vampire_tone3'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_vampire_tone4', 'woman_vampire_tone4'),
            (b'\xf0\x9f\xa7\x9b\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_vampire_tone5', 'woman_vampire_tone5'),
            (b'\xf0\x9f\x9a\xb6\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_walking', 'woman_walking'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_walking_tone1', 'woman_walking_tone1'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_walking_tone2', 'woman_walking_tone2'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_walking_tone3', 'woman_walking_tone3'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_walking_tone4', 'woman_walking_tone4'),
            (b'\xf0\x9f\x9a\xb6\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_walking_tone5', 'woman_walking_tone5'),
            (b'\xf0\x9f\x91\xb3\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_wearing_turban', 'woman_wearing_turban'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_wearing_turban_tone1', 'woman_wearing_turban_tone1'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_wearing_turban_tone2', 'woman_wearing_turban_tone2'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_wearing_turban_tone3', 'woman_wearing_turban_tone3'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_wearing_turban_tone4', 'woman_wearing_turban_tone4'),
            (b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_wearing_turban_tone5', 'woman_wearing_turban_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'woman_white_haired', 'woman_white_haired'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'woman_white_haired_tone1', 'woman_white_haired_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'woman_white_haired_tone2', 'woman_white_haired_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'woman_white_haired_tone3', 'woman_white_haired_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'woman_white_haired_tone4', 'woman_white_haired_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'woman_white_haired_tone5', 'woman_white_haired_tone5'),
            (b'\xf0\x9f\xa7\x95', 'woman_with_headscarf', 'woman_with_headscarf'),
            (b'\xf0\x9f\xa7\x95\xf0\x9f\x8f\xbb', 'woman_with_headscarf_tone1', 'woman_with_headscarf_tone1'),
            (b'\xf0\x9f\xa7\x95\xf0\x9f\x8f\xbc', 'woman_with_headscarf_tone2', 'woman_with_headscarf_tone2'),
            (b'\xf0\x9f\xa7\x95\xf0\x9f\x8f\xbd', 'woman_with_headscarf_tone3', 'woman_with_headscarf_tone3'),
            (b'\xf0\x9f\xa7\x95\xf0\x9f\x8f\xbe', 'woman_with_headscarf_tone4', 'woman_with_headscarf_tone4'),
            (b'\xf0\x9f\xa7\x95\xf0\x9f\x8f\xbf', 'woman_with_headscarf_tone5', 'woman_with_headscarf_tone5'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'woman_with_probing_cane', 'woman_with_probing_cane'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'woman_with_probing_cane_tone1', 'woman_with_probing_cane_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'woman_with_probing_cane_tone2', 'woman_with_probing_cane_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'woman_with_probing_cane_tone3', 'woman_with_probing_cane_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'woman_with_probing_cane_tone4', 'woman_with_probing_cane_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'woman_with_probing_cane_tone5', 'woman_with_probing_cane_tone5'),
            (b'\xf0\x9f\xa7\x9f\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_zombie', 'woman_zombie'),
            (b'\xf0\x9f\xa5\xbf', 'womans_flat_shoe', 'womans_flat_shoe'),
            (b'\xf0\x9f\x91\xaf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'women_with_bunny_ears_partying', 'women_with_bunny_ears_partying'),
            (b'\xf0\x9f\xa4\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'women_wrestling', 'women_wrestling'),
            (b'\xf0\x9f\xa5\xb4', 'woozy_face', 'woozy_face'),
            (b'\xe2\x9c\x8d\xef\xb8\x8f', 'writing_hand', 'writing_hand'),
            (b'\xf0\x9f\xa7\xb6', 'yarn', 'yarn'),
            (b'\xf0\x9f\xa5\xb1', 'yawning_face', 'yawning_face'),
            (b'\xf0\x9f\x9f\xa1', 'yellow_circle', 'yellow_circle'),
            (b'\xf0\x9f\x9f\xa8', 'yellow_square', 'yellow_square'),
            (b'\xe2\x98\xaf\xef\xb8\x8f', 'yin_yang', 'yin_yang'),
            (b'\xf0\x9f\xaa\x80', 'yo_yo', 'yo_yo'),
            (b'\xf0\x9f\xa4\xaa', 'zany_face', 'zany_face'),
            (b'\xf0\x9f\xa6\x93', 'zebra', 'zebra'),
            (b'0\xef\xb8\x8f\xe2\x83\xa3', 'zero', 'zero'),
            (b'\xf0\x9f\xa7\x9f', 'zombie', 'zombie'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x92\xbb', 'technologist_tone4', 'technologist_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x9a\x92', 'firefighter_tone4', 'firefighter_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'man_feeding_baby_tone4', 'man_feeding_baby_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'man_feeding_baby_tone5', 'man_feeding_baby_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x92\xbb', 'technologist_tone5', 'technologist_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x9a\x92', 'firefighter_tone5', 'firefighter_tone5'),
            (b'\xf0\x9f\x91\xad\xf0\x9f\x8f\xbb', 'women_holding_hands_tone1', 'women_holding_hands_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc', 'women_holding_hands_tone1_tone2', 'women_holding_hands_tone1_tone2'),
            (b'\xf0\x9f\xaa\xa1', 'sewing_needle', 'sewing_needle'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x92\xbb', 'technologist', 'technologist'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd', 'women_holding_hands_tone1_tone3', 'women_holding_hands_tone1_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe', 'women_holding_hands_tone1_tone4', 'women_holding_hands_tone1_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x92\xbb', 'technologist_tone1', 'technologist_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x92\xbb', 'technologist_tone2', 'technologist_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf', 'women_holding_hands_tone1_tone5', 'women_holding_hands_tone1_tone5'),
            (b'\xf0\x9f\xaa\xa0', 'plunger', 'plunger'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x92\xbb', 'technologist_tone3', 'technologist_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb', 'women_holding_hands_tone2_tone1', 'women_holding_hands_tone2_tone1'),
            (b'\xf0\x9f\x91\xad\xf0\x9f\x8f\xbc', 'women_holding_hands_tone2', 'women_holding_hands_tone2'),
            (b'\xf0\x9f\xaa\xa3', 'bucket', 'bucket'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd', 'women_holding_hands_tone2_tone3', 'women_holding_hands_tone2_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'person_tone3_curly_hair', 'person_tone3_curly_hair', 'person_medium_skin_tone_curly_hair'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x9a\x92', 'firefighter', 'firefighter'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe', 'women_holding_hands_tone2_tone4', 'women_holding_hands_tone2_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'person_tone5_curly_hair', 'person_tone5_curly_hair', 'person_dark_skin_tone_curly_hair'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf', 'women_holding_hands_tone2_tone5', 'women_holding_hands_tone2_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x9a\x92', 'firefighter_tone1', 'firefighter_tone1'),
            (b'\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'man_feeding_baby', 'man_feeding_baby'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb', 'women_holding_hands_tone3_tone1', 'women_holding_hands_tone3_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x9a\x92', 'firefighter_tone2', 'firefighter_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x9a\x92', 'firefighter_tone3', 'firefighter_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'man_feeding_baby_tone1', 'man_feeding_baby_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc', 'women_holding_hands_tone3_tone2', 'women_holding_hands_tone3_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'man_feeding_baby_tone2', 'man_feeding_baby_tone2'),
            (b'\xf0\x9f\x91\xad\xf0\x9f\x8f\xbd', 'women_holding_hands_tone3', 'women_holding_hands_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'man_feeding_baby_tone3', 'man_feeding_baby_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe', 'women_holding_hands_tone3_tone4', 'women_holding_hands_tone3_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf', 'women_holding_hands_tone3_tone5', 'women_holding_hands_tone3_tone5'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb', 'women_holding_hands_tone4_tone1', 'women_holding_hands_tone4_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc', 'women_holding_hands_tone4_tone2', 'women_holding_hands_tone4_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8f\xab', 'teacher_tone3', 'teacher_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd', 'women_holding_hands_tone4_tone3', 'women_holding_hands_tone4_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8f\xab', 'teacher_tone5', 'teacher_tone5'),
            (b'\xf0\x9f\x91\xad\xf0\x9f\x8f\xbe', 'women_holding_hands_tone4', 'women_holding_hands_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf', 'women_holding_hands_tone4_tone5', 'women_holding_hands_tone4_tone5'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb', 'women_holding_hands_tone5_tone1', 'women_holding_hands_tone5_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc', 'women_holding_hands_tone5_tone2', 'women_holding_hands_tone5_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd', 'women_holding_hands_tone5_tone3', 'women_holding_hands_tone5_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe', 'women_holding_hands_tone5_tone4', 'women_holding_hands_tone5_tone4'),
            (b'\xf0\x9f\x91\xad\xf0\x9f\x8f\xbf', 'women_holding_hands_tone5', 'women_holding_hands_tone5'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'person_curly_hair', 'person_curly_hair'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'person_tone1_curly_hair', 'person_tone1_curly_hair', 'person_light_skin_tone_curly_hair'),
            (b'\xf0\x9f\xaa\xa4', 'mouse_trap', 'mouse_trap'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'person_tone2_curly_hair', 'person_tone2_curly_hair', 'person_medium_light_skin_tone_curly_hair'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xb1', 'person_tone4_curly_hair', 'person_tone4_curly_hair', 'person_medium_dark_skin_tone_curly_hair'),
            (b'\xf0\x9f\xaa\x85', 'piñata', 'piñata'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x8f\xab', 'teacher', 'teacher'),
            (b'\xf0\x9f\xaa\x86', 'nesting_dolls', 'nesting_dolls'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8f\xab', 'teacher_tone1', 'teacher_tone1'),
            (b'\xf0\x9f\xa6\xad', 'seal', 'seal'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8f\xab', 'teacher_tone2', 'teacher_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8f\xab', 'teacher_tone4', 'teacher_tone4'),
            (b'\xf0\x9f\xa6\xa3', 'mammoth', 'mammoth'),
            (b'\xf0\x9f\xa6\xac', 'bison', 'bison'),
            (b'\xf0\x9f\xaa\x9f', 'window', 'window'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_with_veil_tone4', 'man_with_veil_tone4'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_with_veil_tone5', 'man_with_veil_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'health_worker_tone3', 'health_worker_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'health_worker_tone5', 'health_worker_tone5'),
            (b'\xf0\x9f\x91\xb0\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_with_veil', 'man_with_veil'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_with_veil_tone1', 'man_with_veil_tone1'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_with_veil_tone2', 'man_with_veil_tone2'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_with_veil_tone3', 'man_with_veil_tone3'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'health_worker', 'health_worker'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'health_worker_tone1', 'health_worker_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'health_worker_tone2', 'health_worker_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f', 'health_worker_tone4', 'health_worker_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x94\xac', 'scientist_tone3', 'scientist_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x94\xac', 'scientist_tone5', 'scientist_tone5'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_tuxedo_tone4', 'woman_in_tuxedo_tone4'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x94\xac', 'scientist', 'scientist'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_tuxedo_tone5', 'woman_in_tuxedo_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x94\xac', 'scientist_tone1', 'scientist_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x94\xac', 'scientist_tone2', 'scientist_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x94\xac', 'scientist_tone4', 'scientist_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'judge_tone4', 'judge_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'person_tone4_white_hair', 'person_tone4_white_hair', 'person_medium_dark_skin_tone_white_hair'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'judge_tone5', 'judge_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'person_tone5_white_hair', 'person_tone5_white_hair', 'person_dark_skin_tone_white_hair'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_tuxedo_tone3', 'woman_in_tuxedo_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'judge_tone3', 'judge_tone3'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'person_in_manual_wheelchair', 'person_in_manual_wheelchair'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'person_in_manual_wheelchair_tone1', 'person_in_manual_wheelchair_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'person_in_manual_wheelchair_tone2', 'person_in_manual_wheelchair_tone2'),
            (b'\xf0\x9f\xaa\xb6', 'feather', 'feather'),
            (b'\xf0\x9f\x9b\x97', 'elevator', 'elevator'),
            (b'\xf0\x9f\xaa\xa8', 'rock', 'rock'),
            (b'\xf0\x9f\xaa\xb5', 'wood', 'wood'),
            (b'\xf0\x9f\xaa\xb4', 'potted_plant', 'potted_plant'),
            (b'\xf0\x9f\xa6\xab', 'beaver', 'beaver'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'person_tone3_red_hair', 'person_tone3_red_hair', 'person_medium_skin_tone_red_hair'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'person_tone5_red_hair', 'person_tone5_red_hair', 'person_dark_skin_tone_red_hair'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8f\xad', 'factory_worker_tone3', 'factory_worker_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8f\xad', 'factory_worker_tone5', 'factory_worker_tone5'),
            (b'\xf0\x9f\xab\x94', 'tamale', 'tamale'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'person_red_hair', 'person_red_hair'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'person_tone1_red_hair', 'person_tone1_red_hair', 'person_light_skin_tone_red_hair'),
            (b'\xf0\x9f\xab\x95', 'fondue', 'fondue'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'person_tone2_red_hair', 'person_tone2_red_hair', 'person_medium_light_skin_tone_red_hair'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xb0', 'person_tone4_red_hair', 'person_tone4_red_hair', 'person_medium_dark_skin_tone_red_hair'),
            (b'\xf0\x9f\x90\x88\xe2\x80\x8d\xe2\xac\x9b', 'black_cat', 'black_cat'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x8f\xad', 'factory_worker', 'factory_worker'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8f\xad', 'factory_worker_tone1', 'factory_worker_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8f\xad', 'factory_worker_tone2', 'factory_worker_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8f\xad', 'factory_worker_tone4', 'factory_worker_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'person_in_motorized_wheelchair_tone4', 'person_in_motorized_wheelchair_tone4'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'person_white_hair', 'person_white_hair'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8e\x93', 'student_tone4', 'student_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x92\xbc', 'office_worker_tone4', 'office_worker_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x92\xbc', 'office_worker_tone5', 'office_worker_tone5'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'judge', 'judge'),
            (b'\xf0\x9f\xa4\xb5\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_tuxedo', 'woman_in_tuxedo'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_tuxedo_tone1', 'woman_in_tuxedo_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'person_in_motorized_wheelchair_tone5', 'person_in_motorized_wheelchair_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'person_tone1_white_hair', 'person_tone1_white_hair', 'person_light_skin_tone_white_hair'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'judge_tone1', 'judge_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'person_tone2_white_hair', 'person_tone2_white_hair', 'person_medium_light_skin_tone_white_hair'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8e\x93', 'student_tone5', 'student_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x9a\x96\xef\xb8\x8f', 'judge_tone2', 'judge_tone2'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_in_tuxedo_tone2', 'woman_in_tuxedo_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xb3', 'person_tone3_white_hair', 'person_tone3_white_hair', 'person_medium_skin_tone_white_hair'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x8e\x93', 'student', 'student'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_tuxedo_tone3', 'man_in_tuxedo_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8e\x93', 'student_tone1', 'student_tone1'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_tuxedo_tone5', 'man_in_tuxedo_tone5'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'person_in_motorized_wheelchair', 'person_in_motorized_wheelchair'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8e\x93', 'student_tone2', 'student_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8e\x93', 'student_tone3', 'student_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'person_in_motorized_wheelchair_tone1', 'person_in_motorized_wheelchair_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'person_in_motorized_wheelchair_tone2', 'person_in_motorized_wheelchair_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xbc', 'person_in_motorized_wheelchair_tone3', 'person_in_motorized_wheelchair_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'farmer_tone3', 'farmer_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'farmer_tone5', 'farmer_tone5'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x92\xbc', 'office_worker', 'office_worker'),
            (b'\xf0\x9f\xaa\x9a', 'carpentry_saw', 'carpentry_saw'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x92\xbc', 'office_worker_tone1', 'office_worker_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x92\xbc', 'office_worker_tone2', 'office_worker_tone2'),
            (b'\xf0\x9f\x9b\xbb', 'pickup_truck', 'pickup_truck'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x92\xbc', 'office_worker_tone3', 'office_worker_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'person_with_probing_cane_tone3', 'person_with_probing_cane_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'person_with_probing_cane_tone5', 'person_with_probing_cane_tone5'),
            (b'\xf0\x9f\xa4\xb5\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_tuxedo', 'man_in_tuxedo'),
            (b'\xf0\x9f\xaa\xa6', 'headstone', 'headstone'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_tuxedo_tone1', 'man_in_tuxedo_tone1'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_tuxedo_tone2', 'man_in_tuxedo_tone2'),
            (b'\xf0\x9f\xa4\xb5\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f', 'man_in_tuxedo_tone4', 'man_in_tuxedo_tone4'),
            (b'\xf0\x9f\xaa\x84', 'magic_wand', 'magic_wand'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'farmer', 'farmer'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'farmer_tone1', 'farmer_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'farmer_tone2', 'farmer_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8c\xbe', 'farmer_tone4', 'farmer_tone4'),
            (b'\xf0\x9f\x9b\xbc', 'roller_skate', 'roller_skate'),
            (b'\xf0\x9f\xaa\x98', 'long_drum', 'long_drum'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'person_with_probing_cane', 'person_with_probing_cane'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'person_with_probing_cane_tone1', 'person_with_probing_cane_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'person_with_probing_cane_tone2', 'person_with_probing_cane_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xaf', 'person_with_probing_cane_tone4', 'person_with_probing_cane_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'artist_tone3', 'artist_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'artist_tone5', 'artist_tone5'),
            (b'\xf0\x9f\xaa\x97', 'accordion', 'accordion'),
            (b'\xf0\x9f\xaa\x83', 'boomerang', 'boomerang'),
            (b'\xf0\x9f\xaa\x9d', 'hook', 'hook'),
            (b'\xf0\x9f\xaa\xa2', 'knot', 'knot'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'artist', 'artist'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'artist_tone1', 'artist_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'artist_tone2', 'artist_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8e\xa8', 'artist_tone4', 'artist_tone4'),
            (b'\xf0\x9f\x91\xac\xf0\x9f\x8f\xbb', 'men_holding_hands_tone1', 'men_holding_hands_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc', 'men_holding_hands_tone1_tone2', 'men_holding_hands_tone1_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd', 'men_holding_hands_tone1_tone3', 'men_holding_hands_tone1_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe', 'men_holding_hands_tone1_tone4', 'men_holding_hands_tone1_tone4'),
            (b'\xf0\x9f\x8f\xb3\xef\xb8\x8f\xe2\x80\x8d\xe2\x9a\xa7\xef\xb8\x8f', 'transgender_flag', 'transgender_flag'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'pilot_tone3', 'pilot_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf', 'men_holding_hands_tone1_tone5', 'men_holding_hands_tone1_tone5'),
            (b'\xf0\x9f\xa9\xb4', 'thong_sandal', 'thong_sandal'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'pilot_tone5', 'pilot_tone5'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb', 'men_holding_hands_tone2_tone1', 'men_holding_hands_tone2_tone1'),
            (b'\xf0\x9f\x91\xac\xf0\x9f\x8f\xbc', 'men_holding_hands_tone2', 'men_holding_hands_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd', 'men_holding_hands_tone2_tone3', 'men_holding_hands_tone2_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe', 'men_holding_hands_tone2_tone4', 'men_holding_hands_tone2_tone4'),
            (b'\xf0\x9f\xab\x92', 'olive', 'olive'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf', 'men_holding_hands_tone2_tone5', 'men_holding_hands_tone2_tone5'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb', 'men_holding_hands_tone3_tone1', 'men_holding_hands_tone3_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc', 'men_holding_hands_tone3_tone2', 'men_holding_hands_tone3_tone2'),
            (b'\xf0\x9f\xab\x91', 'bell_pepper', 'bell_pepper'),
            (b'\xf0\x9f\x91\xac\xf0\x9f\x8f\xbd', 'men_holding_hands_tone3', 'men_holding_hands_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe', 'men_holding_hands_tone3_tone4', 'men_holding_hands_tone3_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf', 'men_holding_hands_tone3_tone5', 'men_holding_hands_tone3_tone5'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb', 'men_holding_hands_tone4_tone1', 'men_holding_hands_tone4_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc', 'men_holding_hands_tone4_tone2', 'men_holding_hands_tone4_tone2'),
            (b'\xf0\x9f\xab\x90', 'blueberries', 'blueberries'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'pilot', 'pilot'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd', 'men_holding_hands_tone4_tone3', 'men_holding_hands_tone4_tone3'),
            (b'\xf0\x9f\x91\xac\xf0\x9f\x8f\xbe', 'men_holding_hands_tone4', 'men_holding_hands_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'pilot_tone1', 'pilot_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf', 'men_holding_hands_tone4_tone5', 'men_holding_hands_tone4_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'pilot_tone2', 'pilot_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x9c\x88\xef\xb8\x8f', 'pilot_tone4', 'pilot_tone4'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb', 'men_holding_hands_tone5_tone1', 'men_holding_hands_tone5_tone1'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc', 'men_holding_hands_tone5_tone2', 'men_holding_hands_tone5_tone2'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd', 'men_holding_hands_tone5_tone3', 'men_holding_hands_tone5_tone3'),
            (b'\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe', 'men_holding_hands_tone5_tone4', 'men_holding_hands_tone5_tone4'),
            (b'\xf0\x9f\x91\xac\xf0\x9f\x8f\xbf', 'men_holding_hands_tone5', 'men_holding_hands_tone5'),
            (b'\xf0\x9f\xaa\x96', 'military_helmet', 'military_helmet'),
            (b'\xf0\x9f\xab\x96', 'teapot', 'teapot'),
            (b'\xf0\x9f\xa7\x8b', 'bubble_tea', 'bubble_tea'),
            (b'\xf0\x9f\xa5\xb7\xf0\x9f\x8f\xbe', 'ninja_tone4', 'ninja_tone4'),
            (b'\xf0\x9f\xa5\xb7\xf0\x9f\x8f\xbf', 'ninja_tone5', 'ninja_tone5'),
            (b'\xf0\x9f\xa5\xb2', 'smiling_face_with_tear', 'smiling_face_with_tear'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'singer_tone3', 'singer_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'singer_tone5', 'singer_tone5'),
            (b'\xf0\x9f\xa5\xb7', 'ninja', 'ninja'),
            (b'\xf0\x9f\xa5\xb7\xf0\x9f\x8f\xbb', 'ninja_tone1', 'ninja_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'person_feeding_baby_tone3', 'person_feeding_baby_tone3'),
            (b'\xf0\x9f\xaa\x9c', 'ladder', 'ladder'),
            (b'\xf0\x9f\xa5\xb7\xf0\x9f\x8f\xbc', 'ninja_tone2', 'ninja_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'person_feeding_baby_tone5', 'person_feeding_baby_tone5'),
            (b'\xf0\x9f\xa5\xb7\xf0\x9f\x8f\xbd', 'ninja_tone3', 'ninja_tone3'),
            (b'\xf0\x9f\xaa\x9b', 'screwdriver', 'screwdriver'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8e\x84', 'mx_claus_tone3', 'mx_claus_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8e\x84', 'mx_claus_tone5', 'mx_claus_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'person_in_manual_wheelchair_tone3', 'person_in_manual_wheelchair_tone3'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'singer', 'singer'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'singer_tone1', 'singer_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'singer_tone2', 'singer_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8e\xa4', 'singer_tone4', 'singer_tone4'),
            (b'\xf0\x9f\xab\x81', 'lungs', 'lungs'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbd\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_with_veil_tone3', 'woman_with_veil_tone3'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbf\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_with_veil_tone5', 'woman_with_veil_tone5'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'person_feeding_baby', 'person_feeding_baby'),
            (b'\xf0\x9f\xab\x93', 'flatbread', 'flatbread'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'person_feeding_baby_tone1', 'person_feeding_baby_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'person_feeding_baby_tone2', 'person_feeding_baby_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'person_feeding_baby_tone4', 'person_feeding_baby_tone4'),
            (b'\xf0\x9f\xab\x82', 'people_hugging', 'people_hugging'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'woman_feeding_baby_tone3', 'woman_feeding_baby_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'woman_feeding_baby_tone5', 'woman_feeding_baby_tone5'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x8e\x84', 'mx_claus', 'mx_claus'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8e\x84', 'mx_claus_tone1', 'mx_claus_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8e\x84', 'mx_claus_tone2', 'mx_claus_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8e\x84', 'mx_claus_tone4', 'mx_claus_tone4'),
            (b'\xf0\x9f\x91\xb0\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_with_veil', 'woman_with_veil', 'bride_with_veil'),
            (b'\xf0\x9f\xaa\x99', 'coin', 'coin'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_with_veil_tone1', 'woman_with_veil_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc', 'people_holding_hands_tone4_tone2', 'people_holding_hands_tone4_tone2'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbc\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_with_veil_tone2', 'woman_with_veil_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd', 'people_holding_hands_tone4_tone3', 'people_holding_hands_tone4_tone3'),
            (b'\xf0\x9f\x91\xb0\xf0\x9f\x8f\xbe\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f', 'woman_with_veil_tone4', 'woman_with_veil_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe', 'people_holding_hands_tone4', 'people_holding_hands_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf', 'people_holding_hands_tone4_tone5', 'people_holding_hands_tone4_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb', 'people_holding_hands_tone5_tone1', 'people_holding_hands_tone5_tone1'),
            (b'\xf0\x9f\xab\x80', 'anatomical_heart', 'anatomical_heart'),
            (b'\xf0\x9f\x91\xa9\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'woman_feeding_baby', 'woman_feeding_baby'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc', 'people_holding_hands_tone5_tone2', 'people_holding_hands_tone5_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'woman_feeding_baby_tone1', 'woman_feeding_baby_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd', 'people_holding_hands_tone5_tone3', 'people_holding_hands_tone5_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'woman_feeding_baby_tone2', 'woman_feeding_baby_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe', 'people_holding_hands_tone5_tone4', 'people_holding_hands_tone5_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8d\xbc', 'woman_feeding_baby_tone4', 'woman_feeding_baby_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf', 'people_holding_hands_tone5', 'people_holding_hands_tone5'),
            (b'\xf0\x9f\xa4\x8c\xf0\x9f\x8f\xbd', 'pinched_fingers_tone3', 'pinched_fingers_tone3'),
            (b'\xf0\x9f\xa4\x8c\xf0\x9f\x8f\xbf', 'pinched_fingers_tone5', 'pinched_fingers_tone5'),
            (b'\xf0\x9f\xaa\xb3', 'cockroach', 'cockroach'),
            (b'\xf0\x9f\xaa\xb2', 'beetle', 'beetle', 'lady_beetle'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x94\xa7', 'mechanic_tone3', 'mechanic_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x94\xa7', 'mechanic_tone5', 'mechanic_tone5'),
            (b'\xf0\x9f\xa5\xb8', 'disguised_face', 'disguised_face'),
            (b'\xf0\x9f\xa4\x8c', 'pinched_fingers', 'pinched_fingers'),
            (b'\xf0\x9f\xa4\x8c\xf0\x9f\x8f\xbc', 'pinched_fingers_tone2', 'pinched_fingers_tone2'),
            (b'\xf0\x9f\xaa\xb0', 'fly', 'fly'),
            (b'\xf0\x9f\xa4\x8c\xf0\x9f\x8f\xbb', 'pinched_fingers_tone1', 'pinched_fingers_tone1'),
            (b'\xf0\x9f\xa4\x8c\xf0\x9f\x8f\xbe', 'pinched_fingers_tone4', 'pinched_fingers_tone4'),
            (b'\xf0\x9f\xaa\xa7', 'placard', 'placard'),
            (b'\xf0\x9f\x90\xbb\xe2\x80\x8d\xe2\x9d\x84\xef\xb8\x8f', 'polar_bear', 'polar_bear'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x9a\x80', 'astronaut_tone3', 'astronaut_tone3'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x94\xa7', 'mechanic', 'mechanic'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x9a\x80', 'astronaut_tone5', 'astronaut_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x94\xa7', 'mechanic_tone1', 'mechanic_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x94\xa7', 'mechanic_tone2', 'mechanic_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x94\xa7', 'mechanic_tone4', 'mechanic_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'cook_tone3', 'cook_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'cook_tone5', 'cook_tone5'),
            (b'\xf0\x9f\xaa\x9e', 'mirror', 'mirror'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x9a\x80', 'astronaut', 'astronaut'),
            (b'\xf0\x9f\xaa\xa5', 'toothbrush', 'toothbrush'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'cook', 'cook'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x9a\x80', 'astronaut_tone1', 'astronaut_tone1'),
            (b'\xf0\x9f\xaa\xb1', 'worm', 'worm'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x9a\x80', 'astronaut_tone2', 'astronaut_tone2'),
            (b'\xf0\x9f\xa6\xa4', 'dodo', 'dodo'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'cook_tone1', 'cook_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x9a\x80', 'astronaut_tone4', 'astronaut_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'cook_tone2', 'cook_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\x8d\xb3', 'cook_tone4', 'cook_tone4'),
            (b'\xf0\x9f\x9b\x96', 'hut', 'hut'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'person_tone4_bald', 'person_tone4_bald', 'person_medium_dark_skin_tone_bald'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'person_tone5_bald', 'person_tone5_bald', 'person_dark_skin_tone_bald'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd', 'people_holding_hands_tone1_tone3', 'people_holding_hands_tone1_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf', 'people_holding_hands_tone1_tone5', 'people_holding_hands_tone1_tone5'),
            (b'\xf0\x9f\xa7\x91\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'person_bald', 'person_bald'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb', 'people_holding_hands_tone2_tone1', 'people_holding_hands_tone2_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc', 'people_holding_hands_tone2', 'people_holding_hands_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd', 'people_holding_hands_tone2_tone3', 'people_holding_hands_tone2_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'person_tone1_bald', 'person_tone1_bald', 'person_light_skin_tone_bald'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'person_tone2_bald', 'person_tone2_bald', 'person_medium_light_skin_tone_bald'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa6\xb2', 'person_tone3_bald', 'person_tone3_bald', 'person_medium_skin_tone_bald'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe', 'people_holding_hands_tone2_tone4', 'people_holding_hands_tone2_tone4'),
            (b'\xe2\x9a\xa7', 'transgender_symbol', 'transgender_symbol'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf', 'people_holding_hands_tone2_tone5', 'people_holding_hands_tone2_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb', 'people_holding_hands_tone3_tone1', 'people_holding_hands_tone3_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc', 'people_holding_hands_tone3_tone2', 'people_holding_hands_tone3_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd', 'people_holding_hands_tone3', 'people_holding_hands_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe', 'people_holding_hands_tone3_tone4', 'people_holding_hands_tone3_tone4'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf', 'people_holding_hands_tone3_tone5', 'people_holding_hands_tone3_tone5'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb', 'people_holding_hands_tone4_tone1', 'people_holding_hands_tone4_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb', 'people_holding_hands_tone1', 'people_holding_hands_tone1'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbc', 'people_holding_hands_tone1_tone2', 'people_holding_hands_tone1_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe', 'people_holding_hands_tone1_tone4', 'people_holding_hands_tone1_tone4'),
            (b'\xf0\x9f\x91\xab\xf0\x9f\x8f\xbb', 'woman_and_man_holding_hands_tone1', 'woman_and_man_holding_hands_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc', 'woman_and_man_holding_hands_tone1_tone2', 'woman_and_man_holding_hands_tone1_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd', 'woman_and_man_holding_hands_tone1_tone3', 'woman_and_man_holding_hands_tone1_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe', 'woman_and_man_holding_hands_tone1_tone4', 'woman_and_man_holding_hands_tone1_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbb\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf', 'woman_and_man_holding_hands_tone1_tone5', 'woman_and_man_holding_hands_tone1_tone5'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb', 'woman_and_man_holding_hands_tone2_tone1', 'woman_and_man_holding_hands_tone2_tone1'),
            (b'\xf0\x9f\x91\xab\xf0\x9f\x8f\xbc', 'woman_and_man_holding_hands_tone2', 'woman_and_man_holding_hands_tone2'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'person_in_manual_wheelchair_tone4', 'person_in_manual_wheelchair_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd', 'woman_and_man_holding_hands_tone2_tone3', 'woman_and_man_holding_hands_tone2_tone3'),
            (b'\xf0\x9f\xa7\x91\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa6\xbd', 'person_in_manual_wheelchair_tone5', 'person_in_manual_wheelchair_tone5'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe', 'woman_and_man_holding_hands_tone2_tone4', 'woman_and_man_holding_hands_tone2_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbc\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf', 'woman_and_man_holding_hands_tone2_tone5', 'woman_and_man_holding_hands_tone2_tone5'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb', 'woman_and_man_holding_hands_tone3_tone1', 'woman_and_man_holding_hands_tone3_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc', 'woman_and_man_holding_hands_tone3_tone2', 'woman_and_man_holding_hands_tone3_tone2'),
            (b'\xf0\x9f\x91\xab\xf0\x9f\x8f\xbd', 'woman_and_man_holding_hands_tone3', 'woman_and_man_holding_hands_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe', 'woman_and_man_holding_hands_tone3_tone4', 'woman_and_man_holding_hands_tone3_tone4'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbd\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf', 'woman_and_man_holding_hands_tone3_tone5', 'woman_and_man_holding_hands_tone3_tone5'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb', 'woman_and_man_holding_hands_tone4_tone1', 'woman_and_man_holding_hands_tone4_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc', 'woman_and_man_holding_hands_tone4_tone2', 'woman_and_man_holding_hands_tone4_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd', 'woman_and_man_holding_hands_tone4_tone3', 'woman_and_man_holding_hands_tone4_tone3'),
            (b'\xf0\x9f\x91\xab\xf0\x9f\x8f\xbe', 'woman_and_man_holding_hands_tone4', 'woman_and_man_holding_hands_tone4'),
            (b'\xf0\x9f\x91\xab\xf0\x9f\x8f\xbf', 'woman_and_man_holding_hands_tone5', 'woman_and_man_holding_hands_tone5'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbe\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbf', 'woman_and_man_holding_hands_tone4_tone5', 'woman_and_man_holding_hands_tone4_tone5'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbb', 'woman_and_man_holding_hands_tone5_tone1', 'woman_and_man_holding_hands_tone5_tone1'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbc', 'woman_and_man_holding_hands_tone5_tone2', 'woman_and_man_holding_hands_tone5_tone2'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbd', 'woman_and_man_holding_hands_tone5_tone3', 'woman_and_man_holding_hands_tone5_tone3'),
            (b'\xf0\x9f\x91\xa9\xf0\x9f\x8f\xbf\xe2\x80\x8d\xf0\x9f\xa4\x9d\xe2\x80\x8d\xf0\x9f\x91\xa8\xf0\x9f\x8f\xbe', 'woman_and_man_holding_hands_tone5_tone4', 'woman_and_man_holding_hands_tone5_tone4'),
                ), 1):
        
        value = element[0].decode('utf8')
        name = element[1]
        
        emoji = object.__new__(Emoji)
        emoji.animated = False
        emoji.id = emoji_id
        emoji.name = name
        emoji.unicode = value
        emoji.guild = None
        emoji.roles = None
        emoji.managed = False
        emoji.require_colons= True
        emoji.user = ZEROUSER
        emoji.available = True
        EMOJIS[emoji_id] = emoji
        
        UNICODE_TO_EMOJI[value] = emoji
        
        index = 2
        limit = len(element)
        while True:
            name = element[index]
            index += 1
            
            BUILTIN_EMOJIS[name] = emoji
            
            if index == limit:
                break

generate_builtin_emojis()
