def parse_placeholders(text: str, member):
    if not text:
        return ""

    guild = member.guild

    return (text.replace("{$@user}", member.mention)
                .replace("{$user}", str(member))
                .replace("{$useravatar}", member.display_avatar.url)
                .replace("{$servername}", guild.name)
                .replace("{$memcount}", str(guild.member_count))
                .replace("{$serverbanner}", guild.banner.url if guild.banner else "")
                .replace("{$serveravatar}", guild.icon.url if guild.icon else ""))
