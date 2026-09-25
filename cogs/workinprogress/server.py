import discord
import dotenv
import os
import requests
import time

dotenv.load_dotenv('./.env')

EXAROTON_KEY = os.getenv("EXAROTON_KEY")
EXAROTON_SERVER_ID = os.getenv("EXAROTON_SERVER_ID")

# don't load this cog in the main file as these commands are
# either unfinished or don't work properly

class WorkInProgress(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    server = discord.SlashCommandGroup(name="server", description="Commands for server management.")

    @server.command(name="geyserupdate", guild_ids=[608476415825936394, 1117615350503190549])
    async def geyserupdate(self, ctx: discord.ApplicationContext):
        if not EXAROTON_KEY or not EXAROTON_SERVER_ID:
            await ctx.respond("Exaroton is not configured. Set EXAROTON_KEY and EXAROTON_SERVER_ID in .env.", ephemeral=True)
            return
        
        await ctx.defer()
        message = await ctx.followup.send("Checking server status...", wait=True)
        try:
            headers = {"Authorization": f"Bearer {EXAROTON_KEY}"}
            response = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}", headers=headers)
            server = response.json()
            print(server)
            status = server["data"]["status"]
            print("Checking server status...")
            print(status)
            while status != 0 and status != 1:
                await message.edit(content="Server is processing, waiting...")
                print("Server is processing, waiting...")
                time.sleep(15)
                server = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}", headers=headers)
                status = server.json()["data"]["status"]
            if status == 1:       
                server = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}", headers=headers)
                onlineplayers = server.json()["data"]["players"]["count"]
                
                if onlineplayers != 0:
                    for i in range(1, 6):
                        command = f"/say §cATTENTION: The server needs to perform an update and will stop in {6 - i} minutes. Please get to a safe spot and logout before this."
                        commandreq = requests.post(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}/command", headers=headers, json={"command": command})
                        print(commandreq.json())
                        await message.edit(content=f"The server is currently online. The server will stop in {6 - i} minutes to give time for players to logout.")
                        time.sleep(60)
                        server = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}", headers=headers)
                        onlineplayers = server.json()["data"]["players"]["count"]
                        if onlineplayers == 0:
                            break

                await message.edit(content="Server is online, stopping...")        
                print("Server is online, stopping...")
                stopreq = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}/stop", headers=headers)
                time.sleep(10)
                server = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}", headers=headers)
                status = server.json()["data"]["status"]
                while status != 0:
                    await message.edit(content="Server is still online, waiting...")
                    print("Server is still online, waiting...")
                    time.sleep(15)
                    server = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}", headers=headers)
                    status = server.json()["data"]["status"]

            await message.edit(content="Server is offline, downloading Geyser update file...")
            print("Server is offline, downloading Geyser update file")
            
            updateFile = requests.get("https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/spigot")
            if updateFile.status_code != 200:
                print("Failed to download file")
                await message.edit(content="Failed to download file! Please try again.")
                return
            
            print(updateFile.headers)
            await message.edit(content="Downloaded file, uploading to server...")
            print("Downloaded file, uploading to server...")
            
            response = requests.put(
                f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}/files/data/plugins/Geyser-Spigot.jar",
                data=updateFile.content,
                headers={
                    "Authorization": f"Bearer {EXAROTON_KEY}",
                    "Content-Type": "application/octet-stream"
                }
            )        
            if response.status_code != 200:
                print(response.json())
                print("Failed to upload file")
                await message.edit(content="Failed to upload file! Please try again.")
                return
            print("File uploaded successfully")
            await message.edit(content="Geyser updated!")
        except Exception as e:
            print(e.with_traceback())
            await message.edit(content="Something went wrong! Please try again.")