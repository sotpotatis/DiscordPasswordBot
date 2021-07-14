'''Data.py
Various functions related to data readings and writings.'''

import os, json, logging, datetime, pytz

#Paths
SCRIPT_PATH = os.path.realpath(__file__)
SCRIPT_DIRECTORY = os.path.dirname(SCRIPT_PATH)
DATA_PATH = os.path.join(SCRIPT_DIRECTORY, "data/")
GUILDS_PATH = os.path.join(DATA_PATH, "guilds/")

#Defaults
DEFAULT_GUILD_CONFIGURATION = {
    "enabled_locks": [],
    "configuration_created_at": None
}

#Exceptions
class GuildDoesNotExistError(Exception):
    pass

#Logging
logger = logging.getLogger(__name__)

#Functions
def get_now():
    '''Function for getting the current time.
    The PolicemanBot uses UTC for simplicity.'''
    return datetime.datetime.now(tz=pytz.timezone("UTC"))

def read_json_from_file(filepath):
    '''Read JSON from a file and returns it as a dict'''
    logger.debug(f"Reading JSON from filepath {filepath}...")
    return json.loads(open(filepath, "r").read())

def write_json_to_file(data, filepath):
    '''Updates JSON to a file.'''
    logger.debug(f"Updating JSON from filepath {filepath}...")
    with open(filepath, "w") as json_file:
        json_file.write(json.dumps(data))

def get_guild_paths(guild_id):
    '''Function for getting the filepaths associated with a guild.'''
    logger.info(f"Getting guild paths for {guild_id}...")
    guild_path = os.path.join(GUILDS_PATH, str(guild_id))
    guild_configuration_path = os.path.join(guild_path, "config.json")
    return guild_path, guild_configuration_path

def get_guild_configuration(guild_id):
    '''Function for getting the guild configuration for a certain guild.'''
    logger.info(f"Getting configuration for {guild_id}...")
    guild_path, guild_configuration_path = get_guild_paths(guild_id) #Get guild file paths
    if not os.path.exists(guild_path):
        logger.info("Guild directory does not exist.")
        return None
    elif not os.path.exists(guild_configuration_path):
        logger.info("Guild configuration does not exist.")
        return None
    logger.info("Configuration file exists. Returning...")
    return read_json_from_file(guild_configuration_path)

def create_guild_configuration(guild_id):
    '''Function for creating a guild configuration.'''
    logger.info(f"Creating guild configuration for {guild_id}...")
    guild_path, guild_configuration_path = get_guild_paths(guild_id) #Get guild file paths
    if not os.path.exists(guild_path): #If the guild directory does not exist
        logger.info("Guild directory does not exist. Creating...")
        os.mkdir(guild_path)
        logger.info("Guild directory created.")
    if not os.path.exists(guild_configuration_path): #If the guild configuration file does not exist
        logger.info("Guild configuration file does not exist. Creating...")
        guild_data = DEFAULT_GUILD_CONFIGURATION
        guild_data["configuration_created_at"] = str(get_now())
        write_json_to_file(guild_data, guild_configuration_path)
        logger.info("Guild configuration file created.")
    logger.info("Done with creation.")

def get_channel_ids_with_message(guild_id, return_only_enabled_locks=False):
    '''Function for getting the list of channel IDs for a guild
    where a lock message has been created
    '''
    logger.info(f"Getting channel IDs with bot message for guild {guild_id}...")
    #Get the guild data
    guild_configuration = get_guild_configuration(guild_id)
    #Now, check if the channel is set up for authentication
    logger.info("Guild configuration retrieved.")
    #Find the channel
    locked_channel_ids = []
    if guild_configuration == None: #This will be None if a configuration does not exist for the guild
        logger.info("Configuration is None, returning empty list...")
        return []
    logger.info("Iterating through enabled locks...")
    for lock in guild_configuration["enabled_locks"]:
        if lock["enabled"] or return_only_enabled_locks == False:
            locked_channel_ids.append(lock["channel_id"])
    logger.info(f"Found {len(locked_channel_ids)} locked channels.")
    logger.info(f"Locked channel list for server: {locked_channel_ids}")
    #Return the list of locks
    return locked_channel_ids

def get_lock_for_channel_id(guild_id, channel_id, return_only_enabled_locks=True):
    '''Function for finding the enabled lock for the channel ID.'''
    logger.info(f"Getting lock for guild ID {guild_id}, channel ID {channel_id}...")
    #Get the guild data
    guild_configuration = get_guild_configuration(guild_id)
    #Now, check if the channel is set up for authentication
    logger.info("Guild configuration retrieved.")
    #Find the locked channel
    for lock in guild_configuration["enabled_locks"]:
        if lock["enabled"] or not return_only_enabled_locks:
            if lock["channel_id"] == channel_id:
                logger.info("Found enabled lock! Returning...")
                return lock
    logger.warning("Did not find enabled lock! Returning None...")
    return None

def generate_lock_data(channel_id, hashed_password, custom_message, award_role_ids, sent_information_message, enabled=True):
    '''Function for generating a dict of lock data. This will then get dumped into a JSON.
    Channel_ID is passed as an integer, hashed_password is passed as a string, custom_message is passed as a string,
    sent_information_message is a discord.Message object, and embed is a boolean'''
    lock_data = {
        "enabled": enabled,
        "channel_id": channel_id,
        "password": hashed_password,
        "custom_message": custom_message,
        "award_role_ids": award_role_ids,
        "sent_information_message": {
            "id": sent_information_message.id
        },
        "created_at": str(get_now())
    }
    return lock_data

def update_guild_config(guild_id, new_config):
    '''Function for updating the guild config for a certain ID'''
    logger.info(f"Updating guild configuration for {guild_id}...")
    guild_path, guild_configuration_path = get_guild_paths(guild_id)
    write_json_to_file(new_config, guild_configuration_path)
    logger.info("Guild configuration updated.")
