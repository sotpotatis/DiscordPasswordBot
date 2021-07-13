'''Discord Police Bot
The Discord Police Bot is a really simple bot that allows one to lock a server.
It requires you to press a button and enter a message to earn a role.

Link to the beautiful base for the original profile picture:
https://pixabay.com/vectors/policeman-officer-stop-cop-uniform-23796/

Hosted invite link:
https://discord.com/oauth2/authorize?client_id=863082773379416115&scope=bot&permissions=339078238
You can revoke admin access from the bot, however, make sure that it still is allowed to delete messages, and that it can see all the channels
that you want it to see, and that it has permissions to delete messages and award roles.
'''
import logging, json, os, asyncio
from discord import Embed, Color, Game, utils, ChannelType
from discord.ext import commands
from data import  *
from werkzeug.security import check_password_hash, generate_password_hash
BOT_COMMAND_PREFIX = "?"
bot = commands.Bot(command_prefix=BOT_COMMAND_PREFIX, help_command=None) #The help command provided is a custom one, see further below

#Constants
DEFAULT_COMMAND_COLOR = Color.dark_teal()
DEFAULT_ERROR_COLOR = Color.red()
BOT_TOKEN = os.environ["POLICEBOT_BOT_TOKEN"]
BOT_INVITE_LINK = "https://discord.com/oauth2/authorize?client_id=863082773379416115&scope=bot&permissions=339078238" #See note above
#Logging and logging settings
logging.basicConfig(
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

#Functions
def generate_error_embed(title="An error occurred", description="Please try again later. Sorry, m8!"):
    '''Function for generating an error embed.'''
    return Embed(
        title=title,
        description=description,
        color=DEFAULT_ERROR_COLOR
    )

#Commands
@bot.command()
async def ping(ctx):
    '''Ping command.
    A simple ping command.'''
    logger.info("Got a ping request!")
    await ctx.send(
        embed=Embed(
            title="Hey, mate! 👋",
            description=f"I gotcha'. Ping-pong doesn't sound like the police car sirens, but I respond with a pong to ya'. \n➡**I'm pingin' & pongin' at around `{round(bot.latency,2)} ms` for ya', friendo.**",
            color=DEFAULT_COMMAND_COLOR
        )
    )

@bot.command(aliases=["a"])
@commands.cooldown(1, 30, commands.BucketType.user)
async def authenticate(ctx):
    '''The main authentication command.
    This is called by a user when they want
    to authenticate. The bot then sends a DM to the user, requesting the password.
    The command has a cooldown per user to avoid bruteforcing.
    The user only has one password attempt and requires to write "?a" in a channel with every authentication attempt.
    This might seem tedious, but if you think about it, it is a great way to prevent bruteforcing since it adds an extra step for someone
    that would attempt to bruteforce.'''
    logger.info("Got a request to authenticate!")
    logger.info("Deleting original message...")
    await ctx.message.delete()
    logger.info("Original message deleted.")
    #First, validate if the channel actually has a lock enabled
    guild_id = str(ctx.guild.id)
    channel_id = ctx.channel.id
    user_id = ctx.user.id
    tracked_channels = get_channel_ids_with_message(guild_id)
    if channel_id not in tracked_channels:
        logger.warning("The channel is not being tracked by the bot! Sending error message...")
        await ctx.send(
            embed=generate_error_embed("The channel is not being tracked by me!",
                                 "This channel does not seem to have an active authentication message. Are you sure that you are using this command in the right channel, sweetheart?")
        )
        return
    #If we get here, the channel is being tracked, so we want to get the password
    logger.info("The channel is being tracked by the bot! Finding message...")
    enabled_lock = get_lock_for_channel_id(guild_id, channel_id)
    #The function will return None if an enabled lock was not found
    if enabled_lock is None:
        logger.info("It seems like the channel's lock is not active! Sending error...")
        await ctx.send(
            embed=generate_error_embed("The channel is not being tracked by me!",
                                 "It seems like this channel's does not have an active lock currently."),
            delete_after=30
        )
        return
    logger.info("Found an enabled lock.")
    #Check if the user has authenticated
    if user_id in enabled_lock["authenticated_users"]:
        logger.info("User has already authenticated! Sending error message...")
        await ctx.send(
            embed=generate_error_embed(
                "You have already authenticated",
                f"Hey {ctx.author.mention}, you have already authenticated and I have awarded you the roles."
            ),
            delete_after=60
        )
    #Now, send the user a DM requesting the password.
    logger.info("Sending user a DM...")
    try:
        password_request_message = Embed(
            title="🔒 Authentication check! ✋",
            description=f"Hi there, {ctx.author.mention}, you called the authentication command in the server {ctx.guild.name}. Please reply with the password.\n⚠Policemen doesn't work all day, so you have **1 minute to reply with the password**. After that, you have to use the `?a` command again to get a new message from me.",
            color=DEFAULT_COMMAND_COLOR
        )
        password_request_message.set_footer(text="Make sure that you aren't trying to authenticate in another server at the same time. If so,")
        await ctx.author.send(
            embed=password_request_message
        )
    except Exception as e:
        logger.warning("Failed to send user a DM!", exc_info=e)
        await ctx.send(
            embed=generate_error_embed(
                f"{ctx.author.mention}, I could not send you a DM!",
                "Make sure you accept DMs from people like me (this is usually in your privacy settings). I mean, it's not every day you get a policeman knockin' at ya' door! I need to be able to send you a private message so you can provide me with a password."
            )
        )
        return
    #Now, wait for a response to the message
    def is_dm_from_author(message):
        '''Checks if the message is a DM from the message author.'''
        return message.author.id == ctx.author.id and message.channel.type == ChannelType.private
    logger.info("Waiting for response...")
    try:
        response = await bot.wait_for("message", check=is_dm_from_author, timeout=60)
    except asyncio.TimeoutError:
        logger.info("User didn't respond!")
        await ctx.author.send(
            embed=generate_error_embed("You were too slow, mate!",
                                       "You didn't send the password to authenticate with in time. Now, don't worry! Go back to the channel and then write `?a` again, and you will get a new chance from me to authenticate. Cheers!")
        )
        return
    logger.info("Got a response! Using that as password...")
    user_entered_password = response.content
    #Delete password message
    logger.info("Deleting password message...")
    await response.delete()
    logger.info("Password message deleted.")
    logger.info("Found an enabled lock, checking password...")
    #Get the password for the lock
    lock_password = enabled_lock["password"]
    #Check if the passwords are equal
    if check_password_hash(lock_password, user_entered_password) is False:
        logger.info("An incorrect password was entered!")
        error_embed = generate_error_embed(
            "✋ Access denied! ✋",
            f"Sorry, {ctx.author.mention}, it seems like you didn't enter the correct password. I'm therefore doin' my job and keeping you out!"
        )
        error_embed.set_footer(text="You may try again in 30 seconds.")
        await ctx.author.send(
            embed=error_embed
        )
        error_embed.set_footer(text="You may try again in 30 seconds. This message will be automatically be deleted in 2 minutes.")
        await ctx.send(
            embed=error_embed,
            delete_after=120
        )
        return
    else:
        logger.info("A correct password was entered!")
        #Now, we award the listed role IDs to the user
        role_ids_to_award = enabled_lock["award_role_ids"]
        roles = []
        for role_id in role_ids_to_award:
            logger.info(f"Adding role ID {role_id}...")
            role = utils.get(ctx.guild.roles, id=role_id)
            roles.append(role)
            logger.info("Role ID added.")
            logger.info("Awarding role...")
            await ctx.author.add_roles(role)
            logger.info("Role awarded.")
        #Add user to list of authenticated users
        guild_configuration = get_guild_configuration(guild_id)
        if "authenticated_users" not in enabled_lock:
            enabled_lock["authenticated_users"] = []
        enabled_lock["authenticated_users"].append(user_id)
        guild_configuration["enabled_locks"][guild_configuration["enabled_locks"].index(enabled_lock)] = enabled_lock
        logger.info("Updating guild configuration...")
        update_guild_config(guild_id, guild_configuration)
        logger.info("Guild configuration updated.")
        final_embed = Embed(
            title="✅ Oh yeah, that's correct!",
            description=f"I have now let ya in, {ctx.author.mention}! I awarded you some roles since you enterred the correct password.",
            color=DEFAULT_COMMAND_COLOR
        )
        logger.info("Sending final embed to user...")
        await ctx.author.send(embed=final_embed)
        final_embed.set_footer(text="This message will automatically be deleted in 2 minutes.")
        logger.info("Sending final embed to channel...")
        await ctx.send(embed=final_embed, delete_after=120)

@bot.command(aliases=["al"])
async def add_lock(ctx):
    logger.info("Got a request to add a lock!")
    #Check if the author is the server admin
    if not ctx.author.guild_permissions.administrator:
        logger.info("The user is not an admin!")
        await ctx.send(embed=generate_error_embed(
            "You are not a server admin!",
            "Currently, only server admins can create lock messages."
        ))
        return

    logger.info("Check passed, asking questions...")
    #General for all questions
    no_response_error_message = generate_error_embed("No response!",
                                                    f"Hey, {ctx.author.id}, you didn't respond to my previous message. **You get 2 minutes to do that!** Call the `?al`/`?add_lock` command again to start over.")
    #Question 1, what should the password be?
    question_1_embed = Embed(
        title="Step 1: Select password",
        description="Gotcha, we're getting started with the creation. **What should the password be?** This password will be used by people to authenticate. Reply with the password.",
        color=DEFAULT_COMMAND_COLOR
    )
    question_1_embed.set_footer(text="The password will never be stored in plain text. It will be stored in hashed SHA256 format (aka. with strong security).")
    await ctx.send(embed=question_1_embed)
    logger.info("Question 1 sent.")
    def is_from_user(message):
       '''Checks if the message is from the same user that called the command'''
       return message.author.id == ctx.author.id
    #Wait for question 1 response
    try:
        password_message = await bot.wait_for("message", check=is_from_user, timeout=120) #Wait for a reply with a timeout of 120 seconds
    except TimeoutError:
        logger.info("No response from user!")
        await ctx.send(embed=no_response_error_message)
        return
    password = generate_password_hash(password_message.content, "sha256")
    logger.info("Password retrieved. Asking for roles to add...")
    #Question 2, which roles should be awarded?
    question_2_embed = Embed(
        title="Step 2: Select roles",
        description="To protect the server, you need to select which roles that should be added to a user that enters the correct password\n➡Tag **all** roles you want to award a user that successfully has entered the correct password in a message below.",
        color=DEFAULT_COMMAND_COLOR
    )
    await ctx.send(embed=question_2_embed)
    #Wait for question 2 response
    try:
        roles_message = await bot.wait_for("message", check=is_from_user, timeout=120) #Wait for a reply with a timeout of 120 seconds
    except TimeoutError:
        logger.info("No response from user!")
        await ctx.send(embed=no_response_error_message)
        return
    logger.info("Got roles. Getting IDs...")
    award_role_ids = [role.id for role in roles_message.role_mentions]
    #Check if at least one role has been mentioned
    if len(award_role_ids) == 0:
        logger.info("No roles have been mentioned in the message! Returning error...")
        await ctx.send(embed=generate_error_embed(
            "No roles mentioned",
            "You didn't mention any roles to award in your message! I need roles to award, otherwise there is no need locking with a password 🙄\nCall the creation command again to restart the setup."
        ))
        return
    logger.info("Roles were mentioned. Asking for channel...")
    #Question 3: which channel should the lock message be sent in?
    question_3_embed = Embed(
        title="Step 3: Which channel?",
        description="Mention a channel below (like #police-discussion) to where I should send an instruction message with how to unlock access to the roles.",
        color=DEFAULT_COMMAND_COLOR
    )
    question_3_embed.set_footer(text="Make sure that the mentioned channel becomes blue in your message (it embeds as a channel link).")
    await ctx.send(embed=question_3_embed)
    #Wait for question 3 response
    try:
        channel_message = await bot.wait_for("message", check=is_from_user, timeout=120) #Wait for a reply with a timeout of 120 seconds
    except TimeoutError:
        logger.info("No response from user!")
        await ctx.send(embed=no_response_error_message)
        return
    logger.info("Channel message gotten!")
    #Validate the number of mentioned channels
    if len(channel_message.channel_mentions) != 1: #The bot can only send the message in one channel
        logger.info("Channel mention number is not approved! Sending error message...")
        await ctx.send(embed=generate_error_embed(
            "Incorrect number of channels mentioned",
            "Please mention one channel for me to send the message in 🙄 Simple, right? Nah, I forgive ya! Mistakes happen.\nCall the creation command again to restart the setup."
        ))
        return
    mentioned_channel = channel_message.channel_mentions[0]
    channel_id = mentioned_channel.id
    #Check if a lock has been created in the channel already
    server_config = get_guild_configuration(str(ctx.guild.id))
    if server_config != None:
        logger.info("Server configuration found. Checking for lock for this channel already...")
        channel_lock = get_lock_for_channel_id(str(ctx.guild.id), channel_id, return_only_enabled_locks=False)
        if channel_lock != None:
            logger.warning("Error! A lock for the channel exists! Returning error...")
            await ctx.send(embed=generate_error_embed(
                "Lock message already created!",
                "You have already asked me to send a lock message in this channel. You can only have one lock message per channel.\nCall the creation command again to restart the setup."))
            return
        else:
            logger.info("No lock for the channel exist.")
    else: #Create a configuration for later
        logger.info("Guild configuration does not exist. Creating one for later...")
        create_guild_configuration(ctx.guild.id)
    logger.info("Channel retrieved. Asking for custom message....")
    #Question 4, what message to show?
    question_4_embed = Embed(
        title="Step 4: Select a custom message",
        description="Type a pretty message that will be shown in the message I send with information on how to authenticate.",
        color=DEFAULT_COMMAND_COLOR
    )
    question_4_embed.set_footer(text="Write \"nomessagepls\" and I will not add a custom message!")
    await ctx.send(embed=question_4_embed)
    #Wait for question 4 response
    try:
        custom_text_message = await bot.wait_for("message", check=is_from_user, timeout=120) #Wait for a reply with a timeout of 120 seconds
    except TimeoutError:
        logger.info("No response from user!")
        await ctx.send(embed=no_response_error_message)
        return
    custom_text = custom_text_message.content
    logger.info("Custom text retrieved. Sending message...")
    #Send the lock message
    lock_embed = Embed(
        title="📢The police is protecting here ✋",
        description=f"I'm protecting the access to some channels with a password that has been set by {ctx.author.mention}.",
        color=DEFAULT_COMMAND_COLOR
    )
    #Add custom text
    if custom_text.lower() != "nomessagepls":
        logger.info("Adding custom text...")
        lock_embed.add_field(name=f"Custom message from {ctx.author.name}", value=f"`{custom_text}`", inline=False)
    else:
        logger.info("Custom text will not be added.")
    #Add information about how to unlock
    lock_embed.add_field(name="🔒 How to gain access to the locked channels?", value="Type `?a` in this channel, and I will send you a private message asking for the password.", inline=False)
    lock_message = await mentioned_channel.send(embed=lock_embed)
    logger.info("Lock message sent.")
    logger.info("Saving lock...")
    lock_data = generate_lock_data(
        channel_id,
        password,
        custom_text,
        award_role_ids,
        lock_message
    )
    logger.info("Data generated. Adding to config...")
    server_config = get_guild_configuration(ctx.guild.id)
    server_config["enabled_locks"].append(lock_data)
    logger.info("Writing data...")
    update_guild_config(ctx.guild.id, server_config)
    logger.info("Data written. Sending confirmation message...")
    confirmation_message = Embed(
        title="✅ Message created!",
        description="I have now sent a message with information about the newly created lock, and I will start protecting and asking for passwords. At ya' service, m8!",
        color=DEFAULT_COMMAND_COLOR
    )
    await ctx.send(embed=confirmation_message)
    logger.info("Configuration message sent.")

@bot.command(aliases=["rl"])
async def remove_lock(ctx):
    '''The remove_lock command can be used to remove a lock from the channel.
    It permanently deletes the lock from the database.'''
    logger.info("Got a request to remove a lock!")
    #Check if the author is the server admin
    if not ctx.author.guild_permissions.administrator:
        logger.info("The user is not an admin!")
        await ctx.send(embed=generate_error_embed(
            "You are not a server admin!",
            "Currently, only server admins can create lock messages."
        ))
        return
    #Get guild ID and channel ID and find lock
    guild_id = str(ctx.guild.id)
    channel_id = ctx.channel.id
    lock_for_channel = get_lock_for_channel_id(guild_id, channel_id, return_only_enabled_locks=False)
    if lock_for_channel == None:
        logger.info("No lock found! Sending error message...")
        await ctx.send(
            embed=generate_error_embed(
                "No lock found for channel",
                "I couldn't find an enabled lock. Make sure that you type this command in the same channel where I have sent a message asking users to authenticate. Cheers!"
            )
        )
        return
    logger.info("Lock found! Removing from configuration...")
    #Remove lock from configuration
    guild_configuration = get_guild_configuration(guild_id)
    guild_configuration["enabled_locks"].remove(lock_for_channel)
    logger.info("Enabled lock removed in memory. Removing lock message...")
    #Remove the lock message sent by the bot
    lock_message = await ctx.fetch_message(lock_for_channel["sent_information_message"]["id"])
    logger.info("Message retrieved. Removing...")
    await lock_message.delete()
    logger.info("Message deleted. Updating configuration...")
    update_guild_config(guild_id, guild_configuration)
    logger.info("Guild configuration updated. Sending confirmation message...")
    final_message = Embed(
        title="✅ Lock removed",
        description="I'm no longer tracking the password lock associated with the message I sent in this channel earlier.",
        color=DEFAULT_COMMAND_COLOR
    )
    final_message.set_footer(text="Want to create a new lock? Use the ?al//?add_lock command.")
    await ctx.send(embed=final_message)
    logger.info("Message sent and lock removed. All good!")

@bot.command()
async def help(ctx):
    '''The help command. This command is hard-coded, because the bot is simple to use and doesn't have that many commands.'''
    logger.info("Got a request to the help message! Sending...")
    final_message = Embed(
        title="Help",
        description="I'm PolicemanBot, and I can help you to lock your Discord servers with a password, by giving out certain roles to people who know the right password.",
        color=DEFAULT_COMMAND_COLOR
    )
    final_message.add_field(name="Lock a set of roles with a password", value="Type `?al` or `?add_lock` in any channel to get presented with an interactive process.", inline=False)
    final_message.add_field(name="Remove an existing lock", value="Type `?rm` or `?remove_lock` in the channel where I sent the message about an active lock to remove it.", inline=False)
    final_message.add_field(name="Unlocking", value="Type `?a` or `?authenticate` in the channel where I sent the message about an active lock to get a private message asking you for the password.", inline=False)
    final_message.add_field(name="Permissions", value="Every server member can try to authenticate, but only admins can delete or add locks.", inline=False)
    final_message.add_field(name="Invite link", value="Invite me to your own server using the `?il` or `?invite_link` command.", inline=False)
    await ctx.send(embed=final_message)

@bot.command(aliases=["il"])
async def invite_link(ctx):
    '''Invite link command. Send an invite link to the bot to a channel.'''
    logger.info("Got a request to the invite link command!")
    final_message = Embed(
        title="Invite link",
        description="Here is an invite link to the bot!",
        color=DEFAULT_COMMAND_COLOR
    )
    final_message.add_field(name="Link:", value=BOT_INVITE_LINK, inline=False)
    await ctx.send(embed=final_message)

#Events
@bot.event
async def on_ready(*args):
    logger.info("Bot is ready!")
    logger.info("Changing presence...")
    await bot.change_presence(activity=Game(name=f"{BOT_COMMAND_PREFIX}help | PolicemanBot - lock any server with a password!"))

@bot.event
async def on_command_error(ctx, error):
    logger.warning("Currently handling an error - yikes, that's no good!")
    original_error = getattr(error, "original", error)
    logger.info(f"Original error: {original_error}.")
    if isinstance(error, commands.CommandOnCooldown):
        logger.info("The error is a cooldown error! Sending message...")
        await ctx.send(
            embed=generate_error_embed(
                "Command on cooldown",
                f"Sorry about the inconvenience, {ctx.author.mention}, but this command is on cooldown. You may use it again in {round(error.retry_after,2)} seconds."
            )
        )
    elif isinstance(error, commands.CommandNotFound):
        logger.info("The command was not found! Ignoring exception...")
    else:
        logger.critical("The exception was unhandled!")
        await ctx.send(
            embed=generate_error_embed("An unknown error occurred!",
                                       "Sorry. Maybe I need a lunch break. Try again later! If this error persists, report it to the bot author: `sötpotatis!#5212`\nThis could be a permission error - make sure I have permissions to manage and send messages!")
        )

#Logg in and start the bot
logger.info("Logging in bot...")
bot.run(BOT_TOKEN)
