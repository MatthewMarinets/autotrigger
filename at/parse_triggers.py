from typing import Self, TypeVar, overload
from .util import unescape_xml_string, fix_bom
import enum
import re
import os
import json
from collections import deque


with open(os.path.join(os.path.dirname(__file__), '..', 'config.json'), 'r') as fp:
    config = json.load(fp)


_T = TypeVar('_T')


AT_FOLDER = os.path.dirname(__file__)
AUTOTRIGGER_FOLDER = os.path.dirname(AT_FOLDER)
REPO_ROOT = os.path.normpath(os.path.dirname(AUTOTRIGGER_FOLDER))
MODS_FOLDER = f"{REPO_ROOT}/Mods"
GALAXY_FILE = f"{MODS_FOLDER}/ArchipelagoTriggers.SC2Mod/Base.SC2Data/LibABFE498B.galaxy"
TRIGGERS_FILE = f"{MODS_FOLDER}/ArchipelagoTriggers.SC2Mod/Triggers"
TRIGGER_STRINGS_FILE = f"{MODS_FOLDER}/ArchipelagoTriggers.SC2Mod/enUS.SC2Data/LocalizedData/TriggerStrings.txt"


_type_pattern = re.compile(r'Type="(\w+)"')
_id_pattern = re.compile(r'\bId="([0-9A-F]{8})"')
_type_lib_id_pattern = re.compile(r'Type="(\w+)" Library="(\w+)" Id="([0-9A-F]{8})"')


class ElementType(enum.StrEnum):
    Library = 'Library'
    Root = 'Root'
    Category = 'Category'
    Trigger = 'Trigger'
    FunctionCall = 'FunctionCall'
    FunctionDef = 'FunctionDef'
    Param = 'Param'
    ParamDef = 'ParamDef'
    SubFuncType = 'SubFuncType'
    Label = 'Label'
    Comment = 'Comment'
    Variable = 'Variable'
    CustomScript = 'CustomScript'
    Structure = 'Structure'
    Preset = 'Preset'
    PresetValue = 'PresetValue'


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
            m = re.search(_type_pattern, lines[0])
            assert m
            self.type = ElementType(m.group(1))
            m = re.search(_id_pattern, lines[0])
            assert m
            self.element_id = m.group(1)
            assert self.element_id

    def get_inline_value(self, tag: str) -> str|None:
        for line in self.lines:
            if line.startswith(f'<{tag}>'):
                return line[len(tag)+2:-(len(tag)+3)]
        return None

    @overload
    def get_multiline_value(self, tag: str) -> list[str]|None: ...
    @overload
    def get_multiline_value(self, tag: str, default: _T) -> list[str]|_T: ...
    def get_multiline_value(self, tag: str, default = None) -> list[str]|_T:
        start_tag = f'<{tag}>'
        end_tag = f'</{tag}>'
        if start_tag not in self.lines:
            return default
        if end_tag not in self.lines:
            raise ValueError(f'Unclosed tag in element {self}: {start_tag}')
        return [unescape_xml_string(x) for x in self.lines[self.lines.index(start_tag)+1:self.lines.index(end_tag)]]

    def get_attribute(self, tag: str, attribute: str) -> str|None:
        for line in self.lines:
            if line.startswith(f'<{tag}'):
                if m := re.search(rf'\b{attribute}="([^"]+)"', line):
                    return m.group(1)
        return None
    
    def get_first_line_of_tag(self, tag: str) -> str|None:
        for line in self.lines:
            if line.startswith(f'<{tag} '):
                return line
        return None

    def get_all_lines_of_tag(self, tag: str) -> list[str]:
        return [line for line in self.lines if line.startswith(f'<{tag}')]

    def __str__(self) -> str:
        return f'{self.type}(lib={self.library}, id={self.element_id})'
    def __repr__(self) -> str:
        return str(self)
    
    def __hash__(self) -> int:
        return hash((self.element_id, self.type, self.library))
    def __eq__(self, other) -> bool:
        return (
            self.element_id == other.element_id
            and self.type == other.type
            and self.library == other.library
        )


