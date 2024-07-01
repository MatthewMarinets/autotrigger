"""
Script for modifying `Trigger` files with unlock triggers,
so we can update GUI triggers without having to put up with the editor.
todo:
* trigger conditions
* What's going on with StringExternal vs StringToText("")
* Array assignments
"""

from typing import NamedTuple
import re

from autotrigger.at import tables
from autotrigger.at.parse_triggers import ElementType, TriggerElement, TriggerLib, repo_objects, get_referenced_element, sort_elements
from autotrigger.at.util import unescape_xml_string


_library_id_pattern = re.compile(r'Library="(\w+)" Id="([0-9A-F]{8})"')


class AutoVariable(NamedTuple):
    name: str
    var_type: str
    constant: str|None = None


class AutoVarBuilder:
    def __init__(self, data: list[AutoVariable], loop_var: str= '@loop-var', return_type: str = 'void') -> None:
        self.data = data
        self.loop_var = loop_var
        self.return_type = return_type
        self.append_index = len(data)
    def __bool__(self) -> bool:
        return bool(self.data)
    def append(self, variable: AutoVariable) -> None:
        self.data[self.append_index:self.append_index] = [variable]
        self.append_index += 1


def get_indentation(line: str, indent_level: int) -> tuple[int, int]:
        """Returns (this line indent, next indent)"""
        if not line:
            return 0, indent_level
        self_contained_line = re.compile(r'^<[^/<>]+>[^<]*</[^/<>]+>$')
        this_indent_level = indent_level
        if line.startswith('</') and line.endswith('>'):
            indent_level -= 1
            this_indent_level = indent_level
        elif line.startswith('<') and line.endswith('/>'):
            pass
        elif re.match(self_contained_line, line):
            pass
        elif line[0] == '<' and line[-1] == '>':
            indent_level += 1
        elif line.endswith('(') or line.endswith('{'):
            indent_level += 1
        elif line.startswith(')') or line.startswith('}'):
            indent_level -= 1
            this_indent_level = indent_level
        return this_indent_level, indent_level


def indent_lines(lines: list[str], indent: int = 0) -> tuple[int, list[str]]:
    result: list[str] = []
    for line in lines:
        this_indent, indent = get_indentation(line, indent)
        result.append(('    '*this_indent) + line)
    return indent, result


def write_triggers_xml(lib: TriggerLib, triggers_file: str) -> None:
    sorted_elements = sort_elements(lib)
    with open(triggers_file, 'w') as fp:
        def _print(string: str, indent_level: int = 0) -> None:
            print((' ' * (4 * indent_level)) + string, file=fp)
        _print('<?xml version="1.0" encoding="utf-8"?>')
        _print('<TriggerData>')
        _print(f'<Library Id="{lib.library}">', 1)
        for obj in sorted_elements:
            indent_level = 2
            for line in obj.lines:
                this_indent_level, indent_level = get_indentation(line, indent_level)
                _print(line, this_indent_level)
            assert indent_level == 2

        _print('</Library>', 1)
        fp.write('</TriggerData>')


def write_triggers_strings(lib: TriggerLib, triggers_file: str) -> None:
    lines = sorted(['='.join(line_parts) for line_parts in lib.trigger_strings.items()])
    with open(triggers_file, 'w') as fp:
        def _print(string: str, indent_level: int = 0) -> None:
            print((' ' * (4 * indent_level)) + string, file=fp)
        for line in lines:
            _print(line)


_type_map = {
    'gamelink': 'string',
    'difficulty': 'int',
    'filepath': 'string',
    'userinstance': 'string',
    'actormsg': 'string',
    'catalogfieldpath': 'string',
    'userfield': 'string',
    'layoutframe': 'string',
}


def get_variable_type(element: TriggerElement) -> str:
    in_variable_type = False
    variable_type = ''
    type_element: TriggerElement | None = None
    for line in element.lines:
        if line == '<VariableType>' or line == '<ParameterType>':
            in_variable_type = True
        elif in_variable_type and (m := re.match(r'<Type Value="(\w+)"', line)):
            variable_type = m.group(1)
        elif in_variable_type and line.startswith(r'<TypeElement'):
            _, type_element = get_referenced_element(line)
    if variable_type == 'preset':
        assert type_element
        preset_type = preset_backing_type(type_element)
        return _type_map.get(preset_type, preset_type)
    return _type_map.get(variable_type, variable_type)


def toggle_case_of_first_letter(string: str) -> str:
    if string[0].isupper():
        string = string[0].lower() + string[1:]
    else:
        string = string[0].upper() + string[1:]
    return string


def escape_identifier(string: str) -> str:
    return (
        string
        .replace(' ', '')
        .replace('(', '')
        .replace(')', '')
        .replace('/', '')
        .replace('+', '')
        .replace('-', '')
    )


def parameter_name(data: TriggerLib, element: TriggerElement) -> str:
    if identifier := element.get_inline_value('Identifier'):
        return 'lp_' + identifier
    display_name = data.id_to_string(element.element_id, element.type)
    assert display_name
    return escape_identifier('lp_' + display_name[0].lower() + display_name[1:].replace(' ', ''))


def global_variable_name(data: TriggerLib, element: TriggerElement) -> str:
    assert element.type == ElementType.Variable
    identifier = element.get_inline_value('Identifier')
    if identifier is None:
        unescaped = data.id_to_string(element.element_id, element.type)
        assert unescaped
        identifier = toggle_case_of_first_letter(escape_identifier(unescaped))
    return f'lib{data.library}_gv_{identifier}'


def local_variable_name(data: TriggerLib, element: TriggerElement) -> str:
    assert element.type == ElementType.Variable
    identifier = element.get_inline_value('Identifier')
    if identifier is None:
        identifier = data.id_to_string(element.element_id, element.type)
        assert identifier
        identifier = identifier[0].lower() + identifier[1:]
    return escape_identifier('lv_' + identifier)


def variable_name(data: TriggerLib, element: TriggerElement) -> str:
    if data.parents[element].type in (ElementType.Root, ElementType.Category):
        return global_variable_name(data, element)
    return local_variable_name(data, element)


