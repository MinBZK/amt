import sys

from yaml import load, dump


def create_minimal_system_card():
    """
    This script will locally create a system card with only containing the version and the name based on:
    (https://github.com/MinBZK/ai-validation-tad-poc/tree/main/cards). This information will be stores locally in a
    directory.
    :return:
    """
    system_card_init = {"version": "0.1a3", "name": "test algorithm"}
    with open("./tests/data/system_card.yaml", "w") as outfile:
        dump(system_card_init, outfile, default_flow_style=False, sort_keys=False)


# def load_minimal_system_card():

# def write_minimal_system_card():
