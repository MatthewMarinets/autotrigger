from typing import Callable, Protocol
from .. import autotrigger as at
from ..autotrigger import ElementType
import random
import re

class Error:
    def __init__(self, msg: str) -> None:
        self.msg = msg


class add_func(Protocol):
    def __call__(self, lib: at.TriggerLib, parent: at.TriggerElement, index: int, *args, **kwargs) -> Error|None: ...


def random_id(lib: at.TriggerLib, element_type: ElementType) -> str:
    result = random.randint(100, 0xffff_ffff)
    result_string = hex(result)[2:].upper()
    result_string = ('0' * (8 - len(result_string))) + result_string
    assert (result_string, element_type) not in lib.objects
    return result_string


def add_element(lib: at.TriggerLib, element: at.TriggerElement, parent: at.TriggerElement, index: int = -1, tag_name: str = '') -> None:
    lib.objects[element.element_id, element.type] = element
    lib.parents[element] = parent
    lib.children[element] = []

    if index < 0:
        # The +1 makes this go _after_ the specified element rather than before
        # so index = -1 actually puts things at the end
        index += len(lib.children[parent]) + 1
    if index < 0:
        index = 0
    lib.children[parent][index:index] = [element]
    if not tag_name:
        return
    child_pattern = re.compile(r'^\s*<\w+ Type="\w+" Library="(\w+)" Id="([0-9A-F]{8})"/>')
    children_encountered = 0
    for line_number, line in enumerate(parent.lines[:-1], start=1):
        if (m := child_pattern.match(line)) and m.group(1) == lib.library:
            children_encountered += 1
        if children_encountered >= index:
            break
    parent.lines[line_number:line_number] = [f'<{tag_name} Type="{element.type}" Library="{lib.library}" Id="{element.element_id}"/>']


def add_unlock_functiondef(
    lib: at.TriggerLib,
    parent: at.TriggerElement,
    index: int,
    name: str,
) -> Error|None:
    if parent.type not in (ElementType.Root, ElementType.Category):
        return Error('Attempted to add a function def to a non-category')
    function_def_id = random_id(lib, ElementType.FunctionDef)
    param_def_id = random_id(lib, ElementType.ParamDef)
    default_param_id = random_id(lib, ElementType.Param)

    function_def = at.TriggerElement([
        f'<Element Type="{ElementType.FunctionDef}" Id="{function_def_id}">',
        f'<Identifier>{name}</Identifier>',
        # f'<FlagAction/>',  # Not sure if this matters?
        f'<Parameter Type="ParamDef" Library="{lib.library}" Id="{param_def_id}"/>',
        f'</Element>',
    ], lib.library)
    lib.trigger_strings[f'{ElementType.FunctionDef}/Name/lib_{lib.library}_{function_def_id}'] = name
    add_element(lib, function_def, parent, index, 'Item')

    param_def = at.TriggerElement([
        f'<Element Type="ParamDef" Id="{param_def_id}">',
        f'<ParameterType>',
        f'<Type Value="int"/>',
        f'</ParameterType>',
        f'<Default Type="Param" Library="{lib.library}" Id="{default_param_id}"/>',
        f'</Element>',
    ], lib.library)
    lib.trigger_strings[f'{ElementType.ParamDef}/Name/lib_{lib.library}_{param_def_id}'] = 'player'
    add_element(lib, param_def, function_def)

    default_param = at.TriggerElement([
        f'<Element Type="Param" Id="{default_param_id}">',
        f'<Value>0</Value>',
        f'<ValueType Type="int"/>',
        f'</Element>',
    ], lib.library)
    add_element(lib, default_param, param_def)
    return None


def add_set_upgrade_level_function_call(
    lib: at.TriggerLib,
    parent: at.TriggerElement,
    index: int,
    upgrade_name: str,
) -> Error|None:
    if parent.type != ElementType.FunctionDef:
        return Error('Must add function calls to function defs')
    function_call_id = random_id(lib, ElementType.FunctionCall)
    function_arg_1_id = random_id(lib, ElementType.Param)
    function_arg_3_id = random_id(lib, ElementType.Param)
    function_arg_2_id = random_id(lib, ElementType.Param)

    lp_player_elements = [child for child in lib.children[parent] if child.type == ElementType.ParamDef]
    if len(lp_player_elements) != 1:
        return Error(f"Current FunctionDef doesn't have one parameter (got {len(lp_player_elements)} parameters)")
    lp_player_id = lp_player_elements[0].element_id  # FFC5A20B

    # libNtve_gf_SetUpgradeLevelForPlayer
    function_call = at.TriggerElement([
        f'<Element Type="FunctionCall" Id="{function_call_id}">',
        f'<FunctionDef Type="FunctionDef" Library="Ntve" Id="9F8EF8FB"/>',
        f'<Parameter Type="Param" Library="{lib.library}" Id="{function_arg_1_id}"/>',
        f'<Parameter Type="Param" Library="{lib.library}" Id="{function_arg_2_id}"/>',
        f'<Parameter Type="Param" Library="{lib.library}" Id="{function_arg_3_id}"/>',
        f'</Element>',
    ], lib.library)
    add_element(lib, function_call, parent, index, ElementType.FunctionCall)

    # arg 1: lp_player
    arg_1 = at.TriggerElement([
        f'<Element Type="Param" Id="{function_arg_1_id}">',
        f'<ParameterDef Type="ParamDef" Library="Ntve" Id="C7188352"/>',
        f'<Parameter Type="ParamDef" Library="ABFE498B" Id="{lp_player_id}"/>',
        f'</Element>',
    ], lib.library)
    add_element(lib, arg_1, function_call)

    # arg 2: upgrade name
    arg_2 = at.TriggerElement([
        f'<Element Type="Param" Id="{function_arg_2_id}">',
        f'<ParameterDef Type="ParamDef" Library="Ntve" Id="7E5035EE"/>',
        f'<Value>{upgrade_name}</Value>',
        f'<ValueType Type="gamelink"/>',
        f'<ValueGameType Type="Upgrade"/>',
        f'</Element>',
    ], lib.library)
    add_element(lib, arg_2, function_call)

    # arg 3: 1 (upgrade level)
    arg_3 = at.TriggerElement([
        f'<Element Type="Param" Id="{function_arg_3_id}">',
        f'<ParameterDef Type="ParamDef" Library="Ntve" Id="3BFEECBB"/>',
        f'<Value>1</Value>',
        f'<ValueType Type="int"/>',
        f'</Element>',
    ], lib.library)
    add_element(lib, arg_3, function_call)
    return None


