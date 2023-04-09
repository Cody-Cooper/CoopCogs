from redbot.core import commands
import aiohttp
import discord


class QbittChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # URL of your qBittorrent client WebUI
        self.qbittorrent_url = 'http://192.168.1.68:8800'
        self.qbittorrent_username = 'admin'  # Your qBittorrent username
        self.qbittorrent_password = 'adminadmin'  # Your qBittorrent password

    async def login(self):
        headers = {'Referer': self.qbittorrent_url}
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.qbittorrent_url}/api/v2/auth/login', data={
                'username': self.qbittorrent_username,
                'password': self.qbittorrent_password
            }, headers=headers) as response:
                if response.status != 200:
                    raise Exception(
                        f"Failed to authenticate with qBittorrent: {response.status}")
                print(f"Status code: {response.status}")
                print(f"Response content: {await response.text()}")
                cookies = session.cookie_jar.filter_cookies(
                    self.qbittorrent_url)
                return cookies

    async def get_torrents(self, cookies):
        print("get_torrents called")
        jar = aiohttp.CookieJar()
        jar.update_cookies(cookies)
        headers = {'Referer': self.qbittorrent_url}
        async with aiohttp.ClientSession(cookie_jar=jar) as session:
            try:
                async with session.get(f'{self.qbittorrent_url}/api/v2/torrents/info', headers=headers) as response:
                    torrents = await response.json()
                    return torrents
            except Exception as e:
                print(
                    f"Error retrieving torrents from qBittorrent client: {str(e)}")
                return None

    @commands.command()
    async def downloads(self, ctx):
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

        # Add errored section
        if errored:
            value = "\n".join(
                [f"{torrent['name'][:35] + ('...' if len(torrent['name']) > 35 else '')}\n" for torrent in errored[:5]])
            embed.add_field(name="Errored", value=value, inline=False)
        else:
            embed.add_field(
                name="Errored", value="No errors!", inline=False)

        # Add stalled section
        if stalled:
            value = "\n".join(
                [f"{torrent['name'][:35] + ('...' if len(torrent['name']) > 35 else '')}\n{torrent['num_seeds']} seeds - stalled at {torrent['progress'] * 100:.2f}%" for torrent in stalled[:5]])
            embed.add_field(name="Stalled Downloads",
                            value=value, inline=False)
        else:
            embed.add_field(
                name="Stalled Downloads", value="Nothing stalled!", inline=False)

        # Add downloading section
        if downloading:
            value = "\n".join(
                [f"{torrent['name'][:35] + ('...' if len(torrent['name']) > 35 else '')}\n{torrent['num_seeds']} seeds - {torrent['progress'] * 100:.2f}% - {torrent['eta'] // 3600}h {(torrent['eta'] % 3600) // 60}m reamining\n" for torrent in downloading[:5]])
            embed.add_field(name="Downloading", value=value, inline=False)
        else:
            embed.add_field(
                name="Downloading", value="Nothing downloading currently!", inline=False)

        await ctx.send(embed=embed)
