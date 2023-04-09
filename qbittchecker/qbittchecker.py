from redbot.core import commands
import aiohttp
import socket


class QbittChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # URL of your qBittorrent client WebUI
        self.qbittorrent_url = 'http://192.168.1.68:8800'
        self.qbittorrent_username = 'admin'  # Your qBittorrent username
        self.qbittorrent_password = 'adminadmin'  # Your qBittorrent password

    async def login(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.qbittorrent_url}/api/v2/auth/login', data={
                'username': self.qbittorrent_username,
                'password': self.qbittorrent_password
            }) as response:
                cookies = session.cookie_jar.filter_cookies(
                    self.qbittorrent_url)
                return cookies

    async def get_torrents(self, cookies):
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(f'{self.qbittorrent_url}/api/v2/torrents/info?filter=downloading') as response:
                body = await response.text()
                print(body)
                torrents = await response.json()
                return torrents

    @commands.command()
    async def downloads(self, ctx):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        cookies = await self.login()
        torrents = await self.get_torrents(cookies)

        embed = discord.Embed(
            title=f'qBittorrent Downloads ({ip_address})', color=0xff0000)
        for torrent in torrents:
            progress = f"{torrent['progress'] * 100:.2f}%"
            status = torrent['state']
            name = torrent['name']
            embed.add_field(
                name=name, value=f"Status: {status}\nProgress: {progress}")

        await ctx.send(embed=embed)
