__all__ = ('ComponentCommand', )

from scarletio import copy_docs

from .....discord.events.handling_helpers import check_name

from ...converters import get_component_command_parameter_converters
from ...exceptions import handle_command_exception
from ...responding import process_command_coroutine
from ...response_modifier import ResponseModifier
from ...wrappers import CommandWrapper

from ..command_base_custom_id import CommandBaseCustomId
from ..command_base_custom_id.helpers import _validate_custom_ids, _validate_name, split_and_check_satisfaction

from .constants import COMMAND_TARGETS_COMPONENT_COMMAND


class ComponentCommand(CommandBaseCustomId):
    """
    A command, which is called if a message component interaction is received with a matched `custom_id`.
    
    Attributes
    ----------
    _command_function : `async-callable˛
        The command's function to call.
    
    _exception_handlers : `None | list<CoroutineFunction>`
        Exception handlers added with ``.error`` to the interaction handler.
    
    _parameter_converters : `tuple<ParameterConverterBase>`
        Parsers to parse command parameters.
    
    _parent_reference : `None | WeakReferer<SelfReferenceInterface>`
        The parent slasher of the component command.
    
    _regex_custom_ids : `None | tuple<RegexMatcher>`.
        Regex matchers to match custom-ids.
    
    _string_custom_ids : `None | tuple<str>`
        The custom id-s to wait for.
    
    name : `str`
        The component commands name.
        
        Only used for debugging.
    
    response_modifier : `None | ResponseModifier`
        Modifies values returned and yielded to command coroutine processor.
    """
    __slots__ = ()
    
    def __new__(
        cls, function, name = None, *deprecated_positional_parameters, custom_id = ..., target = ..., **keyword_parameters
    ):
        """
        Creates a new ``ComponentCommand`` with the given parameters
        
        Parameters
        ----------
        function : `async-callable`
            The function used as the command when using the respective slash command.
        
        name : `None`, `str` = `None`, Optional
            The name of the component command.
        
        custom_id : `str | re.Pattern | (list | set)<str | re.Pattern>`, Optional (Keyword only)
            Custom id to match by the component command.
        
        target : `None`, `str`, Optional (Keyword only)
            The component command's target.
        
        keyword_parameters : Keyword Parameters
            Additional keyword parameters.
        
        Other Parameters
        ----------------
        allowed_mentions : `None | str, UserBase | Role | AllowedMentionProxy | list<str | UserBase | Role> \
                , Optional (Keyword only)
            Which user or role can the response message ping (or everyone).
        
        show_for_invoking_user_only : `bool`, Optional (Keyword only)
            Whether the response message should only be shown for the invoking user.
        
        wait_for_acknowledgement : `bool`, Optional (Keyword only)
            Whether acknowledge tasks should be ensure asynchronously.
        
        Raises
        ------
        TypeError
            If a parameter's type is incorrect.
        ValueError
            If a parameter's value is incorrect.
        """
        if custom_id is ...:
            raise ValueError(
                '`custom_id` parameter is required.'
            )
        
        if (target is not ...) and (target not in COMMAND_TARGETS_COMPONENT_COMMAND):
            raise ValueError(
                f'`target` can be any of `{COMMAND_TARGETS_COMPONENT_COMMAND!r}`\'s '
                f'values, got {target!r}'
            )
        
        if (function is not None) and isinstance(function, CommandWrapper):
            command_function, wrappers = function.fetch_function_and_wrappers_back()
        else:
            command_function = function
            wrappers = None
        
        # Pre validate
        name = _validate_name(name)
        custom_id = _validate_custom_ids(custom_id)
        
        # Check extra parameters
        response_modifier = ResponseModifier(keyword_parameters)
        if keyword_parameters:
            raise TypeError(f'Extra or unused parameters: {keyword_parameters!r}.')
        
        # Post validate
        name = check_name(command_function, name)
        command_function, parameter_converters = get_component_command_parameter_converters(command_function)
        string_custom_ids, regex_custom_ids = split_and_check_satisfaction(custom_id, parameter_converters)
        
        # Construct
        self = object.__new__(cls)
        self._command_function = command_function
        self._parameter_converters = parameter_converters
        self._string_custom_ids = string_custom_ids
        self._regex_custom_ids = regex_custom_ids
        self._parent_reference = None
        self._exception_handlers = None
        self.name = name
        self.response_modifier = response_modifier
        
        if (wrappers is not None):
            for wrapper in wrappers:
                wrapper.apply(self)
        
        return self
    
    
    @copy_docs(CommandBaseCustomId.invoke)
    async def invoke(self, client, interaction_event, regex_match):
        parameters = []
        
        for parameter_converter in self._parameter_converters:
            try:
                parameter = await parameter_converter(client, interaction_event, regex_match)
            except GeneratorExit:
                raise
            
            except BaseException as err:
                exception = err
            
            else:
                parameters.append(parameter)
                continue
            
            await handle_command_exception(
                self,
                client,
                interaction_event,
                exception,
            )
            return
        
        command_coroutine = self._command_function(*parameters)
        
        try:
            await process_command_coroutine(client, interaction_event, self.response_modifier, command_coroutine)
        except GeneratorExit:
            raise
        
        except BaseException as err:
            exception = err
        
        else:
            return
        
        await handle_command_exception(
            self,
            client,
            interaction_event,
            exception,
        )
        return