def function_name(data: TriggerLib, element: TriggerElement) -> str:
    identifier = element.get_inline_value('Identifier')
    if '<FlagNative/>' in element.lines:
        prefix = ''
    else:
        prefix = f'lib{data.library}_gf_'
    if identifier is not None:
        return f'{prefix}{identifier}'
    return f'{prefix}{escape_identifier(data.id_to_string(element.element_id, element.type, "@func"))}'


def trigger_name(data: TriggerLib, element: TriggerElement) -> str:
    prefix = f'lib{data.library}_gt_'
    if identifier := element.get_inline_value('Identifier'):
        return prefix + identifier
    return f'{prefix}{escape_identifier(data.id_to_string(element.element_id, element.type, "@trigger"))}'



def preset_type_name(data: TriggerLib, element: TriggerElement) -> str:
    return  escape_identifier(data.id_to_string(element.element_id, element.type, "@preset"))


def preset_value(data: TriggerLib, element: TriggerElement) -> str:
    if value := element.get_inline_value('Value'):
        return unescape_xml_string(value)
    prefix = f'lib{data.library}_ge_'
    if identifier := element.get_inline_value('Identifier'):
        identifier = unescape_xml_string(identifier)
    else:
        identifier = escape_identifier(data.id_to_string(element.element_id, element.type, "@presetvalue"))
    preset_type_element = data.parents[element]
    assert preset_type_element.type == ElementType.Preset
    return f'{prefix}{preset_type_name(data, preset_type_element)}_{identifier}'


def preset_backing_type(preset_element: TriggerElement) -> str:
    assert preset_element.type == ElementType.Preset
    result = preset_element.get_attribute('BaseType', 'Value')
    assert result is not None
    return result


def codegen_parameter_type(element: TriggerElement) -> str|None:
    result: str|None = None
    if element.type in (ElementType.ParamDef, ElementType.Variable):
        if ((preset_line := element.get_first_line_of_tag('Preset'))
            or (preset_line := element.get_first_line_of_tag('TypeElement'))
        ):
            preset_lib, preset_element = get_referenced_element(preset_line)
            if preset_element.type == ElementType.Preset:
                return preset_backing_type(preset_element)
            else:
                assert preset_element.type == ElementType.ParamDef
                return codegen_parameter_type(preset_element)
        if default_line := element.get_first_line_of_tag('Default'):
            _, default_element = get_referenced_element(default_line)
            result = codegen_parameter_type(default_element)
    elif preset_line := element.get_first_line_of_tag('Preset'):
        preset_lib, preset_value_element = get_referenced_element(preset_line)
        assert preset_value_element.type == ElementType.PresetValue
        preset_element = preset_lib.parents[preset_value_element]
        return preset_backing_type(preset_element)
    if auto_var_type := element.get_attribute('Type', 'Value'):
        result = result or auto_var_type
    if parameter_line := element.get_first_line_of_tag('Parameter'):
        _, parameter_element = get_referenced_element(parameter_line)
        result = result or codegen_parameter_type(parameter_element)
    if variable_line := element.get_first_line_of_tag('Variable'):
        _, variable_element = get_referenced_element(variable_line)
        result = result or codegen_parameter_type(variable_element)
    assert result != 'preset'
    return result


