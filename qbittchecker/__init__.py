from .qbittchecker import QbittChecker


def setup(bot):
    bot.add_cog(QbittChecker(bot))