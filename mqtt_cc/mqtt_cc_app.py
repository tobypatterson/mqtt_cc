#!/usr/bin/env python3

import argparse
import sys

import mqtt_cc.ui


def _get_commandline_options():
    """
    Parse command line
    """
    # declare command-line argument parser
    command_line = argparse.ArgumentParser(
        description='MQTT Command and Control',
        epilog='A tool that can be used to talk to MQTT devices',
        )

    command_line.add_argument(
        '--host',
        metavar='HOST',
        type=str,
        help='The hostname with the MQTT Broker',
        default='ciorba.co'
    )

    return command_line.parse_args( sys.argv[ 1: ] )


def main():
    """ Script entry point """
    options = _get_commandline_options()

    import clipy.ui
    mqtt_cc.ui.main(options.host)

if __name__ == '__main__':
    main()