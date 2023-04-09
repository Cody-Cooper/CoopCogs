from redbot.core import commands
import aiohttp
import logging
from typing import Any, Dict, List
import discord
import os

logging.basicConfig(level=logging.INFO)


class QbittChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.qbittorrent_url = os.environ.get('QBITTORRENT_URL')
        self.qbittorrent_username = os.environ.get('QBITTORRENT_USERNAME')
        self.qbittorrent_password = os.environ.get('QBITTORRENT_PASSWORD')

    async def login(self) -> Dict[str, str]:
        """
        Logs in to qBittorrent and returns the cookies.

        :return: A dictionary containing the cookies.
        :raises Exception: If authentication fails.
        """
        headers = {'Referer': self.qbittorrent_url}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f'{self.qbittorrent_url}/api/v2/auth/login', data={
                    'username': self.qbittorrent_username,
                    'password': self.qbittorrent_password
                }, headers=headers) as response:
                    if response.status == 401:
                        raise Exception(
                            "Authentication failed: Incorrect credentials")
                    elif response.status != 200:
                        raise Exception(
                            f"Failed to authenticate with qBittorrent: {response.status}")
                    logging.info(f"Status code: {response.status}")
                    logging.info(f"Response content: {await response.text()}")
                    cookies = session.cookie_jar.filter_cookies(
                        self.qbittorrent_url)
                    return cookies
            except Exception as e:
                logging.error(f"An error occurred while logging in: {e}")
                raise

    async def get_torrents(self, cookies: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Retrieves torrents from qBittorrent client.

        :param cookies: A dictionary containing the cookies.
        :return: A list of dictionaries containing torrent information.
        """
        logging.info("get_torrents called")
        jar = aiohttp.CookieJar()
        jar.update_cookies(cookies)
        headers = {'Referer': self.qbittorrent_url}
        async with aiohttp.ClientSession(cookie_jar=jar) as session:
            try:
                async with session.get(f'{self.qbittorrent_url}/api/v2/torrents/info', headers=headers) as response:
                    torrents = await response.json()
                    return torrents
            except Exception as e:
                logging.error(
                    f"Error retrieving torrents from qBittorrent client: {str(e)}")
                return None

    @commands.command()
    async def downloads(self, ctx: Any) -> None:
        """
        Retrieves torrents from qBittorrent client and sends an embed with their status.

        :param ctx: The context in which the command was invoked.
        """
        cookies = await self.login()
        torrents = await self.get_torrents(cookies)

        if torrents is None:
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
        embed = discord.Embed(title=f'qBittorrent Downloads', color=0x6AA84F)

        def truncate_name(name, max_length=35):
            return name[:max_length] + ('...' if len(name) > max_length else '')

        def add_field(embed, name, value):
            embed.add_field(name=name, value=value, inline=False)

        # Add errored section
        if errored:
            value = "\n".join(
                [f"{truncate_name(torrent['name'])}\n" for torrent in errored[:5]])
            add_field(embed, "Errored", value)
        else:
            add_field(embed, "Errored", "No errors!")

        # Add stalled section
        if stalled:
            value = "\n".join(
                [f"{truncate_name(torrent['name'])}\n{torrent['num_seeds']} seeds - stalled at {torrent['progress'] * 100:.2f}%" for torrent in stalled[:5]])
            add_field(embed, "Stalled Downloads", value)
        else:
            add_field(embed, "Stalled Downloads", "Nothing stalled!")

        # Add downloading section
        if downloading:
            value = "\n".join(
                [f"{truncate_name(torrent['name'])}\n{torrent['num_seeds']} seeds - {torrent['progress'] * 100:.2f}% - {torrent['eta'] // 3600}h {(torrent['eta'] % 3600) // 60}m remaining\n" for torrent in downloading[:5]])
            add_field(embed, "Downloading", value)
        else:
            add_field(embed, "Downloading", "Nothing downloading currently!")

        await ctx.send(embed=embed)
