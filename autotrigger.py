"""
Script for modifying `Trigger` files with unlock triggers,
so we can update GUI triggers without having to put up with the editor.
todo:
* presets
* triggers
* What's going on with StringExternal vs StringToText("")
* loops
* Array assignments
"""

import os
from typing import NamedTuple, Self
from collections import deque
import enum
import re

from scripts.at import tables

SCRIPTS_FOLDER = os.path.dirname(__file__)
REPO_ROOT = os.path.normpath(os.path.dirname(SCRIPTS_FOLDER))
MODS_FOLDER = f"{REPO_ROOT}/Mods"
GALAXY_FILE = f"{MODS_FOLDER}/ArchipelagoTriggers.SC2Mod/Base.SC2Data/LibABFE498B.galaxy"
TRIGGERS_FILE = f"{MODS_FOLDER}/ArchipelagoTriggers.SC2Mod/Triggers"
TRIGGER_STRINGS_FILE = f"{MODS_FOLDER}/ArchipelagoTriggers.SC2Mod/enUS.SC2Data/LocalizedData/TriggerStrings.txt"


class ElementType(enum.StrEnum):
    Root = 'Root'
    Category = 'Category'
    Trigger = 'Trigger'
    FunctionCall = 'FunctionCall'
    FunctionDef = 'FunctionDef'
    Param = 'Param'
    ParamDef = 'ParamDef'
    Comment = 'Comment'
    Variable = 'Variable'
    CustomScript = 'CustomScript'
    Structure = 'Structure'
    Preset = 'Preset'
    PresetValue = 'PresetValue'


_type_pattern = re.compile(r'Type="(\w+)"')
_id_pattern = re.compile(r'\bId="([0-9A-F]{8})"')
_library_id_pattern = re.compile(r'Library="(\w+)" Id="([0-9A-F]{8})"')
_function_def_id_pattern = re.compile(r'^<FunctionDef Type="FunctionDef" Library="(\w+)" Id="([0-9A-F]{8})"/>')

class TriggerElement:
    __slots__ = (
        'lines',
        'type',
        'library',
        'element_id',
    )
    def __init__(self, lines: list[str], library: str) -> None:
        self.lines = lines
        self.library = library
        if self.lines[0] == '<Root>':
            self.type = ElementType.Root
            self.element_id: str = 'root'
        else:
            self.type = ElementType(re.search(_type_pattern, lines[0]).group(1))
            m = re.search(_id_pattern, lines[0])
            self.element_id = m.group(1)
            assert self.element_id
    
    def display_string(self, id_to_string: dict[str, str]) -> str:
        return f'{self.type} {id_to_string.get(self.element_id, "Unnamed")} ({self.element_id})'
    
    def get_value(self, tag: str) -> str|None:
        for line in self.lines:
            if line.startswith(f'<{tag}>'):
                return line[len(tag)+2:-(len(tag)+3)]
        return None
    
    def get_attribute(self, tag: str, attribute: str) -> str|None:
        for line in self.lines:
            if line.startswith(f'<{tag}'):
                if m := re.search(rf'\b{attribute}="([^"]+)"', line):
                    return m.group(1)
        return None
        

