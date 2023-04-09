from redbot.core import commands
import aiohttp

class QbittChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.qbittorrent_url = 'http://192.168.1.68:8800' # URL of your qBittorrent client
        self.qbittorrent_username = 'admin' # Your qBittorrent username
        self.qbittorrent_password = 'adminadmin' # Your qBittorrent password

    async def login(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.qbittorrent_url}/api/v2/auth/login', data={
                'username': self.qbittorrent_username,
                'password': self.qbittorrent_password
            }) as response:
                cookies = session.cookie_jar.filter_cookies(self.qbittorrent_url)
                return cookies

    async def get_torrents(self, cookies):
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(f'{self.qbittorrent_url}/api/v2/torrents/info') as response:
                torrents = await response.json()
                return torrents

    @commands.command()
    async def downloads(self, ctx):
        cookies = await self.login()
        torrents = await self.get_torrents(cookies)

        embed = discord.Embed(title='qBittorrent Downloads', color=0xff0000)
        for torrent in torrents:
            embed.add_field(name=torrent['name'], value=f"Progress: {torrent['progress'] * 100}%")

        await ctx.send(embed=embed)