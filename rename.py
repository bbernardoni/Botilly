import discord
import time
import asyncio
import utils

# game data
games = [
  {"name": "Among Us"},
  {"name": "Codenames"},
  {"name": "Red Spymaster"},
  {"name": "Blue Spymaster"},
  {"name": "Jackbox"},
  {"name": "Fall Guys"},
  {"name": "Valorant"},
  {"name": "Town of Salem"},
  {"name": "Traitors of Salem"},
  {"name": "Goose Goose Duck"},
  {"name": "Phasmophobia"},
  {"name": "Crab Game"},
  {"name": "Gartic Phone"},
  {"name": "Clue"},
  {"name": "First Class Trouble"},
  {"name": "Golf with your Friends"},
  {"name": "Tabletop Simulator"},
]
channel_defaults = [
  {"name": "Tiny Beans 1", "count": 5},
  {"name": "Tiny Beans 2", "count": 5},
  {"name": "Tolerable Beans 1", "count": 10},
  {"name": "Tolerable Beans 2", "count": 10},
  {"name": "Jumbo Beans 1", "count": 15},
  {"name": "Jumbo Beans 2", "count": 15},
  {"name": "Monumental Beans", "count": 20},
  {"name": "Unreasonable Beans", "count": 0},
]

# returns non empty string if invalid
lobbies_cat = "Game Lobbies"
async def get_user_VC_renamable(user):
  if not user.voice:
    return "Enter a voice channel to rename"
  channel = user.voice.channel
  if not channel.category or channel.category.name != lobbies_cat:
    return f'Enter a voice channel in "{lobbies_cat}" to rename'
  elif channel.position == channel.category.voice_channels[0].position:
    return f'Cannot rename "{channel.name}"' # waiting room
  return ""

# rename view
class RenameSelector(discord.ui.View):
  def __init__(self, code):
    self.code = code
    super().__init__()
    
  @discord.ui.select(
      placeholder = "Games",
      min_values = 1,
      max_values = 1,
      options = [discord.SelectOption(label="Reset to Default")] 
        + [discord.SelectOption(label=game["name"]) for game in games]
  )
  async def select_callback(self, select, interaction):
    rename_VC_msg = await get_user_VC_renamable(interaction.user)
    if rename_VC_msg != "":
      await interaction.response.edit_message(content=rename_VC_msg, view=None)
      return
    
    channel = interaction.user.voice.channel
    old_name = channel.name
    new_name = select.values[0]
    if select.values[0] == "Reset to Default":
      position = channel.position - channel.category.voice_channels[1].position
      new_name = channel_defaults[position]["name"]
    elif self.code:
      new_name += f" | {self.code}"

    if old_name == new_name:
      await interaction.response.edit_message(content=f'Channel already named "{old_name}"', view=None)
      return
    
    async def rate_limit_callback(retry_after, task):
      # rename cancel view
      class RenameCancel(discord.ui.View):
        @discord.ui.button(label="Cancel Rename", style=discord.ButtonStyle.primary)
        async def button_callback(self, button, interaction):
          task.cancel()
          await interaction.response.edit_message(content="Voice channel rename cancelled", view=None)

      # send retry message
      finish_timestamp = int(time.time() + retry_after)
      await interaction.response.edit_message(content=f'Voice channel rename limit hit when renaming voice channel "{old_name}" to "{new_name}". Waiting {retry_after} seconds until <t:{finish_timestamp}:T> to retry.', view=RenameCancel())

    # try to rename
    rename_task = asyncio.create_task(utils.rename_vc(channel, new_name, rate_limit_callback))
    try:
      await rename_task
    except asyncio.CancelledError:
      return

    # rename succeeded
    if interaction.response.is_done():
      await interaction.followup.edit_message(interaction.message.id, content="Voice channel successfully renamed", view=None)
    else:
      await interaction.response.edit_message(content="Voice channel successfully renamed", view=None)
    await interaction.channel.send(f'**Voice channel "{old_name}" renamed to "{new_name}"**')