class TriggerObjects:
    def __init__(self) -> None:
        self.library = ''
        self.objects: dict[str, TriggerElement] = {}
        self.trigger_strings: dict[str, str] = {}
        self.id_to_string: dict[str, str] = {}
        self.children: dict[str, list[str]] = {}
        self.parents: dict[str, str] = {}
        self.dependencies: list[str] = []
    
    def parent_element(self, element: TriggerElement) -> TriggerElement:
        return self.objects[self.parents[element.element_id]]

    def parse(self, triggers_file: str = TRIGGERS_FILE, trigger_strings_file: str = TRIGGER_STRINGS_FILE) -> Self:
        self._parse_triggers(triggers_file)
        self._update_indices()
        document_info_file = os.path.join(os.path.dirname(TRIGGERS_FILE), 'DocumentInfo')
        self._parse_dependencies(document_info_file)
        self._parse_trigger_strings(trigger_strings_file)
        return self

    def _parse_triggers(self, triggers_file: str = TRIGGERS_FILE) -> None:
        with open(triggers_file, 'r') as fp:
            lines = fp.readlines()
        current_obj: list[str]|None = None
        for line_number, line in enumerate(lines[2:], 3):
            line = line.strip()
            if not line:
                continue
            if line_number == 3:
                PREFIX = '<Library Id="'
                assert line.startswith(PREFIX), "Line 3 didn't have the library ID"
                self.library = line[len(PREFIX):len(PREFIX)+8]
            elif line in ('</Library>', '</TriggerData>'):
                continue
            elif line.startswith('<Element') or line == '<Root>':
                assert current_obj is None
                current_obj = [line]
            elif line in ('</Element>', '</Root>'):
                assert current_obj is not None
                current_obj.append(line)
                new_element = TriggerElement(current_obj, self.library)
                self.objects[new_element.element_id] = new_element
                current_obj = None
            else:
                assert current_obj is not None
                current_obj.append(line)
    
    def _parse_dependencies(self, document_info: str) -> None:
        with open(document_info, 'r') as fp:
            lines = fp.readlines()
        dependency_pattern = re.compile(r'^<Value>file:Mods[\\/]([\w]+)\.SC2Mod</Value>')
        in_dependencies = False
        for line in lines[2:-1]:
            line = line.strip()
            if line == '<Dependencies>':
                in_dependencies = True
            elif line == '</Dependencies>':
                in_dependencies = False
            elif in_dependencies and (m := dependency_pattern.match(line)):
                self.dependencies.append(m.group(1))
    
    def _parse_trigger_strings(self, trigger_strings_file: str = TRIGGER_STRINGS_FILE) -> None:
        with open(trigger_strings_file, 'r') as fp:
            lines = fp.readlines()
        self.trigger_strings.clear()
        for line in lines:
            if not line:
                continue
            key, val = line.strip().split('=', 1)
            self.trigger_strings[key] = val
            self.id_to_string[key[-8:]] = val
        self.id_to_string['root'] = 'Root'
    
    def _update_indices(self) -> None:
        self.children.clear()
        self.parents.clear()
        category_item_pattern = re.compile(rf'^<Item Type="\w+" Library="{self.library}" Id="([0-9A-F]{{8}})"/>$')
        for _, obj in self.objects.items():
            if obj.type in (ElementType.Root, ElementType.Category):
                self.children[obj.element_id] = []
                for line in obj.lines[1:-1]:
                    m = category_item_pattern.match(line)
                    if m is not None:
                        self.children[obj.element_id].append(m.group(1))
            elif obj.type in (ElementType.Comment, ElementType.CustomScript):
                pass
            else:
                self.children[obj.element_id] = []
                for line in obj.lines[1:-1]:
                    if f'Library="{self.library}"' in line:
                        self.children[obj.element_id].append(re.search(_id_pattern, line).group(1))
        for parent, children in self.children.items():
            if self.objects[parent].type in (ElementType.Category, ElementType.Root):
                for child in children:
                    self.parents[child] = parent
            else:            
                for child in children:
                    self.parents.setdefault(child, parent)
        self.parents['root'] = 'root'

    def _sort_elements(self) -> list[TriggerElement]:
        child_order: list[str] = []
        search_stack = deque(['root'])
        while search_stack:
            new_node = search_stack.pop()
            if new_node not in child_order:
                child_order.append(new_node)
                
                this_type = self.objects[new_node].type
                children = self.children.get(new_node, [])
                child_filter = []
                if this_type not in (ElementType.Category, ElementType.Root):
                    child_filter.extend([ElementType.Trigger, ElementType.FunctionDef])
                if this_type != ElementType.FunctionDef:
                    child_filter.append(ElementType.ParamDef)
                if child_filter:
                    children = [
                        child for child in children
                        if self.objects[child].type not in child_filter
                    ]
                search_stack.extend(reversed(children))

        child_index = {x: index for index, x in enumerate(child_order)}
        child_index['root'] = -1
        return sorted(self.objects.values(), key=lambda x: child_index[x.element_id])
    
    
    def write_triggers(self, triggers_file: str = TRIGGERS_FILE) -> None:
        sorted_elements = self._sort_elements()
        with open(triggers_file, 'w') as fp:
            def _print(string: str, indent_level: int = 0) -> None:
                print((' ' * (4 * indent_level)) + string, file=fp)
            _print('<?xml version="1.0" encoding="utf-8"?>')
            _print('<TriggerData>')
            _print('<Library Id="ABFE498B">', 1)
            for obj in sorted_elements:
                indent_level = 2
                for line in obj.lines:
                    this_indent_level, indent_level = get_indentation(line, indent_level)
                    _print(line, this_indent_level)
                assert indent_level == 2

            _print('</Library>', 1)
            fp.write('</TriggerData>')


