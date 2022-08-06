import discord
import os
import json
import asyncio
import requests

# Hacked together workaround to rename a channel manually with the Discord API directly
# This is necessary since py-cord's default handling of rate limits doesn't match desired behavior
# Code derived from https://github.com/Pycord-Development/pycord/blob/d0d7451fd5f040ac2ccd4ab41be98901ed00d320/discord/http.py#L217
async def rename_vc(channel, name, rate_limit_callback):
  url = f"https://discord.com/api/v{discord.API_VERSION}/channels/{channel.id}"
  headers = {
    "Authorization": f"Bot {os.getenv('TOKEN')}",
    "Content-Type": "application/json"
  }
  payload = f'{{"name": "{name}"}}'
  
  response = None
  data = None
  for tries in range(5):
    try:
      response = requests.request("PATCH", url, data=payload, headers=headers)
      data = json.loads(response.text)

      # request successful, return
      if 300 > response.status_code >= 200:
        return

      # we are being rate limited
      if response.status_code == 429:
        if not response.headers.get("Via") or isinstance(data, str):
          raise discord.HTTPException(response, data)

        retry_after = data["retry_after"]
        task = asyncio.current_task()
        await rate_limit_callback(retry_after, task)
        
        try:
          await asyncio.sleep(retry_after)
        except asyncio.CancelledError:
          raise
        continue

      # we've received a 500, 502, or 504, unconditional retry
      if response.status_code in {500, 502, 504}:
        await asyncio.sleep(1 + tries * 2)
        continue

      # the usual error cases
      if response.status_code == 403:
        raise discord.Forbidden(response, data)
      elif response.status_code == 404:
        raise discord.NotFound(response, data)
      elif response.status_code >= 500:
        raise discord.DiscordServerError(response, data)
      else:
        raise discord.HTTPException(response, data)

    except OSError as e:
      if tries < 4 and e.errno in (54, 10054):
        await asyncio.sleep(1 + tries * 2)
        continue
      raise

  if response is not None:
    if response.status_code >= 500:
      raise discord.DiscordServerError(response, data)
    raise discord.HTTPException(response, data)
  raise RuntimeError("Unreachable code in HTTP handling")
