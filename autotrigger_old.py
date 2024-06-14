"""
Script for modifying `Trigger` files with unlock triggers,
so we can update GUI triggers without having to put up with the editor.
"""

import os
from typing import NamedTuple
import random
import re

SCRIPTS_FOLDER = os.path.dirname(__file__)
REPO_ROOT = os.path.normpath(os.path.dirname(SCRIPTS_FOLDER))
GALAXY_FILE = f"{REPO_ROOT}/Mods/ArchipelagoTriggers.SC2Mod/Base.SC2Data/LibABFE498B.galaxy"
TRIGGERS_FILE = f"{REPO_ROOT}/Mods/ArchipelagoTriggers.SC2Mod/Triggers"
TRIGGER_STRINGS_FILE = f"{REPO_ROOT}/Mods/ArchipelagoTriggers.SC2Mod/enUS.SC2Data/LocalizedData/TriggerStrings.txt"


class FreeIds(NamedTuple):
    function_id: str
    player_parameter: str
    function_call: str
    default_player_param: str
    set_upgrade_param_1: str
    set_upgrade_param_2: str
    set_upgrade_param_3: str
    # category_id: str


def trigger_template(upgrade_name: str, available_ids: FreeIds) -> str:
    function_id = available_ids.function_id
    player_parameter_id = available_ids.player_parameter
    function_call_id = available_ids.function_call
    default_player_param_id = available_ids.default_player_param
    set_upgrade_param_1_id = available_ids.set_upgrade_param_1
    set_upgrade_param_2_id = available_ids.set_upgrade_param_2
    set_upgrade_param_3_id = available_ids.set_upgrade_param_3
    return f'''        <Element Type="FunctionDef" Id="{function_id}">
            <FlagAction/>
            <Parameter Type="ParamDef" Library="ABFE498B" Id="{player_parameter_id}"/>
            <FunctionCall Type="FunctionCall" Library="ABFE498B" Id="{function_call_id}"/>
        </Element>
        <Element Type="ParamDef" Id="{player_parameter_id}">
            <ParameterType>
                <Type Value="int"/>
            </ParameterType>
            <Default Type="Param" Library="ABFE498B" Id="{default_player_param_id}"/>
        </Element>
        <Element Type="Param" Id="{default_player_param_id}">
            <Value>0</Value>
            <ValueType Type="int"/>
        </Element>
        <Element Type="FunctionCall" Id="{function_call_id}">
            <FunctionDef Type="FunctionDef" Library="Ntve" Id="9F8EF8FB"/>
            <Parameter Type="Param" Library="ABFE498B" Id="{set_upgrade_param_1_id}"/>
            <Parameter Type="Param" Library="ABFE498B" Id="{set_upgrade_param_2_id}"/>
            <Parameter Type="Param" Library="ABFE498B" Id="{set_upgrade_param_3_id}"/>
        </Element>
        <Element Type="Param" Id="{set_upgrade_param_1_id}">
            <ParameterDef Type="ParamDef" Library="Ntve" Id="C7188352"/>
            <Parameter Type="ParamDef" Library="ABFE498B" Id="{player_parameter_id}"/>
        </Element>
        <Element Type="Param" Id="{set_upgrade_param_2_id}">
            <ParameterDef Type="ParamDef" Library="Ntve" Id="3BFEECBB"/>
            <Value>1</Value>
            <ValueType Type="int"/>
        </Element>
        <Element Type="Param" Id="{set_upgrade_param_3_id}">
            <ParameterDef Type="ParamDef" Library="Ntve" Id="7E5035EE"/>
            <Value>{upgrade_name}</Value>
            <ValueType Type="gamelink"/>
            <ValueGameType Type="Upgrade"/>
        </Element>'''


def code_template(upgrade_name: str, function_name: str) -> str:
    return f'''void libABFE498B_gf_{function_name} (int lp_player) {{
    // Automatic Variable Declarations
    // Implementation
    libNtve_gf_SetUpgradeLevelForPlayer(lp_player, "{upgrade_name}", 1);
}}'''


def trigger_strings_template(ids: FreeIds, function_name: str) -> list[str]:
    return [
        f"FunctionDef/Name/lib_ABFE498B_{ids.function_id}={function_name}",
        f"ParamDef/Name/lib_ABFE498B_{ids.player_parameter}=player",
    ]


def category_template(ids: FreeIds) -> str:
    return f'            <Item Type="FunctionDef" Library="ABFE498B" Id="{ids.function_id}"/>'


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


def generate_ids(triggers_contents: str) -> FreeIds:
    result: list[str] = []
    while len(result) < len(FreeIds._fields):
        candidate = hex(random.randint(0x1000_0000, 0xffff_ffff))[2:].upper()
        if candidate not in triggers_contents:
            assert len(candidate) == 8
            result.append(candidate)
    return FreeIds._make(result)