class RepoObjects:
    def __init__(self) -> None:
        mods = [
            'ArchipelagoTriggers',
            'ArchipelagoCore',
            'ArchipelagoPlayer',
            'ArchipelagoPatches',
        ]
        file_paths = [
            (f'{MODS_FOLDER}/{x}.SC2Mod/Triggers', f'{MODS_FOLDER}/{x}.SC2Mod/enUS.SC2Data/LocalizedData/TriggerStrings.txt')
            for x in mods
        ]
        libs = [TriggerObjects().parse(triggers_file, trigger_strings_file) for triggers_file, trigger_strings_file in file_paths]
        self.libs = {
            lib.library: lib
            for lib in libs
        }
        self.libs_by_name = dict(zip(mods, libs))
repo_objects = RepoObjects()


class AutoVariable(NamedTuple):
    name: str
    var_type: str


class AutoVarBuilder:
    def __init__(self, data: list[AutoVariable], loop_var: str= '@loop-var') -> None:
        self.data = data
        self.loop_var = loop_var
    def __bool__(self) -> bool:
        return bool(self.data)
    def append(self, variable: AutoVariable) -> None:
        self.data.append(variable)


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


_type_map = {
    'gamelink': 'string',
    'difficulty': 'int',
    'filepath': 'string',
    'userinstance': 'string',
    'actormsg': 'string',
    'catalogfieldpath': 'string',
    'userfield': 'string',
}


def get_variable_type(lines: list[str]) -> str:
    in_variable_type = False
    variable_type = ''
    for line in lines:
        if line == '<VariableType>' or line == '<ParameterType>':
            in_variable_type = True
        elif in_variable_type and (m := re.match(r'<Type Value="(\w+)"', line)):
            variable_type = m.group(1)
            break
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


_identifier_pattern = re.compile(r'^<Identifier>([^<]+)</Identifier>')
def get_identifier(element: TriggerElement) -> str|None:
    for line in element.lines:
        if m := _identifier_pattern.match(line):
            return m.group(1)
    return None


def parameter_name(display_name: str) -> str:
    return escape_identifier('lp_' + display_name[0].lower() + display_name[1:].replace(' ', ''))

def global_variable_name(data: TriggerObjects, element: TriggerElement) -> str:
    assert element.type == ElementType.Variable
    identifier = get_identifier(element)
    if identifier is None:
        identifier = toggle_case_of_first_letter(escape_identifier(data.id_to_string[element.element_id]))
    return f'lib{data.library}_gv_{identifier}'

def local_variable_name(data: TriggerObjects, element: TriggerElement) -> str:
    assert element.type == ElementType.Variable
    identifier = get_identifier(element)
    if identifier is None:
        identifier = data.id_to_string[element.element_id]
        identifier = identifier[0].lower() + identifier[1:]
    return escape_identifier('lv_' + identifier)

def variable_name(data: TriggerObjects, element: TriggerElement) -> str:
    if data.objects[data.parents[element.element_id]].type in (ElementType.Root, ElementType.Category):
        return global_variable_name(data, element)
    return local_variable_name(data, element)


def function_name(data: TriggerObjects, element: TriggerElement) -> str:
    identifier = get_identifier(element)
    if identifier is not None:
        return f'lib{data.library}_gf_{identifier}'
    return f'lib{data.library}_gf_{escape_identifier(data.id_to_string[element.element_id])}'


def preset_value(data: TriggerObjects, element: TriggerElement) -> str:
    for line in element.lines[1:-1]:
        if line.startswith('<Identifier>'):
            return line[len('<Identifier>'):-len('</Identifier>')]
        elif line.startswith('<Value>'):
            return line[len('<Value>'):-len('</Value>')]
    return f'lib{data.library}_ge_' + escape_identifier(data.id_to_string[element.element_id])