def codegen_parameter(element: TriggerElement, auto_variables: AutoVarBuilder) -> str:
    assert element.type == ElementType.Param
    value = ''
    _type = ''
    variable = ''
    value_id = ''
    array_param = []
    expression = ''

    _value_pattern = re.compile(r'^<(ValueType|ValueId) (Type|Id)="(\w+)"')
    _variable_pattern = re.compile(r'^<Variable Type="Variable" Library="(\w+)" Id="([0-9A-F]{8})"/>')
    _array_pattern = re.compile(r'<Array Type="Param" Library="(\w+)" Id="([0-9A-F]{8})"/>')
    _function_call_pattern = re.compile(r'^<FunctionCall Type="FunctionCall" Library="(\w+)" Id="([0-9A-F]{8})"/>')
    _preset_pattern = re.compile(r'^<Preset Type="PresetValue" Library="(\w+)" Id="([0-9A-F]{8})"/>')
    in_script_code = False
    script_code_result: list[str] = []
    for line in element.lines:
        if line.startswith('<Value>'):
            value = unescape_xml_string(line[len('<Value>'):-len('</Value>')])
        elif line.startswith('<ExpressionText>'):
            expression = unescape_xml_string(line[len('<ExpressionText>'):-len('</ExpressionText>')])
        elif line == '<ScriptCode>':
            in_script_code = True
        elif line == '</ScriptCode>':
            assert in_script_code
            return '\n'.join(script_code_result)
        elif in_script_code:
            script_code_result.append(unescape_xml_string(line))
        elif m := re.match(_value_pattern, line):
            tag = m.group(1)
            if tag == 'ValueId':
                value_id = m.group(3)
            elif tag == 'ValueType':
                _type = _type_map.get(m.group(3), m.group(3))
            else:
                assert False
        elif m := re.match(_variable_pattern, line):
            lib_id = m.group(1)
            var_id = m.group(2)
            assert lib_id != 'Ntve'
            lib = repo_objects.libs[lib_id]
            variable = variable_name(lib, lib.objects[var_id, ElementType.Variable])
        elif m := re.match(_array_pattern, line):
            lib_id, param_id = m.groups()
            param_element = repo_objects.libs[lib_id].objects[param_id, ElementType.Param]
            array_param.append('[' + codegen_parameter(param_element, auto_variables) + ']')
        elif m := re.match(_function_call_pattern, line):
            lib_id, function_call_id = m.groups()
            assert lib_id != 'Ntve'
            function_call_element = repo_objects.libs[lib_id].objects[function_call_id, ElementType.FunctionCall]
            result = codegen_function_call(function_call_element, auto_variables)
            assert len(result) == 1
            return result[0]
        elif line.startswith('<ValueElement'):
            lib, value_element = get_referenced_element(line)
            if value_element.type == ElementType.Trigger:
                return trigger_name(lib, value_element)
            elif value_element.type == ElementType.Preset:
                if value_preset_line := element.get_first_line_of_tag('ValuePreset'):
                    preset_value_lib, preset_value_element = get_referenced_element(value_preset_line)
                    assert preset_value_element.type == ElementType.PresetValue
                    return preset_value(preset_value_lib, preset_value_element)
                elif base_type := value_element.get_attribute('BaseType', 'Value'):
                    default_result = tables.default_return_values.get(base_type)
                    if default_result:
                        return default_result
                return escape_identifier(lib.trigger_strings[f'{value_element.type}/Name/lib_{value_element.library}_{value_element.element_id}'])
            else:
                assert False, f"Don't know how to handle ValueElement of type {value_element.type}"
        elif m := re.match(_preset_pattern, line):
            lib_id = m.group(1)
            preset_id = m.group(2)
            lib = repo_objects.libs[lib_id]
            return preset_value(lib, lib.objects[preset_id, ElementType.PresetValue])
        elif line.startswith('<Parameter Type="ParamDef"'):
            m = _library_id_pattern.search(line)
            assert m
            lib_id, _id = m.groups()
            element = repo_objects.libs[lib_id].objects[_id, ElementType.ParamDef]
            return parameter_name(repo_objects.libs[lib_id], element)
    if _type == 'abilcmd':
        return f'AbilityCommand("{value}", {value_id or "0"})'
    if value_id:
        return value_id
    if _type == 'layoutframerel':
        return '"' + value.rsplit('/', 1)[-1] + '"'
    if array_param:
        assert variable
        return f'{variable}{"".join(array_param)}'
    if variable:
        return variable
    if _type and _type == 'text':
        data = repo_objects.libs[element.library]
        key = f'{element.type}/Value/lib_{data.library}_{element.element_id}'
        if key in data.trigger_strings:
            return f'StringExternal("{key}")'
        return 'StringToText("")'
    if expression:
        lib = repo_objects.libs[element.library]
        children = lib.children[element]
        expression_to_child = {
            child.get_attribute('ExpressionCode', 'Value'): codegen_parameter(child, auto_variables)
            for child in children
            if child.type == ElementType.Param  # Note(mm): Technically, it's more correct to check the tag name is 'ExpressionParam'
        }
        return '(' + re.sub(
            r'~([A-Z]+)~',
            lambda m: expression_to_child.get(m.group(1), m.group()),
            expression,
        ) + ')'
    if _type == 'string' and not value:
        return '""'
    if not value:
        return f'@param{element.element_id}'
    if _type == 'color':
        parts = value.split(',')
        if len(parts) == 4:
            display_values = ["%.2f" % (float(parts[index])/2.55) for index in (1, 2, 3, 0)]
            return f'ColorWithAlpha({", ".join(display_values)})'
        assert len(parts) == 3
        display_values = ["%.2f" % (float(part)/2.55) for part in parts]
        return f'Color({", ".join(display_values)})'
    if _type == 'fixed':
        return str(float(value))
    if _type == 'string':
        return f'"{repr(value)[1:-1]}"'
    if _type == 'unitfilter':
        include_part, exclude_part = value.split(';')
        include_params = format_filter_parts(include_part.split(','))
        exclude_params = format_filter_parts(exclude_part.split(','))
        return f'UnitFilter({include_params[0]}, {include_params[1]}, {exclude_params[0]}, {exclude_params[1]})'
    return value


def format_filter_parts(categories: list[str]) -> tuple[str, str]:
    lower_filter: list[str] = []
    upper_filter: list[str] = []
    for category in categories:
        if category == '-':
            continue
        if tables.target_filter_value[category] < 32:
            lower_filter.append(category)
        else:
            upper_filter.append(category)
    if not lower_filter:
        lower_param = '0'
    else:
        lower_param = ' | '.join(f'(1 << c_targetFilter{x})' for x in lower_filter)
    if not upper_filter:
        upper_param = '0'
    else:
        upper_param = ' | '.join(f'(1 << (c_targetFilter{x} - 32))' for x in upper_filter)
    return lower_param, upper_param


def codegen_function_info(data: TriggerLib, function_def_id: str) -> tuple[str, list[TriggerElement], list[TriggerElement]]:
    children = data.children[data.objects[function_def_id, ElementType.FunctionDef]]
    return (
        function_name(data, data.objects[function_def_id, ElementType.FunctionDef]),
        [child for child in children if child.type == ElementType.ParamDef],
        [child for child in children if child.type == ElementType.SubFuncType],
    )


def parameter_def_id(element: TriggerElement) -> str:
    assert element.type == ElementType.Param
    param_def_pattern = re.compile(r'<ParameterDef Type="ParamDef" Library="\w+" Id="([0-9A-F]{8})"')
    for line in element.lines:
        if m := re.match(param_def_pattern, line):
            return m.group(1)
    assert False


def is_variable_parameter_constant(element: TriggerElement) -> str|None:
    if value := element.get_inline_value('Value'):
        return value
    if variable_line := element.get_first_line_of_tag('Variable'):
        variable_element_lib, variable_element = get_referenced_element(variable_line)
        if '<Constant/>' not in variable_element.lines:
            return None
        return variable_name(variable_element_lib, variable_element)
    return None


def codegen_custom_script(element: TriggerElement) -> list[str]:
    in_custom_script_block = False
    result: list[str] = []
    for line in element.lines:
        if line == '<ScriptCode>':
            in_custom_script_block = True
        elif line == '</ScriptCode>':
            return result
        elif in_custom_script_block:
            result.append(unescape_xml_string(line))
    assert False, f'Custom script element {element.element_id} was missing a ScriptCode block'


