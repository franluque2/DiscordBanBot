import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Load watched channels
WATCHED_CHANNELS_FILE = 'watched_channels.json'

def load_watched_channels():
    if os.path.exists(WATCHED_CHANNELS_FILE):
        with open(WATCHED_CHANNELS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_watched_channels(channels):
    with open(WATCHED_CHANNELS_FILE, 'w') as f:
        json.dump(list(channels), f, indent=2)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

watched_channels = load_watched_channels()

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print(f'Monitoring {len(watched_channels)} channels')

@bot.tree.command(name="watchchannel", description="Add a channel to the honeypot watch list")
@app_commands.describe(channel_id="The ID of the channel to watch")
async def watch_channel(interaction: discord.Interaction, channel_id: str):
    # Check if user has any of the authorized roles
    authorized_role_ids = config.get('authorized_role_ids', [])
    user_role_ids = {role.id for role in interaction.user.roles}
    if not any(role_id in user_role_ids for role_id in authorized_role_ids):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    try:
        channel_id_int = int(channel_id)
    except ValueError:
        await interaction.response.send_message("❌ Invalid channel ID.", ephemeral=True)
        return
    
    # Verify channel exists
    channel = bot.get_channel(channel_id_int)
    if not channel:
        await interaction.response.send_message("❌ Channel not found.", ephemeral=True)
        return
    
    watched_channels.add(channel_id_int)
    save_watched_channels(watched_channels)
    await interaction.response.send_message(f"✅ Now watching channel: {channel.mention}", ephemeral=True)

@bot.tree.command(name="unwatchchannel", description="Remove a channel from the honeypot watch list")
@app_commands.describe(channel_id="The ID of the channel to stop watching")
async def unwatch_channel(interaction: discord.Interaction, channel_id: str):
    # Check if user has any of the authorized roles
    authorized_role_ids = config.get('authorized_role_ids', [])
    user_role_ids = {role.id for role in interaction.user.roles}
    if not any(role_id in user_role_ids for role_id in authorized_role_ids):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    try:
        channel_id_int = int(channel_id)
    except ValueError:
        await interaction.response.send_message("❌ Invalid channel ID.", ephemeral=True)
        return
    
    if channel_id_int in watched_channels:
        watched_channels.remove(channel_id_int)
        save_watched_channels(watched_channels)
        await interaction.response.send_message(f"✅ No longer watching channel ID: {channel_id}", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Channel ID {channel_id} was not being watched.", ephemeral=True)

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Check if message is in a watched channel
    if message.channel.id not in watched_channels:
        return
    
    # Check if user has any whitelisted role
    whitelisted_role_ids = config.get('whitelisted_role_ids', [])
    user_role_ids = {role.id for role in message.author.roles}
    if any(role_id in user_role_ids for role_id in whitelisted_role_ids):
        return
    
    # User posted in honeypot without whitelist - BAN
    try:
        # Calculate time threshold (1 hour ago)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        # Ban the user and delete their messages from the last hour
        await message.guild.ban(
            message.author,
            reason="Posted in honeypot channel",
            delete_message_seconds=3600  # Delete messages from last hour (3600 seconds)
        )
        
        ban_message = f"Banned {message.author} (ID: {message.author.id}) for posting in honeypot channel #{message.channel.name}"
        print(ban_message)
        
        # Log to logging channel if configured
        logging_channel_id = config.get('logging_channel_id')
        if logging_channel_id:
            logging_channel = bot.get_channel(logging_channel_id)
            if logging_channel:
                embed = discord.Embed(
                    title="🔨 User Banned",
                    description=f"User caught posting in honeypot channel",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="User", value=f"{message.author} ({message.author.mention})", inline=False)
                embed.add_field(name="User ID", value=str(message.author.id), inline=True)
                embed.add_field(name="Channel", value=message.channel.mention, inline=True)
                embed.add_field(name="Message Content", value=message.content[:1024] if message.content else "*No text content*", inline=False)
                embed.set_footer(text="Honeypot Ban System")
                
                await logging_channel.send(embed=embed)
        
    except discord.Forbidden:
        print(f"Failed to ban {message.author} - missing permissions")
    except Exception as e:
        print(f"Error banning {message.author}: {e}")

# Run the bot
bot.run(config['bot_token'])