def codegen_parameter(element: TriggerElement, auto_variables: AutoVarBuilder) -> str:
    assert element.type == ElementType.Param
    value = ''
    _type = ''
    variable = ''
    array_param = []
    expression = ''

    _value_pattern = re.compile(r'^<(ValueType|ValueId) (Type|Id)="(\w+)"')
    _variable_pattern = re.compile(r'^<Variable Type="Variable" Library="(\w+)" Id="([0-9A-F]{8})"/>')
    _array_pattern = re.compile(r'<Array Type="Param" Library="(\w+)" Id="([0-9A-F]{8})"/>')
    _value_element_pattern = re.compile(r'^<ValueElement Type="(Trigger|Preset)" Library="(\w+)" Id="([0-9A-F]{8})"/>')
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
                return m.group(3)
            assert tag == 'ValueType'
            _type = _type_map.get(m.group(3), m.group(3))
        elif m := re.match(_variable_pattern, line):
            lib_id = m.group(1)
            var_id = m.group(2)
            assert lib_id != 'Ntve'
            lib = repo_objects.libs[lib_id]
            variable = variable_name(lib, lib.objects[var_id])
        elif m := re.match(_array_pattern, line):
            lib_id, param_id = m.groups()
            param_element = repo_objects.libs[lib_id].objects[param_id]
            array_param.append('[' + codegen_parameter(param_element, auto_variables) + ']')
        elif m := re.match(_function_call_pattern, line):
            lib_id = m.group(1)
            assert lib_id != 'Ntve'
            function_call_element = repo_objects.libs[lib_id].objects[m.group(2)]
            result = codegen_function_call(function_call_element, auto_variables)
            assert len(result) == 1
            return result[0]
        elif m := re.match(_value_element_pattern, line):
            if m.group(1) == 'Trigger':
                lib_id = m.group(2)
                assert lib_id != 'Ntve'
                trigger_name = repo_objects.libs[lib_id].id_to_string[m.group(3)]
                return f'lib{lib_id}_gt_{trigger_name}'
            elif m.group(1) == 'Preset':
                assert m.group(2) == 'Ntve'
                preset_id = m.group(3)
                return tables.native_presets.get(preset_id, f'@preset{preset_id}')
            else:
                assert False, f"Don't know how to handle ValueElement of type {m.group(1)}"
        elif m := re.match(_preset_pattern, line):
            lib_id = m.group(1)
            preset_id = m.group(2)
            if lib_id == 'Ntve':
                return tables.native_presets.get(preset_id, f'@{preset_id}@')
            lib = repo_objects.libs[lib_id]
            return preset_value(lib, lib.objects[preset_id])
        elif line.startswith('<Parameter Type="ParamDef"'):
            lib_id, _id = _library_id_pattern.search(line).groups()
            return parameter_name(repo_objects.libs[lib_id].id_to_string[_id])
    if array_param:
        assert variable
        return f'{variable}{"".join(array_param)}'
    if variable:
        return variable
    if _type and _type == 'text':
        data = repo_objects.libs[element.library]
        # if element.element_id in data.id_to_string:
        return f'StringExternal("{element.type}/Value/lib_{element.library}_{element.element_id}")'
        # return 'StringToText("")'
    if expression:
        lib = repo_objects.libs[element.library]
        children = [lib.objects[x] for x in lib.children[element.element_id]]
        expression_to_child = {
            child.get_attribute('ExpressionCode', 'Value'): codegen_parameter(child, auto_variables)
            for child in children
        }
        return '(' + re.sub(
            r'~([A-Z]+)~',
            lambda m: expression_to_child.get(m.group(1)),
            expression,
        ) + ')'
    if _type == 'string' and not value:
        return '""'
    if not value:
        return f'@param{element.element_id}'
    if _type == 'fixed':
        return str(float(value))
    if _type == 'string':
        return f'"{repr(value)[1:-1]}"'
    if _type == 'abilcmd':
        return f'AbilityCommand("{value}", 0)'
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



def codegen_function_info(function_def: str) -> tuple[str, list[str]]:
    assert function_def.startswith('<FunctionDef Type="FunctionDef"')
    library, _id = re.match(_function_def_id_pattern, function_def).groups()
    if library in repo_objects.libs:
        data = repo_objects.libs[library]
        return (
            function_name(data, data.objects[_id]),
            [child for child in data.children[_id] if data.objects[child].type == ElementType.ParamDef]
        )
    return tables.native_functions.get((library, _id), (f'@unknown{_id}', []))


def parameter_def_id(element: TriggerElement) -> str:
    assert element.type == ElementType.Param
    param_def_pattern = re.compile(r'<ParameterDef Type="ParamDef" Library="\w+" Id="([0-9A-F]{8})"')
    for line in element.lines:
        if m := re.match(param_def_pattern, line):
            return m.group(1)
    assert False


def unescape_xml_string(string: str) -> str:
    return (
        string
        .replace('&quot;', '"')
        .replace('&apos;', "'")
        .replace('&lt;', '<')
        .replace('&gt;', '>')
        .replace('&amp;', '&')
    )


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
            library, var_id = _library_id_pattern.search(line).groups()
            var_element = repo_objects.libs[library].objects[var_id]
            auto_vars = []
            init_value = codegen_parameter(var_element, auto_vars)
            if '<Constant/>' in element.lines:
                # Initialized in the _h file
                # Note(mm): Technically, `<Constant/>` should appear as a child to `<Type>` specifically
                return []
            if init_value in (
                '0',
                '0.0',
                'null',
                'false',
                '@00000542@',  # uninitialized difficulty
                '@50BDC6EF@',  # uninitialized text
            ):
                return []
            result = f'{variable_name(data, element)} = {init_value};'
            assert not auto_vars
            return [result]
    return []