def codegen_variable_init(element: TriggerElement) -> list[str]:
    data = repo_objects.libs[element.library]
    for line in element.lines:
        if line.startswith('<Value Type="Param"'):
            if '<Constant/>' in element.lines:
                # Initialized in the _h file
                # Note(mm): Technically, `<Constant/>` should appear as a child to `<Type>` specifically
                return []
            element_type = ElementType.Param
            m = _library_id_pattern.search(line)
            assert m
            library, var_id = m.groups()
            var_element = repo_objects.libs[library].objects[var_id, element_type]
            auto_vars: AutoVarBuilder = AutoVarBuilder([])
            init_value = codegen_parameter(var_element, auto_vars)
            if init_value in (
                '0',
                '0.0',
                'null',
                'false',
            ):
                return []
            result = f'{variable_name(data, element)} = {init_value};'
            assert not auto_vars.data
            return [result]
    return []


def subfunction_line(subfunction: TriggerElement) -> str:
    return f'<SubFunctionType Type="SubFuncType" Library="{subfunction.library}" Id="{subfunction.element_id}"/>'


def paramdef_line(paramdef: TriggerElement) -> str:
    return f'<ParameterDef Type="ParamDef" Library="{paramdef.library}" Id="{paramdef.element_id}"/>'


def codegen_function_call(
    element: TriggerElement,
    auto_variables: AutoVarBuilder,
    end='',
    this_subfunc_order: int = 0,
    parent_trigger_name: str = 't',
) -> list[str]:
    assert element.type == ElementType.FunctionCall
    data = repo_objects.libs[element.library]
    if '<Disabled/>' in element.lines:
        return []
    function_def_lines = [line for line in element.lines if line.startswith('<FunctionDef')]
    child_elements = [child for child in data.children.get(element, []) if child.type != ElementType.Comment]
    parameters = [child for child in child_elements if child.type == ElementType.Param]
    subfunction_parameters = [child for child in child_elements if child.type == ElementType.FunctionCall]
    if not function_def_lines:
        return ['@nofunc@']
    assert len(function_def_lines) == 1
    function_def_lib, function_def = get_referenced_element(function_def_lines[0])
    function_name, param_order, subfunc_order = codegen_function_info(function_def_lib, function_def.element_id)
    script_code = function_def.get_multiline_value('ScriptCode')
    if function_def.element_id == '00000123' and function_def.library == 'Ntve':  # customscriptaction
        script_code = element.get_multiline_value('ScriptCode')
        assert script_code
    result: list[str] = []
    if script_code is None and subfunc_order:
        assert not param_order
        assert len(subfunc_order) == 1
        for index, subfunction in enumerate(subfunction_parameters):
            result.extend(codegen_function_call(subfunction, auto_variables, end=';', this_subfunc_order=index))
        return result
    # if script_code is None and '<FlagCondition/>' in function_def.lines:
    if script_code is None and '<FlagOperator/>' in function_def.lines and len(parameters) in (1, 3):
        param_order_ids = [element.element_id for element in param_order]
        parameters = sorted(parameters, key=lambda x: param_order_ids.index(parameter_def_id(x)))
        return ['(' + ' '.join(codegen_parameter(parameter, auto_variables) for parameter in parameters) + ')' + end]
    if script_code is None:
        assert not subfunc_order
        param_order_ids = [element.element_id for element in param_order]
        parameters = sorted(parameters, key=lambda x: param_order_ids.index(parameter_def_id(x)))
        event_args: list[str] = []
        if '<FlagEvent/>' in function_def.lines:
            event_args.append(parent_trigger_name)
        # Note(mm): This doesn't handle the case where a parameter is unspecified and we're supposed to fallback to the default
        return [
            function_name + '('
            + ', '.join(event_args + [codegen_parameter(parameter, auto_variables) for parameter in parameters])
            + ')' + end
        ]

    # get parameter identifiers
    auto_var_element_id = element.element_id
    param_identifier_to_element: dict[str, TriggerElement|list[TriggerElement]] = {}
    param_identifier_to_type_element: dict[str, TriggerElement] = {}
    for paramdef_element in param_order:
        identifier = paramdef_element.get_inline_value('Identifier')
        assert identifier is not None
        arguments = [child for child in parameters if paramdef_line(paramdef_element) in child.lines]
        if len(arguments) == 1:
            param_identifier_to_element[identifier] = arguments[0]
        elif arguments:
            param_identifier_to_element[identifier] = arguments
        default_line = paramdef_element.get_first_line_of_tag('Default')
        if default_line:
            default_lib, default_element = get_referenced_element(default_line)
            param_identifier_to_element.setdefault(identifier, default_element)
            continue
        paramdef_type = paramdef_element.get_attribute('Type', 'Value')
        if paramdef_type == 'sameasparent':
            parent_function_call = data.parents[element]
            assert parent_function_call.type == ElementType.FunctionCall
            auto_var_element_id = parent_function_call.element_id
            parameter_children = [child for child in data.children[parent_function_call] if child.type == ElementType.Param]
            assert len(parameter_children) == 1
            param_line = parameter_children[0].get_first_line_of_tag('ParameterDef')
            assert param_line
            _, parent_paramdef_element = get_referenced_element(param_line)
            default_line = parent_paramdef_element.get_first_line_of_tag('Default')
            param_identifier_to_type_element[identifier] = parent_paramdef_element
            if default_line:
                default_lib, default_element = get_referenced_element(default_line)
                param_identifier_to_element.setdefault(identifier, default_element)
        elif paramdef_type == 'sameas':
            same_as_line = paramdef_element.get_first_line_of_tag('TypeElement')
            assert same_as_line
            _, same_as_element = get_referenced_element(same_as_line)
            assert identifier in param_identifier_to_element
            param_identifier_to_type_element[identifier] = same_as_element
        else:
            assert identifier in param_identifier_to_element

    # get subfunction parameter identifiers
    subfunc_identifier_to_elements: dict[str, list[TriggerElement]] = {}
    for subfunc_def in subfunc_order:
        identifier = subfunc_def.get_inline_value('Identifier')
        assert identifier is not None
        arguments = [child for child in subfunction_parameters if subfunction_line(subfunc_def) in child.lines]
        # Note(mm): This doesn't cover default function arguments
        subfunc_identifier_to_elements[identifier] = arguments

    macro_pattern = re.compile(r'#(\w+)\(([^)]*)\)', re.MULTILINE)
    script_code_index = 0
    while script_code_index < len(script_code):
        line = script_code[script_code_index]
        should_print_line = True
        ate_extra_line = False
        script_code_index += 1
        if line == '#SMARTBREAK':
            line = 'break;'
        elif line == '#SMARTCONTINUE':
            line = 'continue;'
        elif '#DEFRETURN' in line:
            return_type = auto_variables.return_type
            line = line.replace('#DEFRETURN', tables.default_return_values.get(return_type, ''))
        while '#' in line and should_print_line:
            macro_match = macro_pattern.search(line)
            # Note(mm): #IFHAVESUBFUNCS sometimes spreads across multiple lines :/
            if macro_match is None:
                ate_extra_line = True
                script_code_index += 1
                line = line + ')'
                macro_match = macro_pattern.search(line)
            # while (macro_match is None and script_code_index < len(script_code)):
            #     line = f'{line}\n{script_code[script_code_index]}'
            #     macro_match = macro_pattern.search(line)
            #     script_code_index += 1
            assert macro_match is not None
            macro_name, macro_args_str = macro_match.groups()
            macro_args = macro_args_str.split(',')
            if macro_name == 'AUTOVAR':
                if len(macro_args) == 1:
                    macro_args.append('int')
                assert len(macro_args) == 2
                if macro_args[1].startswith('ancestor:'):
                    ancestor = macro_args[1].split(':', 1)[1]
                    parent = element
                    parent_function_def = function_def
                    while parent.type != ElementType.Root and parent_function_def.get_inline_value('Identifier') != ancestor:
                        parent = repo_objects.libs[parent.library].parents[parent]
                        while parent.type not in (ElementType.Root, ElementType.FunctionCall):
                            parent = repo_objects.libs[parent.library].parents[parent]
                        function_def_lib_id = parent.get_attribute('FunctionDef', 'Library')
                        parent_function_def_id = parent.get_attribute('FunctionDef', 'Id')
                        assert function_def_lib_id
                        assert parent_function_def_id
                        parent_function_def = repo_objects.libs[function_def_lib_id].objects[parent_function_def_id, ElementType.FunctionDef]
                    auto_var_element_id = parent.element_id
                elif macro_args[1] == 'parent':
                    paramdef_identifier = macro_args[0]
                    parent = data.parents[element]
                    parent_function_def_line = parent.get_first_line_of_tag('FunctionDef')
                    assert parent_function_def_line
                    parent_functiondef_lib, parent_functiondef_element = get_referenced_element(parent_function_def_line)
                    if paramdef_identifier == 'val':
                        # Note(mm): this deals specifically with Switch statements.
                        # Technically to be entirely correct, we'd preprocess all the scriptcode blocks to link the
                        # arguments in INITAUTOVAR to go from val to value.
                        paramdef_identifier = 'value'
                    parent_paramdef_element = parent_functiondef_lib.keyword_parameters[parent_functiondef_element][paramdef_identifier]
                    argument = [
                        child for child in data.children[parent]
                        if child.type == ElementType.Param and paramdef_line(parent_paramdef_element) in child.lines
                    ]
                    assert len(argument) == 1
                    auto_var_element_id = parent.element_id
                    macro_args[1] = get_variable_type(argument[0])
                auto_var_name = f'auto{auto_var_element_id}_{macro_args[0]}'
                if auto_var_name not in [x.name for x in auto_variables.data]:
                    auto_variables.append(AutoVariable(auto_var_name, macro_args[1].strip()))
                line = line.replace(macro_match.group(), auto_var_name)
            elif macro_name == 'INITAUTOVAR':
                assert len(macro_args) == 2
                auto_var_name = f'auto{auto_var_element_id}_{macro_args[0]}'
                parameter_element = param_identifier_to_element[macro_args[1]]
                assert isinstance(parameter_element, TriggerElement)
                auto_var_type = codegen_parameter_type(parameter_element) or 'int'
                auto_var_type = _type_map.get(auto_var_type, auto_var_type)
                constant_initializer = is_variable_parameter_constant(parameter_element)
                auto_variables.append(AutoVariable(auto_var_name, auto_var_type, constant=constant_initializer))
                if constant_initializer is None:
                    line = line.replace(macro_match.group(), f'{auto_var_name} = {codegen_parameter(parameter_element, auto_variables)};')
                else:
                    line = line.replace(macro_match.group(), '')
                    if not line:
                        should_print_line = False
            elif macro_name == 'PARAM':
                assert len(macro_args) in (1, 2)
                if macro_args[0] not in param_identifier_to_element:
                    line = line.replace(macro_match.group(), 'true')
                else:
                    parameter_element = param_identifier_to_element[macro_args[0]]
                    if isinstance(parameter_element, TriggerElement):
                        assert len(macro_args) == 1
                        line = line.replace(macro_match.group(), codegen_parameter(parameter_element, auto_variables))
                    else:
                        assert len(macro_args) == 2
                        param_parts = [codegen_parameter(p, auto_variables) for p in parameter_element]
                        joiner = macro_args[1].replace('" "', '')
                        line = line.replace(macro_match.group(), joiner.join(param_parts))
            elif macro_name == 'IFHAVESUBFUNCS':
                assert len(macro_args) == 2
                subfunc_elements = subfunc_identifier_to_elements[macro_args[0]]
                subfunc_elements = [subfunc_element for subfunc_element in subfunc_elements if '<Disabled/>' not in subfunc_element.lines]
                if subfunc_elements:
                    line = line.replace(macro_match.group(), macro_args[1])
                else:
                    line = line.replace(macro_match.group(), '')
                if not line and ate_extra_line:
                    should_print_line = False
            elif macro_name == 'IFSUBFUNC':
                assert len(macro_args) == 2
                assert macro_args[0] == 'notfirst'
                if this_subfunc_order == 0:
                    line = line.replace(macro_match.group(), '')
                else:
                    line = line.replace(macro_match.group(), macro_args[1])
            elif macro_name == 'SUBFUNCS':
                assert len(macro_args) in (1, 2)
                subfunc_elements = subfunc_identifier_to_elements[macro_args[0]]
                if function_def.element_id == '00000137':
                    # IfThenElse
                    if macro_args[0] == 'then':
                        starting_auto_var_amount = len(auto_variables.data)
                        starting_auto_var_index = auto_variables.append_index
                    elif macro_args[0] == 'else':
                        auto_vars_added_by_then = len(auto_variables.data) - starting_auto_var_amount
                        auto_variables.append_index = starting_auto_var_index
                if len(macro_args) == 1:
                    formatted_subfuncs = [
                        codegen_function_call(child, auto_variables, end=';', this_subfunc_order=index)
                        for index, child in enumerate(subfunc_elements)
                    ]
                    assert macro_match.group() == line
                    for subfunc_lines in formatted_subfuncs:
                        result.extend(subfunc_lines)
                    line = ''
                    should_print_line = False
                elif not subfunc_elements:
                    line = line.replace(macro_match.group(), 'true')
                else:
                    formatted_subfuncs = [
                        codegen_function_call(child, auto_variables, this_subfunc_order=index)
                        for index, child in enumerate(subfunc_elements)
                    ]
                    formatted_subfuncs = [x for x in formatted_subfuncs if x]
                    for subfunc_lines in formatted_subfuncs:
                        assert len(subfunc_lines) == 1
                    line = line.replace(macro_match.group(), macro_args[1].strip('"').join(subfunc_lines[0] for subfunc_lines in formatted_subfuncs))
                if function_def.element_id == '00000137' and macro_args[0] == 'else':
                    # IfThenElse cleanup
                    auto_variables.append_index += auto_vars_added_by_then
            else:
                assert False, f'Macro not implemented: {macro_name}'
        if should_print_line:
            result.extend(line.split('\n'))
    # keywords:
    # AUTOVAR
    # DEFRETURN
    # IFHAVESUBFUNCS
    # IFSUBFUNC
    # INITAUTOVAR
    # PARAM
    # PRESETIDENT
    # SMARTBREAK
    # SMARTCONTINUE
    # SUBFUNCS
    return result


