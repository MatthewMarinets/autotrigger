
import sys
from .. import autotrigger as at


class ConsoleColours:
    RESET = 0
    BOLD = 1
    UNDERLINE = 4
    # Add 10 to turn a colour into a background colour
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    GREY = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97


enable_colours = True
def _console_code(*modifiers: int, background: int|None = None) -> str:
    if not enable_colours:
        return ''
    if not modifiers:
        modifier_ids = [ConsoleColours.RESET]
    else:
        modifier_ids = [modifier for modifier in modifiers]
    if background is not None:
        modifier_ids.append(background + 10)
    return f"\x1b[{';'.join(map(str, modifier_ids))}m"


def print_help() -> None:
    print('cd - change directory')
    print('ls - print current object info')
    print('gen - generate the galaxy code for the element')
    print('xml - display the xml lines for the elemnt')
    print('help')
    print('exit')


def element_name(lib: at.TriggerLib, element: at.TriggerElement) -> str:
    return lib.id_to_string(element.element_id, element.type, 'Unnamed') + ('/' if element.type == at.ElementType.Category else '')


def element_abspath(element: at.TriggerElement, data: at.TriggerLib) -> str:
    result: list[str] = []
    while element.type != at.ElementType.Root:
        result.append(data.id_to_string(element.element_id, element.type, str(element)))
        element = data.parents[element]
    return '/' + '/'.join(reversed(result))


def path_to_obj(path: str, start: at.TriggerElement, data: at.TriggerLib) -> tuple[str, at.TriggerElement]:
    if not path:
        return ('No path provided', start)
    current = start
    if path.startswith('/'):
        current = data.objects[('root', at.ElementType.Root)]
        path = path[1:]
    parts = path.split('/')
    for part in parts:
        if part == '.' or not part:
            continue
        if part == '..':
            current = data.parents[current]
            continue
        if (part_id := (part[-8:].upper(), part[:-8])) in data.objects:
            current = data.objects[part_id[0], at.ElementType(part_id[1])]
            continue
        candidates = [
            x for x in data.children[current]
            if data.id_to_string(x.element_id, x.type, '').casefold() == part.casefold()
        ]
        if candidates:
            current = candidates[0]
            continue
        if part.isnumeric() or part[:1] == '-' and part[1:].isnumeric():
            index = int(part)
            if index >= len(data.children[current]) or index < -len(data.children[current]):
                return (f'index {index} is out of bounds for {element_abspath(current, data)} ({len(data.children[current])} children)', start)
            current = data.children[current][index]
            continue
        else:
            return (f'Unknown name "{part}" in directory {element_abspath(current, data)}', start)
    return ('', current)        


def interactive(repo: at.RepoObjects) -> None:

    running = True
    lib = repo.libs_by_name['ArchipelagoTriggers']
    DEFAULT_ID = ('root', at.ElementType.Root)
    current_id = DEFAULT_ID
    print('Started interactive trigger console')
    while running:
        element: at.TriggerElement = lib.objects[current_id]
        sys.stdout.write(f'{_console_code(ConsoleColours.BRIGHT_MAGENTA)}{element_abspath(element, lib)}{_console_code()} $ ')
        sys.stdout.flush()
        command = input().split()
        if not command:
            continue
        elif command[0] == 'help':
            print_help()
        elif command[0] == 'exit':
            running = False
        elif command[0] == 'ls':
            if len(command) > 2:
                print(f'ls takes up to 1 argument, {len(command) - 1} given')
                continue
            elif len(command) == 2:
                error_msg, search_element = path_to_obj(command[1], element, lib)
                if error_msg:
                    print(error_msg)
                    continue
            else:
                search_element = element
            print(f'Contents of {element_name(lib, search_element)} ({search_element})')
            parent = lib.parents[search_element]
            child_names = [(element_name(lib, child), child) for child in lib.children.get(search_element, [])]
            name_width = max((len(name[0]) for name in child_names), default=1) + 2
            print(f'.. {" ":{name_width}} ({parent})')
            for child_index, (child_name, child) in enumerate(child_names):
                print(f'{child_index:>2} {child_name:<{name_width}} ({child})')
        elif command[0] == 'cd':
            if len(command) < 2:
                print('cd takes an argument')
                continue
            error_msg, element = path_to_obj(command[1], element, lib)
            if error_msg:
                print(error_msg)
            else:
                current_id = element.element_id, element.type
        elif command[0] == 'xml':
            print(element_name(lib, element))
            indent_level = 0
            for line in element.lines:
                this_indent_level, indent_level = at.get_indentation(line, indent_level)
                print(('   ' * this_indent_level) + line)
        elif command[0] == 'gen':
            if element.type == at.ElementType.Trigger:
                print('===triggers are WIP===')
                print(at.codegen_trigger(lib, element))
            elif element.type == at.ElementType.FunctionDef:
                print(at.codegen_function_def(lib, element))
            elif element.type == at.ElementType.FunctionCall:
                lines = at.codegen_function_call(element, at.AutoVarBuilder([]))
                indent = 0
                for line in lines:
                    this_indent, indent = at.get_indentation(line, indent)
                    print(('    ' * this_indent) + line)
            elif element.type == at.ElementType.Variable:
                for line in at.codegen_variable_init(element):
                    print(line)
            elif element.type == at.ElementType.Param:
                print(at.codegen_parameter(element, at.AutoVarBuilder([])))
            elif element.type == at.ElementType.PresetValue:
                print(at.preset_value(lib, element))
            else:
                print(f'Unable to codegen type of {element_name(lib, element)} ({element})')
        elif command[0] == 'add':
            print('Not implemented')
        else:
            print(f'Unknown command: {command[0]}')