def subfunction_line(subfunction_type_id: str) -> str:
    return f'<SubFunctionType Type="SubFuncType" Library="Ntve" Id="{subfunction_type_id}"/>'


def paramdef_line(paramdef_id: str, library: str = 'Ntve') -> str:
    return f'<ParameterDef Type="ParamDef" Library="{library}" Id="{paramdef_id}"/>'


def codegen_function_call(
    element: TriggerElement,
    auto_variables: AutoVarBuilder,
    end=''
) -> list[str]:
    assert element.type == ElementType.FunctionCall
    data = repo_objects.libs[element.library]
    result: list[str] = []
    function_def = [line for line in element.lines if line.startswith('<FunctionDef')]
    parameters = [data.objects[child] for child in data.children.get(element.element_id, []) if data.objects[child].type == ElementType.Param]
    if not function_def:
        return ['@nofunc@']
    assert len(function_def) == 1
    function_name, param_order = codegen_function_info(function_def[0])
    try:
        parameters = sorted(parameters, key=lambda x: param_order.index(parameter_def_id(x)))
    except ValueError as ex:
        f = []
        for parameter in parameters:
            for line in parameter.lines:
                if line.startswith('<ParameterDef'):
                    f.append(_library_id_pattern.search(line).group(2))
        print(f'Missing parameters: (\'Ntve\', {function_name[-8:]!r}): ({function_name!r}, {f}),')
    if function_name.startswith('@@'):
        result.append(function_name[2:])
    elif function_name == '@set':
        result.append(' = '.join(codegen_parameter(param, auto_variables) for param in parameters) + end)
    elif function_name == '@add':
        result.append('(' + ' + '.join(codegen_parameter(param, auto_variables) for param in parameters) + ')')
    elif function_name == '@custom-script':
        result.extend(codegen_custom_script(element))
    elif function_name == '@binary-op':
        result.append('(' + ' '.join(codegen_parameter(param, auto_variables) for param in parameters) + ')' + end)
    elif function_name == '@binary-op-statement':
        result.append(' '.join(codegen_parameter(param, auto_variables) for param in parameters) + end)
    elif function_name == '@binary-op-statement-eq':
        assert len(parameters) == 3
        params = [codegen_parameter(p, auto_variables) for p in parameters]
        result.append(f'{params[0]} {params[1]}= {params[2]}' + end)
    elif function_name == '@eq':
        result.append('(' + ' '.join(codegen_parameter(param, auto_variables) for param in parameters) + ')' + end)
    elif function_name == '@return':
        assert len(parameters) == 1
        result.append(f'return {codegen_parameter(parameters[0], auto_variables)};')
    elif function_name == '@return-default':
        data = repo_objects.libs[element.library]
        parent = element
        while parent.type not in (ElementType.Root, ElementType.Category, ElementType.FunctionDef):
            parent = data.objects[data.parents[parent.element_id]]
        assert parent.type == ElementType.FunctionDef
        return_type = parent.get_attribute('Type', 'Value')
        if return_type is None:
            default_value = ''
        else:
            default_value = tables.default_return_values[return_type]
        result.append(f'return {default_value};')
    elif function_name == '@or':
        clause_elements = [data.objects[x] for x in data.children[element.element_id] if data.objects[x].type != ElementType.Comment]
        result.append('(' + ' || '.join(';'.join(codegen_function_call(x, auto_variables)) for x in clause_elements) + ')')
    elif function_name == '@and':
        children = [data.objects[x] for x in data.children[element.element_id]]
        this_result: list[str] = []
        for child in children:
            if child.type == ElementType.Comment:
                continue
            this_result.extend(codegen_function_call(child, auto_variables))
        result.append('(' + ' && '.join(this_result) + ')')
    elif function_name == '@if-elseif':
        clause_elements = [data.objects[x] for x in data.children[element.element_id]]
        for clause_index, clause in enumerate(clause_elements):
            if subfunction_line('C7699CD9') not in clause.lines:
                continue
            children = [data.objects[x] for x in data.children[clause.element_id]]
            conditionals = [child for child in children if subfunction_line('C60B9062') in child.lines]
            body = [child for child in children if subfunction_line('BF750C3C') in child.lines]
            if conditionals:
                conditional_expr = " && ".join(codegen_function_call(conditional, auto_variables)[0] for conditional in conditionals)
            else:
                conditional_expr = 'true'
            assert body
            start = 'else if' if clause_index else 'if'
            result.append(f'{start} ({conditional_expr}) {{')
            for body_func in body:
                result.extend(codegen_function_call(body_func, auto_variables, end=';'))
            result.append('}')
    elif function_name == '@if-else':
        children = [data.objects[x] for x in data.children[element.element_id] if data.objects[x].type == ElementType.FunctionCall]
        conditionals = [x for x in children if subfunction_line('00000003') in x.lines]
        blocks = [x for x in children if subfunction_line('00000004') in x.lines]
        else_blocks = [x for x in children if subfunction_line('00000005') in x.lines]
        if conditionals:
            conditional_expr = " && ".join(codegen_function_call(conditional, auto_variables)[0] for conditional in conditionals)
        else:
            conditional_expr = 'true'
        result.append(f'if ({conditional_expr}) {{')
        # Note(mm): For whatever reason, Blizzard's code generator adds the auto variables from the else block first????
        else_block_result: list[str] = []
        if else_blocks:
            else_block_result.append('else {')
            for block in else_blocks:
                else_block_result.extend(codegen_function_call(block, auto_variables, end=';'))
            else_block_result.append('}')
        else:
            else_block_result.append('')
        for block in blocks:
            result.extend(codegen_function_call(block, auto_variables, end=';'))
        result.append('}')
        result.extend(else_block_result)
    elif function_name == '@loop-player-group':
        children = [data.objects[x] for x in data.children[element.element_id] if data.objects[x].type != ElementType.Comment]
        group = [child for child in children if paramdef_line('A4B226A9') in child.lines]
        iteration_var_param = [child for child in children if paramdef_line('857209C7') in child.lines]
        body = [child for child in children if subfunction_line('DF50D5F0') in child.lines]
        assert len(group) == 1
        assert group[0].type == ElementType.Param
        assert len(iteration_var_param) == 1
        iteration_var = [
            data.objects[child] for child in data.children[iteration_var_param[0].element_id]
            if data.objects[child].type == ElementType.Variable
        ]
        assert len(iteration_var) == 1

        loop_var_name = local_variable_name(data, iteration_var[0])
        group_var_name = f'auto{element.element_id}_g'
        auto_variables.append(AutoVariable(group_var_name, 'playergroup'))
        result.append(f'{group_var_name} = {codegen_parameter(group[0], auto_variables)};')
        result.append(f'{loop_var_name} = -1;')
        result.append('while (true) {')
        result.append(f'{loop_var_name} = PlayerGroupNextPlayer({group_var_name}, {loop_var_name});')
        result.append(f'if ({loop_var_name} < 0) {{ break; }}')
        for child in body:
            result.extend(codegen_function_call(child, auto_variables, end=';'))
        result.append('}')
    elif function_name == '@loop-unit-group':
        children = [data.objects[x] for x in data.children[element.element_id] if data.objects[x].type != ElementType.Comment]
        group = [child for child in children if paramdef_line('00000618') in child.lines]
        iteration_var_param = [child for child in children if paramdef_line('00000617') in child.lines]
        body = [child for child in children if subfunction_line('00000007') in child.lines]
        assert len(group) == 1
        assert group[0].type == ElementType.Param
        assert len(iteration_var_param) == 1
        iteration_var = [
            data.objects[child] for child in data.children[iteration_var_param[0].element_id]
            if data.objects[child].type == ElementType.Variable
        ]
        assert len(iteration_var) == 1

        loop_var_name = local_variable_name(data, iteration_var[0])
        iterator_name = f'auto{element.element_id}_u'
        group_var_name = f'auto{element.element_id}_g'
        auto_variables.append(AutoVariable(group_var_name, 'unitgroup'))
        auto_variables.append(AutoVariable(iterator_name, 'int'))
        result.append(f'{group_var_name} = {codegen_parameter(group[0], auto_variables)};')
        result.append(f'{iterator_name} = UnitGroupCount({group_var_name}, c_unitCountAll);')
        result.append(f'for (;; {iterator_name} -= 1) {{')
        result.append(f'{loop_var_name} = UnitGroupUnitFromEnd({group_var_name}, {iterator_name});')
        result.append(f'if ({loop_var_name} == null) {{ break; }}')
        for child in body:
            result.extend(codegen_function_call(child, auto_variables, end=';'))
        result.append('}')
    elif function_name == '@for-unit-in-group':
        children = [data.objects[x] for x in data.children[element.element_id] if data.objects[x].type != ElementType.Comment]
        block_statements = [child for child in children if subfunction_line('9441B8B5') in child.lines]
        assert len(parameters) == 1
        group_var_name = f'auto{element.element_id}_g'
        iterator_name = f'auto{element.element_id}_u'
        unit_var_name = f'auto{element.element_id}_var'
        auto_variables.append(AutoVariable(group_var_name, 'unitgroup'))
        auto_variables.append(AutoVariable(iterator_name, 'int'))
        auto_variables.append(AutoVariable(unit_var_name, 'unit'))
        result.append(f'{group_var_name} = {codegen_parameter(parameters[0], auto_variables)};')
        result.append(f'{iterator_name} = UnitGroupCount({group_var_name}, c_unitCountAll);')
        result.append(f'for (;; {iterator_name} -= 1) {{')
        result.append(f'{unit_var_name} = UnitGroupUnitFromEnd({group_var_name}, {iterator_name});')
        result.append(f'if ({unit_var_name} == null) {{ break; }}')
        for block in block_statements:
            result.extend(codegen_function_call(block, AutoVarBuilder(auto_variables.data, loop_var=unit_var_name), end=';'))
        result.append('}')
    elif function_name == '@loop-var':
        result.append(auto_variables.loop_var)
    elif function_name == '@switch':
        children = [data.objects[x] for x in data.children[element.element_id] if data.objects[x].type != ElementType.Comment]
        switch_var = [child for child in children if paramdef_line('B4ACF12A') in child.lines]
        case_blocks = [child for child in children if subfunction_line('AD43BC93') in child.lines]
        else_block = [child for child in children if subfunction_line('3E7C4C40') in child.lines]
        assert len(switch_var) == 1
        assert case_blocks

        switch_var_name = f'auto{element.element_id}_val'
        auto_variables.append(AutoVariable(switch_var_name, 'int'))
        result.append(f'{switch_var_name} = {codegen_parameter(switch_var[0], auto_variables)};')
        for index, block in enumerate(case_blocks):
            assert '<FunctionDef Type="FunctionDef" Library="Ntve" Id="3A1227AB"/>' in block.lines
            start = 'else if' if index else 'if'
            block_statements = [
                data.objects[x] for x in data.children[block.element_id]
                if subfunction_line('363CE97C') in data.objects[x].lines
                and data.objects[x].type != ElementType.Comment
            ]
            block_param = [data.objects[x] for x in data.children[block.element_id] if data.objects[x].type == ElementType.Param]
            assert len(block_param) < 2
            if block_param:
                result.append(f'{start} ({switch_var_name} == {codegen_parameter(block_param[0], auto_variables)}) {{')
            else:
                result.append('{')
            for child in block_statements:
                result.extend(codegen_function_call(child, auto_variables, end=';'))
            result.append('}')
        result.append('else {')
        for child in else_block:
            result.extend(codegen_function_call(child, auto_variables, end=';'))
        result.append('}')
    elif function_name == '@while':
        children = [data.objects[x] for x in data.children[element.element_id] if data.objects[x].type != ElementType.Comment]
        block = [
            child for child in children
            if subfunction_line('A1B37466') in child.lines  # conditional while, 71596144
            or subfunction_line('4945FAA8') in child.lines  # while-true, CEDAB9C3
        ]
        conditionals = [child for child in children if subfunction_line('20298AEC') in child.lines]
        if conditionals:
            conditional_expr = " && ".join(codegen_function_call(conditional, auto_variables)[0] for conditional in conditionals)
        else:
            conditional_expr = 'true'
        result.append(f'while ({conditional_expr}) {{')
        for element in block:
            result.extend(codegen_function_call(element, auto_variables, end=';'))
        result.append('}')
    else:
        result.append(function_name + '(' + ', '.join(codegen_parameter(param, auto_variables) for param in parameters) + ')' + end)

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


