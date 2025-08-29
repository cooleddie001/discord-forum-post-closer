import json
import discord
import asyncio
from datetime import datetime, timezone
import json

client = discord.Client(intents=discord.Intents.all())
tree = discord.app_commands.CommandTree(client)

#caching here to prevent redundent requests
done_tags = {

}

#similiar thing here, don't retrieve from disk every time we cant to check
mod_tags_cache = {}

async def resolve_forum_post(channel: discord.ChannelType.public_thread, user_id, send_message=True):
    #build name
    tag = mod_tags_cache.get(str(user_id), None)
    name = f"[DONE {tag}] {channel.name}"

    #shorten name so no 403
    if len(name) > 100:
        name = name[:97] + "..."

    #get current tags on post
    current_tags = channel.applied_tags.copy()
    current_tags.append(done_tags[channel.parent.id])
    if send_message:
        await channel.send(f"<@{user_id}> has resolved this post")
    await channel.edit(locked=True, archived=True, name=name, applied_tags=current_tags)

def is_mod_from_interaction(interaction: discord.Interaction):
    return interaction.channel.permissions_for(interaction.user).manage_threads

def sanity_checks(interaction):
    #if channel is not a forum post, return
    print(interaction.channel.type)
    if not interaction.channel.type == discord.ChannelType.public_thread:
        return False, "not a forum post"
    
    #mods need to set a tag first
    if mod_tags_cache.get(str(interaction.user.id), None) is None:
        return False, "need a tag, set your mod tag first with /set_tag"

    #if user does not have manage posts permission in the forum channel, return
    if not is_mod_from_interaction(interaction):
        return False, "not a mod"
    
    #if post has "DONE" tag, also return
    parent_forum = interaction.channel.parent
    if not hasattr(parent_forum, "available_tags"):
        return False, "either not a forum channel, or no tags"
    
    #check if the bot have permisisons to close the post (manage_threads)
    if not interaction.channel.permissions_for(interaction.guild.me).manage_threads:
        return False, "bot does not have permission to close this post"

    #cache done tag, if we haven't done so already
    if done_tags.get(interaction.channel.parent.id, None) is None:
        done_tag = next(
            (tag for tag in parent_forum.available_tags if "done" in tag.name.lower()),
            None
        )
        done_tags[interaction.channel.parent.id] = done_tag
    
    #if done tag is applied, it is already resolved, return
    done_tag = done_tags[interaction.channel.parent.id]
    if done_tag is None:
        return False, "this channel needs a DONE tag"

    if done_tag in interaction.channel.applied_tags:
        return False, "already resolved"

    return True, ""

@tree.command(name="resolve")
@discord.app_commands.default_permissions(manage_threads=True)
async def resolve(interaction: discord.Interaction):
    cleared, msg = sanity_checks(interaction)
    if not cleared:
        await interaction.response.send_message(msg)
        return

    await interaction.response.send_message(f"<@{interaction.user.id}> has resolved this post")
    await resolve_forum_post(interaction.channel, interaction.user.id, send_message=False)
    return

@tree.command(name="resolve_timer")
@discord.app_commands.default_permissions(manage_threads=True)
async def resolve_timer(interaction: discord.Interaction, time_duration: str = "1h"):
    cleared, msg = sanity_checks(interaction)
    if not cleared:
        await interaction.response.send_message(msg)
        return

    #parse time duration
    unit = time_duration[-1]
    if unit not in ["s", "m", "h", "d"]:
        await interaction.response.send_message("invalid time suffix or format, put in the format (time)(s, m, h, d)")
        return

    duration = int(time_duration[:-1])
    if unit == "m":
        duration *= 60
    elif unit == "h":
        duration *= 3600
    elif unit == "d":
        duration *= 86400

    await interaction.response.send_message(f"<@{interaction.user.id}> set a timer to auto-close this post <t:{int(datetime.now(timezone.utc).timestamp()) + duration}:R>, unless there is further activity.")
    await asyncio.sleep(duration)

    #one last check if done tag is applied, if not, resolve
    cleared, msg = sanity_checks(interaction)
    if not cleared:
        return
    
    #also check if there has been activity in the thread
    last_message = None
    async for message in interaction.channel.history(limit=1):
        last_message = message

    if last_message is not None and last_message.author.id != client.user.id:
        print(f"post id {interaction.channel.id} had activity, not closing")
        return

    await resolve_forum_post(interaction.channel, interaction.user.id)

@tree.command(name="set_tag")
@discord.app_commands.default_permissions(manage_threads=True)
async def set_tag(interaction: discord.Interaction, tag: str):
    if not is_mod_from_interaction(interaction):
        await interaction.response.send_message("not a mod")
        return

    tag = tag.strip().upper()
    if len(tag) > 5:
        await interaction.response.send_message("tag name too long, max 5 characters")
        return
    
    #write mod tag to file
    mod_tags_cache[str(interaction.user.id)] = tag
    with open("tags.json", "w") as f:
        json.dump({"tags": mod_tags_cache}, f, indent=4)

    await interaction.response.send_message(f"set your mod tag to {tag}")


@client.event
async def on_ready():
    await tree.sync()
    print("logged on, commands synced now")

with open("token.txt", "r") as f:
    token = f.read()

with open("tags.json", "r") as f:
    mod_tags_cache = json.load(f).get("tags", {})

client.run(token)