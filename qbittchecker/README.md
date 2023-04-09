# CoopCogs

### QbittChecker

Make sure in your Qbittorrent webUI you add both your server AND docker container IP to the bypasses on the Web UI tab.

![WebUI bypass in qbittorrent](../images/qBittChecker/webUIbypass.png)

Set the following environment values in your docker container: QBITTORRENT_URL, QBITTORRENT_USERNAME, QBITTORRENT_PASSWORD. Below is a screenshot of what that looks like in an Unraid server.

![unraid environment variables](../images/qBittChecker/Unraid%20variables.png)