def codegen_function_def(data: TriggerObjects, element: TriggerElement, indent: int = 0) -> str:
    result: list[str] = []
    assert element.type == ElementType.FunctionDef
    parameters = [data.objects[child] for child in data.children[element.element_id] if data.objects[child].type == ElementType.ParamDef]
    functions = [data.objects[child] for child in data.children[element.element_id] if data.objects[child].type == ElementType.FunctionCall]
    variables = [data.objects[child] for child in data.children[element.element_id] if data.objects[child].type == ElementType.Variable]
    return_type = parse_return_type(element)


    def _print(string: str = '', this_indent: int|None = None) -> None:
        if this_indent is None:
            this_indent = indent
        result.append(('    ' * this_indent * (len(string) > 0)) + string)
    
    _print(
        f'{return_type} {function_name(data, element)} ('
        + (', '.join(f'{get_variable_type(parameter.lines)} {parameter_name(data.id_to_string[parameter.element_id])}' for parameter in parameters))
        + ') {'
    )
    indent += 1
    if variables:
        _print('// Variable Declarations')
    for variable in variables:
        variable_type = get_variable_type(variable.lines)
        _print(f'{variable_type} {local_variable_name(data, variable)};')
    if variables:
        _print()
    _print('// Automatic Variable Declarations')
    auto_var_insertion_point = len(result)
    automatic_variables = AutoVarBuilder([])
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
    indent -= 1
    if automatic_variables:
        result[auto_var_insertion_point:auto_var_insertion_point] = ['']
    result[auto_var_insertion_point:auto_var_insertion_point] = [f'    {x.var_type} {x.name};' for x in automatic_variables.data]
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


