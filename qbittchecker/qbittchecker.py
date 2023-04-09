from redbot.core import commands
import aiohttp
import discord
import os

QB_URL = os.environ.get('QBITTORRENT_URL')
QB_USERNAME = os.environ.get('QBITTORRENT_USERNAME')
QB_PASSWORD = os.environ.get('QBITTORRENT_PASSWORD')
HEADERS = {'Referer': QB_URL}


class QbittChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def login(self) -> dict:
        """
        Logs in to qBittorrent and returns the cookies.

        :return: A dictionary containing the cookies.
        :raises Exception: If authentication fails.
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f'{QB_URL}/api/v2/auth/login', data={
                    'username': QB_USERNAME,
                    'password': QB_PASSWORD
                }, headers=HEADERS) as response:
                    if response.status == 401:
                        raise Exception(
                            "Authentication failed: Incorrect credentials")
                    elif response.status != 200:
                        raise Exception(
                            f"Failed to authenticate with qBittorrent: {response.status}")
                    cookies = session.cookie_jar.filter_cookies(QB_URL)
                    return cookies
            except aiohttp.ClientError as e:
                raise Exception(f"An error occurred while logging in: {e}")

    async def get_torrents(self, cookies: dict) -> list:
        """
        Retrieves torrents from qBittorrent client.

        :param cookies: A dictionary containing the cookies.
        :return: A list of dictionaries containing torrent information.
        """
        jar = aiohttp.CookieJar()
        jar.update_cookies(cookies)
        async with aiohttp.ClientSession(cookie_jar=jar) as session:
            try:
                async with session.get(f'{QB_URL}/api/v2/torrents/info', headers=HEADERS) as response:
                    torrents = await response.json()
                    return torrents
            except aiohttp.ClientError as e:
                raise Exception(
                    f"Error retrieving torrents from qBittorrent client: {str(e)}")

    @commands.command()
    async def downloads(self, ctx: discord.ext.commands.Context) -> None:
        """
        Retrieves torrents from qBittorrent client and sends an embed with their status.

        :param ctx: The context in which the command was invoked.
        """
        cookies = await self.login()
        torrents = await self.get_torrents(cookies)

        if not torrents:
            await ctx.send("Error retrieving torrents from qBittorrent client.")
            return

        # Filter torrents by status
        downloading = [
            torrent for torrent in torrents if torrent['state'] == "downloading"]
        stalled = [
            torrent for torrent in torrents if torrent['state'] == "stalledDL"]
        errored = [
            torrent for torrent in torrents if torrent['state'] == "errored"]

        # Create embed
        embed = discord.Embed(color=0x6AA84F)

        def truncate_name(name, max_length=35):
            return name[:max_length] + ('...' if len(name) > max_length else '')

        def add_field(embed, name, value):
            embed.add_field(name=name, value=value, inline=False)

        # Add errored section
        if errored:
            value = '\n'.join(
                [f"```{truncate_name(torrent['name'])}```" for torrent in errored[:5]])
            add_field(embed, ':no_entry:  Errored', value)

        # Add stalled section
        if stalled:
            value = '\n'.join(
                [f"```{truncate_name(torrent['name'])}\
                    {torrent['num_seeds']} seeds - stalled at {torrent['progress'] * 100:.2f}%```" for torrent in stalled[:5]])
            add_field(embed, ':warning:  Stalled Downloads', value)

        # Add downloading section
        if downloading:
            value = '\n'.join(
                [f"```{truncate_name(torrent['name'])}\
                    {torrent['num_seeds']} seeds - {torrent['progress'] * 100:.2f}% - {torrent['eta'] // 3600}h {(torrent['eta'] % 3600) // 60}m remaining```" for torrent in downloading[:5]])
            add_field(embed, ':white_check_mark:  Downloading', value)

        # Add footer only if no torrents are found
        if not errored and not stalled and not downloading:
            embed.set_footer(
                text="If your download isn't listed here, it was either not found or stopped by my filters. Let me know and I'll look in to it!")

        await ctx.send(embed=embed)
