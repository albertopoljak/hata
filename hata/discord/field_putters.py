__all__ = ()

from scarletio import CallableAnalyzer

from .utils import datetime_to_timestamp


def _has_entity_include_internals_parameter(entity_type):
    """
    Returns whether the given entity's `.to_data` method has `include_internals` parameter.
    
    Parameters
    ----------
    entity_type : `type` with `{to_data}`
        The entity type to inspect.
    
    Returns
    -------
    has_include_internal_parameter : `bool`
    """
    analyzer = CallableAnalyzer(entity_type.to_data, as_method = True)
    
    for parameter in analyzer.parameters:
        if parameter.name == 'include_internals':
            has_include_internals_parameter = True
            break
    
    else:
        has_include_internals_parameter = False
    
    return has_include_internals_parameter


def entity_id_optional_putter_factory(field_key):
    """
    Returns an entity id putter.
    
    Parameters
    ----------
    field_key : `str`
        The field's key used in payload.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(entity_id, data, defaults):
        """
        Puts the `entity_id` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        entity_id : `int`
            An entity's identifier.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        
        if defaults or entity_id:
            if entity_id:
                raw_entity_id = str(entity_id)
            else:
                raw_entity_id = None
            data[field_key] = raw_entity_id
        
        return data
    
    return putter


def entity_id_array_optional_putter_factory(field_key):
    """
    Returns an entity id array putter.
    
    Parameters
    ----------
    field_key : `str`
        The field's key used in payload.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(entity_id_array, data, defaults):
        """
        Puts the `entity_id_array` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        entity_id_array : `None`, `tuple` of `int`
            An entity's identifier.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
            
        if defaults or (entity_id_array is not None):
            if entity_id_array is None:
                entity_id_array = []
            else:
                entity_id_array = [str(entity_id) for entity_id in entity_id_array]
            
            data[field_key] = entity_id_array
        
        return data
    
    return putter


def preinstanced_putter_factory(field_key):
    """
    Returns a preinstanced putter.
    
    Parameters
    ----------
    field_key : `str`
        The field's key used in payload.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(preinstanced, data, defaults):
        """
        Puts the `preinstanced` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        preinstanced : ``PreinstancedBase``
            The preinstanced object.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        
        data[field_key] = preinstanced.value
        
        return data
    
    return putter


def preinstanced_optional_putter_factory(field_key, default):
    """
    Returns an optional preinstanced putter.
    
    Parameters
    ----------
    field_key : `str`
        The field's key used in payload.
    default : `object`
        Default value to exclude when default values are not required.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(preinstanced, data, defaults):
        """
        Puts the `preinstanced` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        preinstanced : ``PreinstancedBase``
            The preinstanced object.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal default
        nonlocal field_key
        
        if defaults or (preinstanced is not default):
            data[field_key] = preinstanced.value
        
        return data
    
    return putter


def preinstanced_array_putter_factory(field_key):
    """
    Returns a new preinstanced array putter.
    
    Parameters
    ----------
    field_key : `str`
        The field's key used in payload.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(preinstanced_array, data, defaults):
        """
        Puts the `preinstanced` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        preinstanced_array :`None`, `tuple` of  ``PreinstancedBase``
            The preinstanced object.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        
        if preinstanced_array is None:
            field_value = []
        else:
            field_value = [preinstanced.value for preinstanced in preinstanced_array]
        data[field_key] = field_value
        
        return data
    
    return putter


def int_putter_factory(field_key):
    """
    Returns an `int` putter.
    
    Parameters
    ----------
    field_key : `str`
        The field's key used in payload.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(field_value, data, defaults):
        """
        Puts the given `int` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        field_value : `int`
            Integer field value.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        
        data[field_key] = field_value
        
        return data
    
    return putter


def int_optional_putter_factory(field_key, default_value):
    """
    Returns an optional `int` putter.
    
    Parameters
    ----------
    field_key : `str`
        The field's key used in payload.
    default_value : `int`
        The default value to ignore if defaults are not required.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(field_value, data, defaults):
        """
        Puts the given `int` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        field_value : `int`
            Integer field value.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        nonlocal default_value
        
        if defaults or (field_value != default_value):
            data[field_key] = field_value
        
        return data
    
    return putter


def int_optional_postprocess_putter_factory(field_key, default_value, postprocessor):
    """
    Returns an `int` putter.
    
    Parameters
    ----------
    field_key : `str`
        The field's key used in payload.
    default_value : `int`
        The default value to ignore if defaults are not required.
    postprocessor : `callable`
        Postprocessor to apply before putting the value into the the `data` object.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(field_value, data, defaults):
        """
        Puts the given `int` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        field_value : `int`
            Integer field value.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        nonlocal default_value
        nonlocal postprocessor
        
        if defaults or (field_value != default_value):
            data[field_key] = postprocessor(field_value)
        
        return data
    
    return putter