def parse_return_type(element: TriggerElement) -> str:
    in_return_type_block = False
    for line in element.lines:
        if line == '<ReturnType>':
            in_return_type_block = True
        elif line == '</ReturnType>':
            in_return_type_block = False
        elif in_return_type_block and (m := re.match(r'^<Type Value="(\w+)"/>', line)):
            return _type_map.get(m.group(1), m.group(1))
    return 'void'


def codegen_function_def(data: TriggerLib, element: TriggerElement) -> str:
    result: list[str] = []
    indent = 0
    assert element.type == ElementType.FunctionDef
    parameters = [child for child in data.children[element] if child.type == ElementType.ParamDef]
    functions = [child for child in data.children[element] if child.type == ElementType.FunctionCall]
    variables = [child for child in data.children[element] if child.type == ElementType.Variable]
    this_function_name = function_name(data, element)
    return_type = parse_return_type(element)
    if return_type == 'preset':
        type_element_line = element.get_first_line_of_tag('TypeElement')
        assert type_element_line
        _, preset_element = get_referenced_element(type_element_line)
        assert preset_element.type == ElementType.Preset
        return_type = preset_backing_type(preset_element)

    if '<Disabled/>' in element.lines:
        return ''

    parameter_types_names = [(get_variable_type(parameter), parameter_name(data, parameter)) for parameter in parameters]
    trigger_vars: list[tuple[str, str]] = []
    if '<FlagCreateThread/>' in element.lines:
        trigger_basename = f'auto_{this_function_name}'
        trigger_name = f'{trigger_basename}_Trigger'
        this_function_name = f'{trigger_name}Func'
        result.append(f'trigger {trigger_name} = null;')
        trigger_vars = [(parameter_type, f'{trigger_basename}_{_parameter_name}') for parameter_type, _parameter_name in parameter_types_names]
        for parameter_type, _parameter_name in trigger_vars:
            result.append(f'{parameter_type} {_parameter_name};')
        result.append('')
        result.append(
            f'{return_type} {function_name(data, element)} ('
            + (', '.join(" ".join(x) for x in parameter_types_names))
            + ') {'
        )
        for trigger_type_name, parameter_type_name in zip(trigger_vars, parameter_types_names):
            result.append(f'    {trigger_type_name[1]} = {parameter_type_name[1]};')
        if trigger_vars:
            result.append('')
        result.append(f'    if ({trigger_name} == null) {{')
        result.append(f'        {trigger_name} = TriggerCreate("{this_function_name}");')
        result.append('    }')
        result.append('')
        result.append(f'    TriggerExecute({trigger_name}, false, false);')
        result.append('}')
        result.append('')
        trigger_parameter_types_names = parameter_types_names
        parameter_types_names = [('bool', 'testConds'), ('bool', 'runActions')]
        return_type = 'bool'

    elif '<FlagEvent/>' in element.lines:
        parameter_types_names[0:0] = [('trigger', 't')]

    def _print(string: str = '', this_indent: int|None = None) -> None:
        if this_indent is None:
            this_indent = indent
        result.append(('    ' * this_indent * (len(string) > 0)) + string)

    _print(
        f'{return_type} {this_function_name} ('
        + (', '.join(" ".join(x) for x in parameter_types_names))
        + ') {'
    )
    indent += 1

    if trigger_vars:
        for trigger_type_name, parameter_type_name in zip(trigger_vars, trigger_parameter_types_names):
            _print(f'{trigger_type_name[0]} {parameter_type_name[1]} = {trigger_type_name[1]};')
        _print('')

    if variables:
        _print('// Variable Declarations')
    for variable in variables:
        variable_type = get_variable_type(variable)
        _print(f'{variable_type} {local_variable_name(data, variable)};')
    if variables:
        _print()
    _print('// Automatic Variable Declarations')
    auto_var_insertion_point = len(result)
    automatic_variables = AutoVarBuilder([], return_type=return_type)
    if variables:
        _print('// Variable Initialization')
        for variable in variables:
            for line in codegen_variable_init(variable):
                _print(line)
        _print()
    _print('// Implementation')
    for function in functions:
        lines = codegen_function_call(function, automatic_variables, end=';')
        indent, lines = indent_lines(lines, indent)
        result.extend(lines)
    if return_type != 'void':
        # Note(mm): This doesn't handle the case where the else block returns but the main if block doesn't
        last_substantive_line = -1
        while last_substantive_line > -len(result) and result[last_substantive_line].strip() in ('}', ''):
            last_substantive_line -= 1
        if not result[last_substantive_line].strip().startswith('return'):
            _print(f'return {tables.default_return_values[return_type]};')
    if automatic_variables:
        result[auto_var_insertion_point:auto_var_insertion_point] = ['']
    result[auto_var_insertion_point:auto_var_insertion_point] = [
        f'    {"const " if x.constant else ""}{x.var_type} {x.name}{" = " if x.constant else ""}{x.constant or ""};'
        for x in automatic_variables.data
    ]
    indent -= 1
    assert indent == 0
    _print('}')
    return '\n'.join(result)