class TriggerLib:
    __slots__ = (
        'library',
        'name',
        'objects',
        'trigger_strings',
        'children',
        'parents',
        'dependencies',
        'keyword_parameters',
    )
    def __init__(self, name: str) -> None:
        self.library: str = ''
        self.name = name
        self.objects: dict[tuple[str, ElementType], TriggerElement] = {}
        self.trigger_strings: dict[str, str] = {}
        self.children: dict[TriggerElement, list[TriggerElement]] = {}
        self.parents: dict[TriggerElement, TriggerElement] = {}
        self.dependencies: list[str] = []
        self.keyword_parameters: dict[TriggerElement, dict[str, TriggerElement]] = {}

    def parent_element(self, element: TriggerElement) -> TriggerElement:
        return self.parents[element]
    
    def get_element(self, element_id: str, element_type: ElementType) -> TriggerElement:
        return self.objects[(element_id, element_type)]

    def parse(self, triggers_file: str = TRIGGERS_FILE, trigger_strings_file: str = TRIGGER_STRINGS_FILE) -> Self:
        self._parse_triggers(triggers_file)
        self._update_indices()
        self._update_keyword_parameter_indices()
        document_info_file = os.path.join(os.path.dirname(triggers_file), 'DocumentInfo')
        if os.path.isfile(document_info_file):
            self._parse_dependencies(document_info_file)
        self._parse_trigger_strings(trigger_strings_file)
        return self
    
    def sort_elements(self) -> None:
        sorted_objects = sort_elements(self)
        self.objects.clear()
        for obj in sorted_objects:
            self.objects[obj.element_id, obj.type] = obj
        self._update_indices()
    
    @overload
    def id_to_string(self, element_id: str, element_type: ElementType) -> str|None: ...
    @overload
    def id_to_string(self, element_id: str, element_type: ElementType, default: _T) -> str|_T: ...
    def id_to_string(self, element_id: str, element_type: ElementType, default = None) -> str|_T:
        if element_id == 'root':
            return 'Root'
        return self.trigger_strings.get(f'{element_type}/Name/lib_{self.library}_{element_id}', default)
    
    def root(self) -> TriggerElement:
        return self.objects['root', ElementType.Root]

    def _parse_triggers(self, triggers_file: str = TRIGGERS_FILE) -> None:
        with open(triggers_file, 'r') as fp:
            lines = fp.readlines()
        fix_bom(lines)
        current_obj: list[str]|None = None
        if len(lines) <= 3:
            self.library = 'nolibrary'
            self.objects['root', ElementType.Root] = TriggerElement(['<Root>', '</Root>'], self.library)
            return
        for line_number, line in enumerate(lines[2:], 3):
            line = line.strip()
            if not line:
                continue
            if line_number == 3:
                library_standard_pattern = re.compile(r'^<(?:Library|Standard) Id="([\w]+)"/?>$')
                m = library_standard_pattern.match(line)
                assert m is not None, f"Line 3 didn't have the library ID (file {triggers_file})"
                self.library = m.group(1)
            elif line in ('</Library>', '</TriggerData>'):
                continue
            elif line.startswith('<Element') or line == '<Root>':
                assert current_obj is None
                current_obj = [line]
            elif line in ('</Element>', '</Root>'):
                assert current_obj is not None
                current_obj.append(line)
                new_element = TriggerElement(current_obj, self.library)
                self.objects[new_element.element_id, new_element.type] = new_element
                current_obj = None
            else:
                assert current_obj is not None
                current_obj.append(line)

    def _parse_dependencies(self, document_info: str) -> None:
        with open(document_info, 'r') as fp:
            lines = fp.readlines()
        fix_bom(lines)
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
        self.trigger_strings.clear()
        if not os.path.exists(trigger_strings_file):
            return
        with open(trigger_strings_file, 'r') as fp:
            lines = fp.readlines()
        fix_bom(lines)
        for line in lines:
            if not line:
                continue
            key, val = line.strip().split('=', 1)
            self.trigger_strings[key] = val
            element_type = line.split('/', 1)[0]

    def _update_indices(self) -> None:
        self.children.clear()
        self.parents.clear()
        category_item_pattern = re.compile(rf'^<Item Type="(\w+)" Library="{self.library}" Id="([0-9A-F]{{8}})"/>$')
        for _, obj in self.objects.items():
            if obj.type in (ElementType.Root, ElementType.Category):
                self.children[obj] = []
                for line in obj.lines[1:-1]:
                    m = category_item_pattern.match(line)
                    if m is not None:
                        self.children[obj].append(self.objects[m.group(2), ElementType(m.group(1))])
            elif obj.type in (ElementType.Comment, ElementType.CustomScript):
                pass
            else:
                self.children[obj] = []
                for line in obj.lines[1:-1]:
                    if m := _type_lib_id_pattern.search(line):
                        if m.group(2) != self.library:
                            continue
                        child_id = m.group(3)
                        child_type = ElementType(m.group(1))
                        self.children[obj].append(self.objects[child_id, child_type])
        priorities = {
            ElementType.Category: 10,
            ElementType.Root: 10,
            ElementType.Preset: 8,
        }
        for parent, children in self.children.items():
            for child in children:
                if child not in self.parents:
                    self.parents[child] = parent
                elif priorities.get(parent.type, 1) > priorities.get(self.parents[child].type, 1):
                    self.parents[child] = parent
        root_element = self.objects['root', ElementType.Root]
        self.parents[root_element] = root_element

    def _update_keyword_parameter_indices(self) -> None:
        self.keyword_parameters.clear()
        for element in self.objects.values():
            if element.type != ElementType.FunctionDef:
                continue
            if '<ScriptCode>' not in element.lines:
                continue
            parameters = [child for child in self.children[element] if child.type == ElementType.ParamDef]
            assert element not in self.keyword_parameters
            self.keyword_parameters[element] = {parameter.get_inline_value('Identifier'): parameter for parameter in parameters}  # type: ignore
            assert None not in self.keyword_parameters[element]


