from redbot.core import commands
import requests

class qBittorrentStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def qbstatus(self, ctx):
        """Check the status of downloads in qBittorrent"""
        # Set the URL to your qBittorrent WebUI
        url = "http://192.168.1.68:8080/api/v2/torrents/info"

        # Set your qBittorrent username and password
        username = "admin"
        password = "adminadmin"

        # Send a request to the qBittorrent WebUI to get the list of torrents
        response = requests.get(url, auth=(username, password))

        # Check if the request was successful
        if response.status_code == 200:
            # Get the list of torrents from the response
            torrents = response.json()

            # Create a message with the status of each torrent
            message = ""
            for torrent in torrents:
                message += f"{torrent['name']} - {torrent['state']}\\n"

            # Send the message to Discord
            await ctx.send(message)
        else:
            # If the request was not successful, send an error message
            await ctx.send("Error: Could not connect to qBittorrent WebUI")