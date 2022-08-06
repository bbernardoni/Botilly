import discord
import os
import logging
import utils
import rename

logging.basicConfig(level=logging.INFO)

bot = discord.Bot(debug_guilds=[989558627901792287])

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

# overlay command
@bot.slash_command(name = "overlay", description = "Post overlay for current voice channel")
async def overlay(ctx):
  if not ctx.user.voice:
    await ctx.respond("Enter a voice channel to make an overlay for", ephemeral=True)
    return
  channel = ctx.user.voice.channel
  await ctx.respond(f"**Overlay for {channel.name}:**\nhttps://streamkit.discord.com/overlay/voice/{ctx.guild_id}/{channel.id}?icon=true&online=true&logo=white&text_color=%23ffffff&text_size=28&text_outline_color=%23000000&text_outline_size=0&text_shadow_color=%23000000&text_shadow_size=0&bg_color=%231e2124&bg_opacity=0&bg_shadow_color=%23000000&bg_shadow_size=0&invite_code=jreTYZS&limit_speaking=True&small_avatars=false&hide_names=false&fade_chat=0")

# rename command
# todo shorter name for code
# todo Option for special member counts?
# todo do I need renaming message?
@bot.slash_command(name = "rename", description = "Rename current voice channel")
async def renameVC(ctx, code: discord.Option(str, "Game Code", required=False)):
  rename_VC_msg = await rename.get_user_VC_renamable(ctx.user)
  if rename_VC_msg != "":
    await ctx.respond(rename_VC_msg, ephemeral=True)
    return
  await ctx.respond("Choose a game to name the voice channel", ephemeral=True, view=rename.RenameSelector(code))

# reset VC name when empty
@bot.event
async def on_voice_state_update(member, before, after):
  left_ch = before.channel
  if not left_ch or not left_ch.category or left_ch.category.name != rename.lobbies_cat:
    return # wrong category
  if left_ch.position == left_ch.category.voice_channels[0].position:
    return # waiting room VC
  if len(left_ch.members) > 0:
    return # not empty
  position = left_ch.position - left_ch.category.voice_channels[1].position
  name = rename.channel_defaults[position]["name"]
  if left_ch.name == name:
    return # already defaultly named

  # todo handle codenames spys leaving
  # todo reset VC limit too
  await utils.rename_vc(left_ch, name, None)

'''
Lobby postings
Summary at top
Message per event 
  Show host as well
  Game/tag
  AU mod info
  Time Description
  React
  Delete option (check owner / mod)
  Edit option (check owner / mod)
Rearrange will be a bit of a pain
  Probably have to repost everything later with each update
Auto delete? How long after?
'''

async def game_ac(ctx):
    return "foo", "bar", "baz", ctx.interaction.user.name

# host lobby command
@bot.slash_command(name = "host", description = "Host lobby")
async def host(ctx, game: discord.Option(str, "Game Name", autocomplete=game_ac)):
  tag_or_game = "asdf"
  host_name = "asdf"
  time = "asdf"
  desc = "asdf"
  await ctx.respond(f"{tag_or_game} lobby at <{time}> hosted by {host_name}. {desc}")

# run bot run
bot.run(os.getenv('TOKEN'))
