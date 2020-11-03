"""Used by the make system to generate info_config.h from info.json.
"""
from milc import cli

from qmk.decorators import automagic_keyboard, automagic_keymap
from qmk.info import info_json
from qmk.path import is_keyboard, normpath

usb_properties = {
    'vid': 'VENDOR_ID',
    'pid': 'PRODUCT_ID',
    'device_ver': 'DEVICE_VER',
}


def diode_direction(diode_direction):
    """Return the config.h lines that set diode direction
    """
    return """
#ifndef DIODE_DIRECTION
#   define DIODE_DIRECTION %s
#endif // DIODE_DIRECTION
""" % diode_direction


def keyboard_name(keyboard_name):
    """Return the config.h lines that set the keyboard's name.
    """
    return """
#ifndef DESCRIPTION
#    define DESCRIPTION %s
#endif // DESCRIPTION

#ifndef PRODUCT
#    define PRODUCT %s
#endif // PRODUCT
""" % (keyboard_name, keyboard_name)


def manufacturer(manufacturer):
    """Return the config.h lines that set the manufacturer.
    """
    return """
#ifndef MANUFACTURER
#    define MANUFACTURER %s
#endif // MANUFACTURER
""" % (manufacturer)


def direct_pins(direct_pins):
    """Return the config.h lines that set the direct pins.
    """
    rows = []

    for row in direct_pins:
        cols = ','.join([col or 'NO_PIN' for col in row])
        rows.append('{' + cols + '}')

    col_count = len(direct_pins[0])
    row_count = len(direct_pins)

    return """
#ifndef MATRIX_COLS
#    define MATRIX_COLS %s
#endif // MATRIX_COLS

#ifndef MATRIX_ROWS
#    define MATRIX_ROWS %s
#endif // MATRIX_ROWS

#ifndef DIRECT_PINS
#    define DIRECT_PINS {%s}
#endif // DIRECT_PINS
""" % (col_count, row_count, ','.join(rows))


def col_pins(col_pins):
    """Return the config.h lines that set the column pins.
    """
    cols = ','.join(col_pins)
    col_num = len(col_pins)

    return """
#ifndef MATRIX_COLS
#    define MATRIX_COLS %s
#endif // MATRIX_COLS

#ifndef MATRIX_COL_PINS
#    define MATRIX_COL_PINS {%s}
#endif // MATRIX_COL_PINS
""" % (col_num, cols)


def row_pins(row_pins):
    """Return the config.h lines that set the row pins.
    """
    rows = ','.join(row_pins)
    row_num = len(row_pins)

    return """
#ifndef MATRIX_ROWS
#    define MATRIX_ROWS %s
#endif // MATRIX_ROWS

#ifndef MATRIX_ROW_PINS
#    define MATRIX_ROW_PINS {%s}
#endif // MATRIX_ROW_PINS
""" % (row_num, rows)


@cli.argument('-o', '--output', arg_only=True, type=normpath, help='File to write to')
@cli.argument('-q', '--quiet', arg_only=True, action='store_true', help="Quiet mode, only output error messages")
@cli.argument('-kb', '--keyboard', help='Keyboard to generate config.h for.')
@cli.subcommand('Used by the make system to generate info_config.h from info.json', hidden=True)
@automagic_keyboard
@automagic_keymap
def generate_config_h(cli):
    """Generates the info_config.h file.
    """
    # Determine our keyboard(s)
    if not cli.config.generate_config_h.keyboard:
        cli.log.error('Missing paramater: --keyboard')
        cli.subcommands['info'].print_help()
        return False

    if not is_keyboard(cli.config.generate_config_h.keyboard):
        cli.log.error('Invalid keyboard: "%s"', cli.config.generate_config_h.keyboard)
        return False

    # Build the info.json file
    kb_info_json = info_json(cli.config.generate_config_h.keyboard)

    # Build the info_config.h file.
    config_h_lines = ['/* This file was generated by `qmk generate-config-h`. Do not edit or copy.' ' */', '', '#pragma once']

    if 'diode_direction' in kb_info_json:
        config_h_lines.append(diode_direction(kb_info_json['diode_direction']))

    if 'keyboard_name' in kb_info_json:
        config_h_lines.append(keyboard_name(kb_info_json['keyboard_name']))

    if 'manufacturer' in kb_info_json:
        config_h_lines.append(manufacturer(kb_info_json['manufacturer']))

    if 'matrix_pins' in kb_info_json:
        if 'direct' in kb_info_json['matrix_pins']:
            config_h_lines.append(direct_pins(kb_info_json['matrix_pins']['direct']))

        if 'cols' in kb_info_json['matrix_pins']:
            config_h_lines.append(col_pins(kb_info_json['matrix_pins']['cols']))

        if 'rows' in kb_info_json['matrix_pins']:
            config_h_lines.append(row_pins(kb_info_json['matrix_pins']['rows']))

    if 'usb' in kb_info_json:
        for info_name, config_name in usb_properties.items():
            if info_name in kb_info_json['usb']:
                config_h_lines.append('')
                config_h_lines.append('#ifndef ' + config_name)
                config_h_lines.append('#    define %s %s' % (config_name, kb_info_json['usb'][info_name]))
                config_h_lines.append('#endif // ' + config_name)

    # Show the results
    config_h = '\n'.join(config_h_lines)

    if cli.args.output:
        cli.args.output.parent.mkdir(parents=True, exist_ok=True)
        if cli.args.output.exists():
            cli.args.output.replace(cli.args.output.name + '.bak')
        cli.args.output.write_text(config_h)

        if not cli.args.quiet:
            cli.log.info('Wrote info_config.h to %s.', cli.args.output)

    else:
        print(config_h)