def find_element_names(trigger_strings: list[str]
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    CATEGORY_PREFIX = 'Category/Name/lib_ABFE498B_'
    # CUSTOM_SCRIPT_PREFIX = 'CustomScript/Name/lib_ABFE498B_'
    FUNCTION_PREFIX = 'FunctionDef/Name/lib_ABFE498B_'
    # PARAM_PREFIX = 'ParamDef/Name/lib_ABFE498B_'
    TRIGGER_PREFIX = 'Trigger/Name/lib_ABFE498B_'
    VARIABLE_PREFIX = 'Variable/Name/lib_ABFE498B_'
    category_result: list[tuple[str, str]] = []
    function_result: list[tuple[str, str]] = []
    other_result: list[tuple[str, str]] = []
    for line in trigger_strings:
        for prefix, result_list in (
            (CATEGORY_PREFIX, category_result),
            (FUNCTION_PREFIX, other_result),
            (TRIGGER_PREFIX, other_result),
            (VARIABLE_PREFIX, other_result),
        ):
            if line.startswith(prefix):
                result_list.append(
                    (line[len(prefix):len(prefix)+8], line[len(prefix)+9:-1])
                )
                break
    return category_result, category_result + other_result


def codegen_trigger(data: TriggerLib, trigger: TriggerElement) -> str:
    result: list[str] = []
    assert trigger.type == ElementType.Trigger
    variables = [child for child in data.children[trigger] if child.type == ElementType.Variable]
    event_lines = [line for line in trigger.lines if line.strip().startswith('<Event')]
    events = [get_referenced_element(line)[1] for line in event_lines]
    condition_lines = [line for line in trigger.lines if line.strip().startswith('<Condition')]
    conditions = [get_referenced_element(line)[1] for line in condition_lines]
    functions = [
        child for child in data.children[trigger]
        if child.type == ElementType.FunctionCall
        and child not in events
        and child not in conditions
    ]

    indent = 0
    def _print(string: str = '', this_indent: int|None = None) -> None:
        if this_indent is None:
            this_indent = indent
        result.append(('    ' * this_indent * (len(string) > 0)) + string)

    TRIGGER_NAME = trigger_name(data, trigger)
    _print('//' + ('-' * 98))
    _print(f'// Trigger: {data.id_to_string(trigger.element_id, trigger.type, "@trigger")}')
    _print('//' + ('-' * 98))
    _print(f'bool {TRIGGER_NAME}_Func (bool testConds, bool runActions) {{')
    indent += 1
    if variables:
        _print('// Variable Declarations')
        for variable in variables:
            variable_type = get_variable_type(variable)
            _print(f'{variable_type} {local_variable_name(data, variable)};')
        _print()
    
    _print('// Automatic Variable Declarations')
    auto_var_insertion_point = len(result)
    automatic_variables = AutoVarBuilder([], return_type='bool')

    if variables:
        _print('// Variable Initialization')
        for variable in variables:
            for line in codegen_variable_init(variable):
                _print(line)
        _print()
    
    if conditions:
        _print('// Conditions')
        _print('if (testConds) {')
        for element_index, element in enumerate(conditions):
            if element_index:
                _print()
            condition_result = codegen_function_call(element, automatic_variables)
            assert len(condition_result) == 1
            _print(f'    if (!({condition_result[0]})) {{')
            _print('        return false;')
            _print('    }')
        _print('}')
        _print()

    if functions:
        _print('// Actions')
        _print('if (!runActions) {')
        _print('    return true;')
        _print('}')
        _print()
    for function in functions:
        lines = codegen_function_call(function, automatic_variables, end=';')
        indent, lines = indent_lines(lines, indent)
        result.extend(lines)
    _print('return true;')

    if automatic_variables:
        result[auto_var_insertion_point:auto_var_insertion_point] = ['']
    result[auto_var_insertion_point:auto_var_insertion_point] = [
        f'    {"const " if x.constant else ""}{x.var_type} {x.name}{" = " if x.constant else ""}{x.constant or ""};'
        for x in automatic_variables.data
    ]
    indent -= 1
    assert indent == 0
    _print('}')

    _print()
    _print(f'//{"-"*98}')
    _print(f'void {TRIGGER_NAME}_Init () {{')
    indent += 1
    _print(f'{TRIGGER_NAME} = TriggerCreate("{TRIGGER_NAME}_Func");')
    if '<InitOff/>' in trigger.lines:
        _print(f'TriggerEnable({TRIGGER_NAME}, false);')
    for event in events:
        lines = codegen_function_call(event, automatic_variables, end=';', parent_trigger_name=TRIGGER_NAME)
        indent, lines = indent_lines(lines, indent)
        result.extend(lines)
    indent -= 1
    _print('}')
    _print()
    return '\n'.join(result)


def codegen_library(data: TriggerLib) -> str:
    global_custom_scripts: list[TriggerElement] = []
    function_defs: list[TriggerElement] = []
    triggers: list[TriggerElement] = []
    global_variables: list[TriggerElement] = []
    for element in data.objects.values():
        if data.parents[element].type not in (ElementType.Root, ElementType.Category):
            continue
        elif element.type == ElementType.CustomScript:
            global_custom_scripts.append(element)
        elif element.type == ElementType.FunctionDef:
            function_defs.append(element)
        elif element.type == ElementType.Trigger:
            triggers.append(element)
        elif element.type == ElementType.Variable:
            global_variables.append(element)

    result: list[str] = []
    result.append('include "TriggerLibs/NativeLib"')
    for dependency_name in data.dependencies:
        dependency = repo_objects.libs_by_name[dependency_name]
        result.append(f'include "Lib{dependency.library}"')
    result.append('')
    result.append(f'include "Lib{data.library}_h"')
    result.append('')
    result.append('//' + ('-' * 98))
    library_string_key = f'Library/Name/{data.library}'
    result.append(f'// Library: {data.trigger_strings[library_string_key]}')
    result.append('//' + ('-' * 98))
    result.append('// External Library Initialization')
    result.append(f'void lib{data.library}_InitLibraries () {{')
    result.append('    libNtve_InitVariables();')
    for dependency_name in data.dependencies:
        if dependency_name == 'ArchipelagoPatches':
            # Note(mm): This doesn't generate any variables right now
            # And I don't feel like parsing the whole thing every time to check it
            continue
        dependency = repo_objects.libs_by_name[dependency_name]
        result.append(f'    lib{dependency.library}_InitVariables();')
    result.append('}')
    result.append('')

    result.append('// Variable Initialization')
    result.append(f'bool lib{data.library}_InitVariables_completed = false;')
    result.append('')
    result.append(f'void lib{data.library}_InitVariables () {{')
    result.append(f'    if (lib{data.library}_InitVariables_completed) {{')
    result.append('        return;')
    result.append('    }')
    result.append('')
    result.append(f'    lib{data.library}_InitVariables_completed = true;')
    result.append('')
    for variable in global_variables:
        var_init = codegen_variable_init(variable)
        result.extend((' '* 4) + line for line in var_init)
    result.append('}')
    result.append('')

    if global_custom_scripts:
        result.append('// Custom Script')
    for custom_script in global_custom_scripts:
        result.append('//' + ('-' * 98))
        result.append(f'// Custom Script: {data.id_to_string(custom_script.element_id, custom_script.type, "@customscript")}')
        result.append('//' + ('-' * 98))
        custom_script_lines = codegen_custom_script(custom_script)
        result.extend(indent_lines(custom_script_lines)[1])
        result.append('')
    if global_custom_scripts:
        result.append(f'void lib{data.library}_InitCustomScript () {{')
        for custom_script in global_custom_scripts:
            if custom_script_func := custom_script.get_inline_value('InitFunc'):
                result.append(f'{custom_script_func}();')
        result.append('}')
        result.append('')

    presets = [
        x for x in data.objects.values()
        if x.type == ElementType.Preset
    ]
    if presets:
        result.append('// Presets')
    result.append('// Functions')
    for element in function_defs:
        function_def = codegen_function_def(data, element)
        if function_def:
            result.append(function_def)
            result.append('')
    result.append('// Triggers')
    for element in triggers:
        trigger_result = codegen_trigger(data, element)
        result.append(trigger_result)
    
    if triggers:
        result.append(f'void lib{data.library}_InitTriggers () {{')
        for element in triggers:
            result.append(f'    {trigger_name(data, element)}_Init();')
        result.append('}')
        result.append('')

    # Library init
    result.append(f'//{"-"*98}')
    result.append('// Library Initialization')
    result.append(f'//{"-"*98}')
    result.append(f'bool lib{data.library}_InitLib_completed = false;')
    result.append('')
    result.append(f'void lib{data.library}_InitLib () {{')
    result.append(f'    if (lib{data.library}_InitLib_completed) {{')
    result.append('        return;')
    result.append('    }')
    result.append('')
    result.append(f'    lib{data.library}_InitLib_completed = true;')
    result.append('')
    result.append(f'    lib{data.library}_InitLibraries();')
    if global_variables:
        result.append(f'    lib{data.library}_InitVariables();')
    if global_custom_scripts:
        result.append(f'    lib{data.library}_InitCustomScript();')
    if triggers:
        result.append(f'    lib{data.library}_InitTriggers();')
    result.append('}')
    result.append('')
    return '\n'.join(result)


if __name__ == '__main__':
    import sys
    import os
    ap_triggers = repo_objects.libs_by_name['ArchipelagoTriggers']
    ap_player = repo_objects.libs_by_name['ArchipelagoPlayer']
    from autotrigger.at import add_funcs, interactive
    if False:
        error, category = interactive.path_to_obj(
            '/TechTree/Zerg/Unlocks/MiscUpgrades',
            ap_triggers.root(), ap_triggers
        )
        assert not error
        assert not add_funcs.add_unlock_functiondef(
            ap_triggers, category, -1, 'AP_Triggers_Zerg_CreepStomach', 'AP_ZergCreepStomach',
        )
        sorted_elements = sort_elements(ap_triggers)
        ap_triggers.objects = {(x.element_id, x.type): x for x in sorted_elements}
    if '-i' in sys.argv:
        interactive.interactive(repo_objects)
    else:
        ap_triggers.sort_elements()
        ap_player.sort_elements()
        os.makedirs('out', exist_ok=True)
        with open('out/aptriggers.log', 'w') as fp:
            print(codegen_library(ap_triggers), file=fp)
        with open('out/applayer.log', 'w') as fp:
            print(codegen_library(ap_player), file=fp)
        write_triggers_xml(ap_triggers, 'out/aptriggers.xml')
        write_triggers_strings(ap_triggers, 'out/aptriggerstrings.txt')