class CategorizedElement(NamedTuple):
    element_id_chain: list[str]
    element_type: str


def parse_categories(triggers_contents: str) -> tuple[list[CategorizedElement], dict[str, int]]:
    category_start_pattern = re.compile(r'^\s*<Element Type="(\w+)" Id="([A-F0-9]{8})">')
    category_element_pattern = re.compile(r'^\s*<Item Type="(\w+)" Library="ABFE498B" Id="([A-F0-9]{8})"/>')
    category_end_pattern = re.compile(r'^\s*</Element>')
    
    result: list[CategorizedElement] = []
    child_to_parent: dict[str, str] = {}
    element_id_to_line_number: dict[str, int] = {}

    def assemble_heritage(child_id: str) -> list[str]:
        current = child_id
        result: list[str] = []
        while current != 'Root':
            result.append(current)
            current = child_to_parent[current]
        return result[::-1]

    lines = triggers_contents.split('\n')
    in_category = ''
    for line_number, line in enumerate(lines, 1):
        if m := re.match(category_start_pattern, line):
            assert not in_category
            element_id_to_line_number[m.group(2)] = line_number
            if m.group(1) == 'Category':
                in_category = m.group(2)
        elif '<Root>' in line:
            assert not in_category
            in_category = 'Root'
        elif m := re.match(category_element_pattern, line):
            assert in_category
            child_to_parent[m.group(2)] = in_category
            result.append(CategorizedElement(assemble_heritage(m.group(2)), m.group(1)))
        elif m := re.match(category_end_pattern, line):
            assert in_category != 'Root'
            in_category = ''
        elif '</Root>' in line:
            assert in_category == 'Root'
            in_category = ''
    return result, element_id_to_line_number
        


class Splicer:
    __slots__ = (
        'triggers_content',
        'trigger_strings',
        'galaxy_contents',
        'category_items',
        'element_id_to_line_number',
        'category_id_to_name',
        'id_to_name',
        'category_name_map',
    )
    def __init__(self) -> None:
        with open(TRIGGERS_FILE, 'r') as fp:
            self.triggers_content = fp.read()
        with open(TRIGGER_STRINGS_FILE, 'r', encoding='utf-8-sig') as fp:
            self.trigger_strings = fp.readlines()
        with open(GALAXY_FILE, 'r') as fp:
            self.galaxy_contents = fp.read()
        self.category_items, self.element_id_to_line_number = parse_categories(self.triggers_content)
        category_names, other_names = find_element_names(self.trigger_strings)
        self.category_id_to_name = dict(category_names)
        self.id_to_name = dict(other_names)
        # @assumption: triggers always go at the end of the .galaxy file; we don't need their strings

        # construct a map from the fully-qualified category to an ID
        self.category_name_map: dict[str, str] = {}
        for category_item in self.category_items:
            if category_item.element_type != 'Category':
                continue
            self.category_name_map['/'.join(self.category_id_to_name[x] for x in category_item.element_id_chain)] = (
                category_item.element_id_chain[-1]
            )

    def splice(self, upgrade_name: str, function_name: str, category: str) -> None:
        assert category in self.category_name_map
        category_id = self.category_name_map[category]
        category_members = [x for x in self.category_items if len(x.element_id_chain) > 1 and x.element_id_chain[-2] == category_id]
        available_ids = generate_ids(self.triggers_content)
        category_content = category_template(available_ids)
        trigger_content = trigger_template(upgrade_name, available_ids)
        code_content = code_template(upgrade_name, function_name)
        # self.trigger_strings.extend(trigger_strings_template(available_ids, function_name))
        # todo: actually splice in triggers, code, and categories

    def print_children(self, category: str) -> None:
        print(f"Category {category}:")
        assert category in self.category_name_map, f"Unknown category {category!r}"
        category_id = self.category_name_map[category]
        children = [x for x in self.category_items if len(x.element_id_chain) > 1 and x.element_id_chain[-2] == category_id]
        for child in children:
            print(
                f"  {self.id_to_name[child.element_id_chain[-1]]}:"
                f" {child.element_type} ({child.element_id_chain[-1]})"
                f" {TRIGGERS_FILE}#{self.element_id_to_line_number[child.element_id_chain[-1]]}"
            )
    
    def write(self) -> None:
        with open(TRIGGERS_FILE, 'w') as fp:
            fp.write(self.triggers_content)
        with open(TRIGGER_STRINGS_FILE, 'w', encoding='utf-8-sig') as fp:
            fp.writelines(sorted(self.trigger_strings))
        with open(GALAXY_FILE, 'w') as fp:
            fp.write(self.galaxy_contents)


if __name__ == '__main__':
    splicer = Splicer()
    splicer.print_children("TechTree/Zerg/Unlocks/UnitUpgrades")
    # splicer.splice("AP_K5GasBonuses", "AP_Triggers_Zerg_VespeneEfficiency")
    splicer.write()