class RepoObjects:
    __slots__ = (
        'libs', 'libs_by_name'
    )
    def __init__(self) -> None:
        mods = [
            'ArchipelagoTriggers',
            'ArchipelagoCore',
            'ArchipelagoPlayer',
            'ArchipelagoPatches',
            'ArchipelagoTradeSystem',
        ]
        libs = [TriggerLib('Native').parse(config['native'], config['native_triggerstrings'])] + [
            TriggerLib(name).parse(
                f'{MODS_FOLDER}/{name}.SC2Mod/Triggers',
                f'{MODS_FOLDER}/{name}.SC2Mod/enUS.SC2Data/LocalizedData/TriggerStrings.txt'
            )
            for name in mods
        ]
        self.libs = {
            lib.library: lib
            for lib in libs
        }
        self.libs_by_name = {lib.name: lib for lib in libs}
repo_objects = RepoObjects()


def get_referenced_element(line: str) -> tuple[TriggerLib, TriggerElement]:
    m = _type_lib_id_pattern.search(line)
    assert m, line
    _type, _lib, _id = m.groups()
    lib = repo_objects.libs[_lib]
    return lib, lib.objects[_id, ElementType(_type)]


def sort_elements(lib: TriggerLib) -> list[TriggerElement]:
    child_order: dict[TriggerElement, int] = {}
    root_element = lib.objects['root', ElementType.Root]
    search_stack = deque([root_element])
    while search_stack:
        new_node = search_stack.pop()
        if new_node not in child_order:
            child_order[new_node] = len(child_order)
            children = lib.children.get(new_node, [])
            child_filter: list[ElementType] = []
            if new_node.type not in (ElementType.Category, ElementType.Root):
                child_filter.extend([ElementType.Trigger, ElementType.FunctionDef, ElementType.CustomScript])
            if new_node.type != ElementType.FunctionDef:
                child_filter.append(ElementType.ParamDef)
            if new_node.type == ElementType.Param:
                child_filter.append(ElementType.Variable)
            if child_filter:
                children = [
                    child for child in children
                    if child.type not in child_filter
                ]
            search_stack.extend(reversed(children))

    child_order[root_element] = -1
    return sorted(lib.objects.values(), key=lambda x: child_order[x])
