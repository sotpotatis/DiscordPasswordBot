# DiscordPasswordBot / PolicemanBot

PolicemanBot is an easy way to lock a set of roles in Discord with a password.
Nothing more, nothing less.
The bot only took a few hours for me to write and isn't my biggest Discord bot project at all, but there is no harm in making it open source just because of that 

### Run it yourself

Set an environment variable called `POLICEBOT_BOT_TOKEN` that has the value of your Discord bot token. Make sure you have requirements.txt installed, have created the relative directory `data/guilds`, and then you are good to go!
(the directory can be empty)

### Hosted version

The hosted version can be added to your server using the hosted invite link:

https://discord.com/oauth2/authorize?client_id=863082773379416115&scope=bot&permissions=339078238

This link can also be grabbed using the `?il` command.

You can revoke admin access from the bot, however, make sure that it still is allowed to delete messages, and that it can see all the channels
that you want it to see, and that it has permissions to delete messages and award roles.

### Quick tutorial

**Basic locking approach**
1. Create a role called something like "Authenticated" in Discord. (called {Your new role name} below)
2. Change the permissions of all channels you want to hide to:
    * Everyone --> View messages --> Disabled (X)
    * {Your new role name} --> View messages --> Enabled (✔)
3. Create a channel where people can enter a password (recommended)
4. Type `?al` or `?add_lock` in any channel
5. Follow the instructions given by the bot. When it asks for roles, tag {Your new role name}. When it asks for channels, tag the channel where you want people to be able to use the `?a` (authenticate) command.
6. Make sure the bot sends a confirmation message.

**Remove a created lock**
1. Go to the channel where the bot has sent a message *with* the title "The police is protecting here!".
2. Type `?rl` or `?remove_lock`
3. Wait for confirmation.

**Troubleshooting (related to usage, not code)**

* Make sure that the bot has permissions to manage, send, and delete messages in the configured channel.
* Make sure that you or the user having trouble is accepting DMs from the bot
* Make sure that if you're executing an administrative command, that you have admin permissions.
### Note about tokens

Previous commits have included a bot token directly in the code, but that is of course not how you should handle security... :P
That token has been revoked, so there is no need for you to think that you can hack me with it:)
