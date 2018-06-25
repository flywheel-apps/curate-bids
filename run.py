import json
from flywheel_bids.curate_bids import main_with_args

if __name__ == '__main__':

    # Grab Config
    config = '/flywheel/v0/config.json'
    with open(config) as configFile:
        CONFIG = json.load(configFile)

    api_key = CONFIG['inputs']['api_key']['key']
    session_id = CONFIG['destination']['id']
    reset = CONFIG['config']['reset']

    main_with_args(api_key, session_id, reset)