def add_unit_lock_func(
    lib: at.TriggerLib,
    parent: at.TriggerElement,
    index: int,
    tech_tree_name: str,
    lock: bool = False,
) -> Error|None:
    if parent.type != ElementType.FunctionDef:
        return Error(f'Attempted to add unit lock function to non-function def ({parent.type})')
    # /TechTree/Terran/AP_Triggers_clearTerranTech: FunctionDef(lib=ABFE498B, id=CCD6216D)
    # /TechTree/Terran/AP_Triggers_clearZergTech: FunctionDef(lib=ABFE498B, id=D1655E1B)
    # /TechTree/Terran/AP_Triggers_clearProtossTech: FunctionDef(lib=ABFE498B, id=5C629511)
    function_call_id = random_id(lib, ElementType.FunctionCall)  # C765194F
    player_param_id = random_id(lib, ElementType.Param)  # F2BAECA6
    unit_param_id = random_id(lib, ElementType.Param)  # AE7EA2A8
    allow_param_id = random_id(lib, ElementType.Param)  # F29D4EAA

    lp_player_elements = [child for child in lib.children[parent] if child.type == ElementType.ParamDef]
    if len(lp_player_elements) != 1:
        return Error(f"Current FunctionDef doesn't have one parameter (got {len(lp_player_elements)} parameters)")
    lp_player_id = lp_player_elements[0].element_id  # FFC5A20B
    
    # TechTreeUnitAllow
    function_call = at.TriggerElement([
        f'<Element Type="FunctionCall" Id="{function_call_id}">',
        f'<FunctionDef Type="FunctionDef" Library="Ntve" Id="51A273F5"/>',
        f'<Parameter Type="Param" Library="{lib.library}" Id="{player_param_id}"/>',
        f'<Parameter Type="Param" Library="{lib.library}" Id="{unit_param_id}"/>',
        f'<Parameter Type="Param" Library="{lib.library}" Id="{allow_param_id}"/>',
        f'</Element>',
    ], lib.library)
    add_element(lib, function_call, parent, index, tag_name=ElementType.FunctionCall)

    player_param = at.TriggerElement([
        f'<Element Type="Param" Id="{player_param_id}">',
        f'<ParameterDef Type="ParamDef" Library="Ntve" Id="B15D29C1"/>',
        f'<Parameter Type="ParamDef" Library="{lib.library}" Id="{lp_player_id}"/>',
        f'</Element>',
    ], lib.library)
    add_element(lib, player_param, function_call)

    unit_param = at.TriggerElement([
        f'<Element Type="Param" Id="{unit_param_id}">',
        f'<ParameterDef Type="ParamDef" Library="Ntve" Id="BC66D9AD"/>',
        f'<Value>{tech_tree_name}</Value>',
        f'<ValueType Type="gamelink"/>',
        f'<ValueGameType Type="Unit"/>',
        f'</Element>',
    ], lib.library)
    add_element(lib, unit_param, function_call)

    if lock:
        preset_id = '00000106'
    else:
        preset_id = '00000107'
    allow_param = at.TriggerElement([
        f'<Element Type="Param" Id="{allow_param_id}">',
        f'<ParameterDef Type="ParamDef" Library="Ntve" Id="C26556EA"/>',
        f'<Preset Type="PresetValue" Library="Ntve" Id="{preset_id}"/>',
        f'</Element>',
    ], lib.library)
    add_element(lib, allow_param, function_call)
    return None


def parse_bool(val: str) -> bool:
    if val.lower() in ('false', 'f'):
        return False
    elif val.lower() in ('true', 't'):
        return True
    raise ValueError('Invalid bool literal')


ADD_FUNCS: dict[str, tuple[add_func, list[str], dict[int, Callable]]] = {
    'unlock_fn': (add_unlock_functiondef, ['index', 'name'], {0: int}),
    'upgrade': (add_set_upgrade_level_function_call, ['index', 'upgrade_name'], {0: int}),
    'unit': (add_unit_lock_func, ['index', 'tech_tree_name', 'lock'], {0: int, 2: parse_bool}),
}
