import discord
import logging

class AntiNukeActions:
    def __init__(self, bot):
        self.bot = bot

    async def get_channel_snapshot(self, channel: discord.abc.GuildChannel):
        snapshot = {
            'id': channel.id,
            'name': channel.name,
            'type': str(channel.type),
            'category_id': channel.category_id,
            'position': channel.position,
            'overwrites': {target.id: dict(overwrite) for target, overwrite in channel.overwrites.items()}
        }
        
        if isinstance(channel, discord.TextChannel):
            snapshot['topic'] = channel.topic
            snapshot['slowmode_delay'] = channel.slowmode_delay
            snapshot['nsfw'] = channel.nsfw
        
        return snapshot

    async def get_role_snapshot(self, role: discord.Role):
        return {
            'id': role.id,
            'name': role.name,
            'permissions': role.permissions.value,
            'color': role.color.value,
            'hoist': role.hoist,
            'mentionable': role.mentionable,
            'position': role.position
        }

    async def ban(self, guild, user, reason):
        if user.id == guild.owner_id:
            return False, "Cannot ban guild owner"
        if user.top_role >= guild.me.top_role:
            return False, "User has higher or equal role than bot"
        
        try:
            await guild.ban(user, reason=reason)
            return True, "User banned"
        except Exception as e:
            logging.error(f"Failed to ban user {user.id}: {e}")
            return False, str(e)

    async def strip_dangerous_roles(self, guild, user):
        dangerous_permissions = {
            "administrator", "manage_guild", "manage_roles", "manage_channels",
            "ban_members", "kick_members", "manage_webhooks"
        }
        
        roles_to_remove = [r for r in user.roles if any(getattr(r.permissions, p, False) for p in dangerous_permissions) and r < guild.me.top_role]
        
        if roles_to_remove:
            try:
                await user.remove_roles(*roles_to_remove, reason="Anti-Nuke: Dangerous roles removed")
                return True, f"Removed {len(roles_to_remove)} dangerous roles"
            except Exception as e:
                return False, str(e)
        return True, "No dangerous roles to remove"

    async def rollback_channel(self, guild, channel_data):
        try:
            # Reconstruct overwrites carefully. Some IDs might be gone.
            overwrites = {}
            for target_id, perms in channel_data['overwrites'].items():
                target = guild.get_role(target_id) or guild.get_member(target_id)
                if target:
                    overwrites[target] = discord.PermissionOverwrite(**perms)

            if channel_data['type'] == 'text':
                await guild.create_text_channel(
                    name=channel_data['name'],
                    category=guild.get_channel(channel_data['category_id']),
                    position=channel_data['position'],
                    topic=channel_data['topic'],
                    slowmode_delay=channel_data['slowmode_delay'],
                    nsfw=channel_data['nsfw'],
                    overwrites=overwrites
                )
            return True, "Channel restored"
        except Exception as e:
            return False, str(e)

    async def rollback_role(self, guild, role_data):
        try:
            await guild.create_role(
                name=role_data['name'],
                permissions=discord.Permissions(role_data['permissions']),
                color=discord.Color(role_data['color']),
                hoist=role_data['hoist'],
                mentionable=role_data['mentionable']
            )
            return True, "Role restored"
        except Exception as e:
            return False, str(e)