def nullable_int_optional_putter_factory(field_key, default_value):
    """
    Returns an nullable optional `int` putter.
    
    Parameters
    ----------
    field_key : `str`
        The field's key used in payload.
    default_value : `int`
        The default value to ignore if defaults are not required.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(field_value, data, defaults):
        """
        Puts the given `int` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        field_value : `int`
            Integer field value.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        nonlocal default_value
        
        if defaults or (field_value != default_value):
            if field_value == default_value:
                field_value = None
            
            data[field_key] = field_value
        
        return data
    
    return putter


def bool_optional_putter_factory(field_key, default_value):
    """
    Returns a new optional `bool` putter.
    
    Parameters
    ----------
    field_key : `str`
        The field's key used in payload.
    default_value : `bool`
        The default value to ignore if defaults are not required.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(field_value, data, defaults):
        """
        Puts the given `bool` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        field_value : `bool`
            Boolean field value.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        nonlocal default_value
        
        if defaults or (field_value != default_value):
            data[field_key] = field_value
        
        return data
    
    return putter


def nullable_date_time_optional_putter_factory(field_key):
    """
    Returns a new nullable date time putter.
    
    Parameters
    ----------
    field_key : `str`
        The field's key used in payload.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(field_value, data, defaults):
        """
        Puts the given `DateTime` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        field_value : `DateTime`
            Date time field value.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        
        if defaults or (field_value is not None):
            if field_value is None:
                timestamp = None
            else:
                timestamp = datetime_to_timestamp(field_value)
            data[field_key] = timestamp
        
        return data
    
    return putter


def force_string_putter_factory(field_key):
    """
    Returns a new string putter.
    
    Returns
    -------
    field_key : `str`
        The field's key used in payload.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(field_value, data, defaults):
        """
        Puts the given `string` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        field_value : `string`
            String field value.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        
        data[field_key] = field_value
        
        return data
    
    return putter


def nullable_string_putter_factory(field_key):
    """
    Returns a new nullable string putter.
    
    Returns
    -------
    field_key : `str`
        The field's key used in payload.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(field_value, data, defaults):
        """
        Puts the given `string` into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        field_value : `None`, `string`
            String field value.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        
        if field_value is None:
            field_value = ''
        
        data[field_key] = field_value
        
        return data
    
    return putter


def nullable_entity_array_putter_factory(field_key):
    """
    Returns a new nullable entity array putter.
    
    Returns
    -------
    field_key : `str`
        The field's key used in payload.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(entity_array, data, defaults, *, include_internals = False):
        """
        Puts the given entity array into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        entity_array : `None`, `tuple` of `object`
            Entity array.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        include_internals : `bool` = `False`, Optional (Keyword only)
            Whether internal fields should be included.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
            
        if entity_array is None:
            entity_data_array = []
        else:
            entity_data_array = [
                entity.to_data(defaults = defaults, include_internals = include_internals)
                for entity in entity_array
            ]
        
        data[field_key] = entity_data_array
        
        return data
    
    return putter


def nullable_entity_array_optional_putter_factory(field_key):
    """
    Returns a nullable entity array putter.
    
    Returns
    -------
    field_key : `str`
        The field's key used in payload.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(entity_array, data, defaults, *, include_internals = False):
        """
        Puts the given entity array into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        entity_array : `None`, `tuple` of `object`
            Entity array.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        include_internals : `bool` = `False`, Optional (Keyword only)
            Whether internal fields should be included.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        
        if defaults or (entity_array is not None):
            if entity_array is None:
                entity_data_array = []
            else:
                entity_data_array = [
                    entity.to_data(defaults = defaults, include_internals = include_internals)
                    for entity in entity_array
                ]
            
            data[field_key] = entity_data_array
        
        return data
    
    return putter


def nullable_entity_putter_factory(field_key, entity_type):
    """
    Returns a new nullable entity putter.
    
    Returns
    -------
    field_key : `str`
        The field's key used in payload.
    entity_type : `object` with `{to_data}`
        The expected entity type.
    
    Returns
    -------
    putter : `FunctionType`
    """
    return default_entity_putter_factory(field_key, entity_type, None)


