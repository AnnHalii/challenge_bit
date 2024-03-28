import json

from scrapper.constants import LINK
from scrapper.helpers import process_onion_link


def main():
    output_json = process_onion_link(LINK)

    with open(f'../domains.json', 'w') as output_file:
        output_file.write(json.dumps(output_json, indent=4))


if __name__ == '__main__':
    main()
