from hashlib import sha1
from typing import Optional, Union, Literal, Tuple

from ..config_types import ScriptSetting, ConcreteScript, ScriptInsertion, ScriptPosition, Fmt
from ..utils import version

from ..lib.registrar import get_interface

from .condition_parser import get_condition_parser, stringify_conds

def wrap_code(code, conditions: Union[bool, list]):
    if ((type(conditions) is bool) and conditions) or len(conditions) == 0:
        return code

    else:
        main_code = '\n'.join([f'    {line}' for line in code.split('\n')])
        return f'if ({stringify_conds(conditions)}) {{\n{main_code}\n}}'

def indent(line, indentation):
    return indentation + line if len(line) > 0 else line

def indent_lines(text: str, indent_size: int) -> str:
    return '\n'.join([
        indent(line, indent_size * ' ')
        for line
        in text.split('\n')
    ])

def stringify_script_data(sd, indent_size: int, in_html: bool) -> str:
    srcTag = f" src=\"{sd['src']}\"" if 'src' in sd else ''

    opening, closing = (
        f'<script {sd["tag"]}{srcTag}>',
        '</script>',
    ) if in_html else (
        f'// {sd["tag"]}',
        '',
    )

    wrapped_code = wrap_code(sd["code"], sd["conditions"])
    indented_code = indent_lines(wrapped_code, indent_size if in_html else 0)

    # avoid two empty new lines for external scripts
    opening, indented_code = (
        f'{opening}\n',
        f'{indented_code}\n',
    ) if len(indented_code) > 0 else (
        opening,
        ''
    )

    return (
        opening +
        indented_code +
        closing
    )

def encapsulate_scripts(scripts, version, indent_size) -> str:
    pretext = "<div id=\"anki-am\" data-name=\"Assets by ASSET MANAGER\""
    version_text = f" data-version=\"{version}\"" if len(version) > 0 else ''

    top_delim = f"{pretext}{version_text}>"
    bottom_delim = '</div>'

    indented_scripts = [
        indent_lines(scc, indent_size)
        for scc in scripts
    ]
    combined = [
        item
        for sublist
        in [[top_delim], indented_scripts, [bottom_delim]]
        for item
        in sublist
    ]

    return '\n'.join(combined)

def gen_data_attributes(name: str, version: str):
    return f'data-name="{name}" data-version="{version}"'


def position_does_not_match(script, position) -> bool:
    return script.position != position and not (
        script.position in ['into_template', 'external'] and
        position in ['question', 'answer']
    )

def get_script_and_code(script, model_name, cardtype_name, position) -> Tuple[ConcreteScript, str]:
    script
    if isinstance(script, ConcreteScript):
        return (script, script.code)
    else:

        iface = get_interface(script.tag)

        return (
            iface.getter(
                script.id,
                script.storage,
            ),
            iface.generator(
                script.id,
                script.storage,
                model_name,
                cardtype_name,
                position,
            ),
        )

def package(tag: str, code: str, conditions_simplified: list, indent_size: int) -> str:
    sd = {
        'tag': tag,
        'code': code,
        'conditions': conditions_simplified,
    }

    return stringify_script_data(sd, indent_size, True)

def package_for_external(tag: str, filename: str, indent_size: int) -> Tuple[str, str]:
    sd = {
        'tag': tag,
        'src': filename,
        # no code or conditions, as they are present in external file
        'code': '',
        'conditions': [],
    }

    return ((filename, stringify_script_data(sd, indent_size, False)))

def stringify_setting(
    setting: ScriptSetting,
    model_name: str,
    model_id: int,
    cardtype_name: str,
    position: ScriptInsertion,
) -> str:
    the_parser = get_condition_parser(cardtype_name, position)
    script_data = []

    if not setting.enabled or setting.insert_stub:
        return script_data

    for script, code in map(lambda s: get_script_and_code(s, model_name, cardtype_name, position), setting.scripts):
        if (
            not script.enabled or
            len(code) == 0 or
            position_does_not_match(script, position)
        ):
            continue

        needs_inject, conditions_simplified = the_parser(script.conditions)

        if not needs_inject:
            continue

        tag = gen_data_attributes(
            script.name,
            script.version,
        )

        if script.position == 'external' and position in ['question', 'answer']:
            filename = f'_am_{model_id}_{sha1(script.name.encode()).hexdigest()}.js'
            script_data.append(package_for_external(tag, filename, setting.indent_size))
        else:
            script_data.append(package(tag, code, conditions_simplified, setting.indent_size))

    return script_data