def default_entity_putter_factory(field_key, entity_type, default):
    """
    Returns a new defaulted entity putter.
    
    Returns
    -------
    field_key : `str`
        The field's key used in payload.
    entity_type : `object` with `{to_data}`
        The expected entity type.
    default : `object`
        The default value to handle as an unique case.
    
    Returns
    -------
    putter : `FunctionType`
    """
    if _has_entity_include_internals_parameter(entity_type):
        def putter(entity, data, defaults, *, include_internals = False):
            """
            Puts the given entity into the given `data` json serializable object.
            
            > This function is generated.
            
            Parameters
            ----------
            entity : `object` with `{to_data}`
                Entity.
            data : `dict` of (`str`, `Any`) items
                Json serializable dictionary.
            defaults : `bool`
                Whether default values should be included as well.
            include_internals : `bool` = `False`, Optional (Keyword only)
                Whether internal fields should be included.
            
            Returns
            -------
            data : `dict` of (`str`, `Any`) items
            """
            nonlocal default
            nonlocal field_key
            
            if entity is default:
                entity_data = None
            else:
                entity_data = entity.to_data(defaults = defaults, include_internals = include_internals)
            
            data[field_key] = entity_data
            
            return data
    
    else:
        def putter(entity, data, defaults):
            """
            Puts the given entity into the given `data` json serializable object.
            
            > This function is generated.
            
            Parameters
            ----------
            entity : `object` with `{to_data}`
                Entity.
            data : `dict` of (`str`, `Any`) items
                Json serializable dictionary.
            defaults : `bool`
                Whether default values should be included as well.
            
            Returns
            -------
            data : `dict` of (`str`, `Any`) items
            """
            nonlocal default
            nonlocal field_key
            
            if entity is default:
                entity_data = None
            else:
                entity_data = entity.to_data(defaults = defaults)
            
            data[field_key] = entity_data
            
            return data
    
    return putter


def entity_putter_factory(field_key, entity_type):
    """
    Returns a new entity putter.
    
    Returns
    -------
    field_key : `str`
        The field's key used in payload.
    entity_type : `object` with `{to_data}`
        The expected entity type.
    
    Returns
    -------
    putter : `FunctionType`
    """
    if _has_entity_include_internals_parameter(entity_type):
        def putter(entity, data, defaults, *, include_internals = False):
            """
            Puts the given entity into the given `data` json serializable object.
            
            > This function is generated.
            
            Parameters
            ----------
            entity : `object` with `{to_data}`
                Entity.
            data : `dict` of (`str`, `Any`) items
                Json serializable dictionary.
            defaults : `bool`
                Whether default values should be included as well.
            include_internals : `bool` = `False`, Optional (Keyword only)
                Whether internal fields should be included.
            
            Returns
            -------
            data : `dict` of (`str`, `Any`) items
            """
            nonlocal field_key
            
            data[field_key] = entity.to_data(defaults = defaults, include_internals = include_internals)
            
            return data
    
    else:
        def putter(entity, data, defaults):
            """
            Puts the given entity into the given `data` json serializable object.
            
            > This function is generated.
            
            Parameters
            ----------
            entity : `object` with `{to_data}`
                Entity.
            data : `dict` of (`str`, `Any`) items
                Json serializable dictionary.
            defaults : `bool`
                Whether default values should be included as well.
            
            Returns
            -------
            data : `dict` of (`str`, `Any`) items
            """
            nonlocal field_key
            
            data[field_key] = entity.to_data(defaults = defaults)
            
            return data
    
    return putter


def flag_optional_putter_factory(field_key, default_value):
    """
    Returns a new defaulted flag putter.
    
    Returns
    -------
    field_key : `str`
        The field's key used in payload.
    default : `object`
        The default value to handle as an unique case.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(flag, data, defaults):
        """
        Puts the given flags into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        flag : ``FlagBase``
            Flag instance.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        nonlocal default_value
        
        if defaults or (flag != defaults):
            data[field_key] = int(flag)
        
        return data
    
    return putter


def string_flag_optional_putter_factory(field_key, default_value):
    """
    Returns a new defaulted string flag putter.
    
    Returns
    -------
    field_key : `str`
        The field's key used in payload.
    default : `object`
        The default value to handle as an unique case.
    
    Returns
    -------
    putter : `FunctionType`
    """
    def putter(flag, data, defaults):
        """
        Puts the given flags into the given `data` json serializable object.
        
        > This function is generated.
        
        Parameters
        ----------
        flag : ``FlagBase``
            Flag instance.
        data : `dict` of (`str`, `Any`) items
            Json serializable dictionary.
        defaults : `bool`
            Whether default values should be included as well.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        nonlocal field_key
        nonlocal default_value
        
        if defaults or (flag != defaults):
            data[field_key] = format(flag, 'd')
        
        return data
    
    return putter