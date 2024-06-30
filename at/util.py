
def unescape_xml_string(string: str) -> str:
    return (
        string
        .replace('&quot;', '"')
        .replace('&apos;', "'")
        .replace('&lt;', '<')
        .replace('&gt;', '>')
        .replace('&amp;', '&')
    )


def fix_bom(lines: list[str]) -> None:
    if lines and lines[0].startswith('ï»¿'):
        lines[0] = lines[0][len('ï»¿'):]
