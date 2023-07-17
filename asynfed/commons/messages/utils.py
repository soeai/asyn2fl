
import logging
import json


def deserialize(json_str) -> dict:
    return json.loads(json_str)

def print_message(dict_to_print):
    def check_value(value):
        if isinstance(value, bool):
            return 'True' if value else 'False'
        elif value is None:
            return 'None'
        elif isinstance(value, dict):
            return json.dumps(value)
        elif isinstance(value, list):
            return ', '.join(map(str, value))
        else:
            return value if value != '' else 'None'
    
    def print_list(lst, offset=0):
        for i, v in enumerate(lst):
            if isinstance(v, dict):
                logging.info('|' + ' '*(offset+OFFSET) + f'[{i}]')
                print_dict(v, offset=offset+OFFSET*2)
            else:
                logging.info('|' + ' '*(offset+OFFSET) + f'[{i}]: {check_value(v):<50}')

    def print_dict(dict_to_print, offset=0):
        for k, v in dict_to_print.items():
            if isinstance(v, dict):
                logging.info('|' + ' '*offset + f'{k:<20}' + ' '*(MAX_LENGTH-offset-20))
                print_dict(v, offset=offset+OFFSET)
            elif isinstance(v, list):
                logging.info('|' + ' '*offset + f'{k:<20}' + ' '*(MAX_LENGTH-offset-20))
                print_list(v, offset=offset+OFFSET)
            else:
                logging.info('|' + ' '*offset + f'{k:<20}: {check_value(v):<50}')

    MAX_LENGTH = 80
    OFFSET = 3
    logging.info('|' + '-'*MAX_LENGTH + '|')
    print_dict(dict_to_print)
    logging.info('|' + '-'*MAX_LENGTH + '|')