def codegen_trigger(data: TriggerObjects, trigger: TriggerElement) -> str:
    # Todo(mm): This is incomplete
    result: list[str] = []
    assert trigger.type == ElementType.Trigger
    variables = [data.objects[child] for child in data.children[trigger.element_id] if data.objects[child].type == ElementType.Variable]

    indent = 0
    def _print(string: str) -> None:
        result.append(('    ' * indent * (len(string) > 0)) + string)

    _print('//' + ('-' * 98))
    _print(f'// Trigger: {data.id_to_string[trigger.element_id]}')
    _print('//' + ('-' * 98))
    _print(f'bool lib{data.library}_gt_{data.id_to_string[trigger.element_id]}_Func (bool testConds, bool runActions) {{')
    indent += 1
    _print('// Variable Declarations')
    for variable in variables:
        variable_type = get_variable_type(variable.lines)
        _print(f'{variable_type} {local_variable_name(data, variable)};')
    result.append('')
    return '\n'.join(result)


def codegen_library(data: TriggerObjects) -> str:
    result: list[str] = []
    result.append('include "TriggerLibs/NativeLib"')
    for dependency_name in data.dependencies:
        dependency = repo_objects.libs_by_name[dependency_name]
        result.append(f'include "Lib{dependency.library}"')
    result.append('')
    result.append(f'include "Lib{data.library}_h"')
    result.append('')
    result.append('//' + ('-' * 98))
    result.append(f'// Library: {data.id_to_string[data.library]}')
    result.append('//' + ('-' * 98))
    result.append('// External Library Initialization')
    result.append('void libABFE498B_InitLibraries () {')
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
    for variable in data.objects.values():
        if (variable.type != ElementType.Variable
            or data.parent_element(variable).type not in (ElementType.Root, ElementType.Category)
        ):
            continue
        var_init = codegen_variable_init(variable)
        result.extend((' '* 4) + line for line in var_init)
    result.append('}')
    result.append('')

    custom_scripts = [
        x for x in data.objects.values()
        if x.type == ElementType.CustomScript
        and data.parent_element(x).type in (ElementType.Root, ElementType.Category)
    ]
    if custom_scripts:
        result.append('// Custom Script')
    for custom_script in custom_scripts:
        result.append('//' + ('-' * 98))
        result.append(f'// Custom Script: {data.id_to_string[custom_script.element_id]}')
        result.append('//' + ('-' * 98))
        custom_script_lines = codegen_custom_script(custom_script)
        result.extend(indent_lines(custom_script_lines)[1])
        result.append('')
    if custom_scripts:
        result.append(f'void lib{data.library}_InitCustomScript () {{')
        result.append('}')
        result.append('')

    result.append('// Functions')
    for element in data.objects.values():
        if element.type == ElementType.FunctionDef:
            result.append(codegen_function_def(data, element))
            result.append('')
    result.append('// Triggers')
    return '\n'.join(result)



if __name__ == '__main__':
    from scripts.at.interactive import interactive
    ap_triggers = repo_objects.libs_by_name['ArchipelagoTriggers']
    ap_player = repo_objects.libs_by_name['ArchipelagoPlayer']
    # print(codegen_function(triggers, triggers.objects['D8068F8E']))
    with open('aptriggers.log', 'w') as fp:
        print(codegen_library(ap_triggers), file=fp)
    with open('applayer.log', 'w') as fp:
        print(codegen_library(ap_player), file=fp)
    # interactive(triggers)
    # triggers.write_triggers('test.xml')

