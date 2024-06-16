
import sys
from autotrigger import ElementType, TriggerElement, TriggerLib, codegen_trigger


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
    print('gen - generate the galaxy code for a trigger')
    print('cd - change directory')
    print('ls - print current object info')
    print('help')
    print('exit')


def element_abspath(element: TriggerElement, data: TriggerLib) -> str:
    result: list[str] = []
    while element.element_id != 'root':
        result.append(data.id_to_string.get(element.element_id, element.element_id))
        element = data.objects[data.parents[element.element_id]]
    result.append('Root')
    return '/'.join(reversed(result))


def path_to_obj(path: str, start: TriggerElement, data: TriggerLib) -> tuple[str, TriggerElement]:
    if not path:
        return ('No path provided', start)
    current = start
    if path.startswith('/'):
        current = data.objects['root']
        path = path[1:]
    parts = path.split('/')
    for part in parts:
        if part == '.' or not part:
            continue
        if part == '..':
            current = data.objects[data.parents[current.element_id]]
            continue
        if part.upper() in data.objects:
            current = data.objects[part.upper()]
            continue
        candidates = [
            x for x in data.children[current.element_id]
            if data.id_to_string.get(x, '').casefold() == part.casefold()
        ]
        if candidates:
            current = data.objects[candidates[0]]
        else:
            return (f'Unknown name "{part}" in directory {element_abspath(current, data)}', start)
    return ('', current)        


def interactive(data: TriggerLib) -> None:

    running = True
    current_id = 'root'
    print('Started interactive trigger console')
    while running:
        element: TriggerElement = data.objects[current_id]
        sys.stdout.write(f'{_console_code(ConsoleColours.BRIGHT_MAGENTA)}{element_abspath(element, data)}{_console_code()} $ ')
        sys.stdout.flush()
        command = input().split()
        if not command:
            continue
        elif command[0] == 'help':
            print_help()
        elif command[0] == 'exit':
            running = False
        elif command[0] == 'ls':
            print(f'Contents of {data.id_to_string.get(element.element_id, "Unnamed")} ({element.element_id})')
            print(f'Parent: {data.objects[data.parents[element.element_id]].display_string(data.id_to_string)}')
            for child in data.children[element.element_id]:
                print(data.objects[child].display_string(data.id_to_string))
        elif command[0] == 'cd':
            if len(command) < 2:
                print('cd takes an argument')
                continue
            error_msg, element = path_to_obj(command[1], element, data)
            if error_msg:
                print(error_msg)
            else:
                current_id = element.element_id
        elif command[0] == 'print':
            print(f'{data.id_to_string.get(element.element_id, "Unnamed")}')
            indent_level = 0
            for line in element.lines:
                this_indent_level, indent_level = data.get_indentation(line, indent_level)
                print(('   ' * this_indent_level) + line)
        elif command[0] == 'gen':
            if element.type == ElementType.Trigger:
                print(codegen_trigger(data, element))
            else:
                print(f'{data.id_to_string.get(element.element_id, element.element_id)} is not a trigger')
        else:
            print(f'Unknown command: {command[0]}')


