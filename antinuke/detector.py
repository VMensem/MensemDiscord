import discord
import time
import asyncio
from collections import defaultdict
from .actions import AntiNukeActions
from discord.ext import tasks

class AntiNukeDetector:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.actions = AntiNukeActions(bot)
        # {guild_id: {action_type: {user_id: [timestamps]}}}
        self.rate_counters = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self.locks = defaultdict(asyncio.Lock)

    def cog_unload(self):
        self.cleanup_task.cancel()

    @tasks.loop(seconds=60)
    async def cleanup_task(self):
        for guild_id in list(self.rate_counters.keys()):
            for action in list(self.rate_counters[guild_id].keys()):
                for user_id in list(self.rate_counters[guild_id][action].keys()):
                    now = time.time()
                    self.rate_counters[guild_id][action][user_id] = [t for t in self.rate_counters[guild_id][action][user_id] if now - t < 300]
                    if not self.rate_counters[guild_id][action][user_id]:
                        del self.rate_counters[guild_id][action][user_id]
                if not self.rate_counters[guild_id][action]:
                    del self.rate_counters[guild_id][action]
            if not self.rate_counters[guild_id]:
                del self.rate_counters[guild_id]


    async def handle_action(self, guild, action_type, target, executor=None):
        async with self.locks[guild.id]:
            # 1. Get Settings
            settings = await self.db.get_settings(guild.id)
            if not settings or not settings.get('enabled'):
                return

            # 2. Identify executor
            if not executor:
                executor = await self._get_executor(guild, action_type, target)
            
            if not executor or executor.id == self.bot.user.id or executor.id == guild.owner_id:
                return

            # 3. Check Whitelist
            if await self.db.is_whitelisted(guild.id, executor.id):
                return

            # 4. Get Effective Limit (Emergency Mode)
            limit = await self.db.get_limit(guild.id, action_type)
            max_actions = limit['max_actions'] if limit else 5
            window = limit['window_seconds'] if limit else 10
            severity = limit['severity'] if limit else "MEDIUM"
            
            # Apply emergency reduction
            if settings.get('emergency_mode', False):
                max_actions = max(1, max_actions // 2)

            # 5. Update Counter
            now = time.time()
            user_actions = self.rate_counters[guild.id][action_type][executor.id]
            user_actions.append(now)
            self.rate_counters[guild.id][action_type][executor.id] = [t for t in user_actions if now - t < window]
            
            # 6. Check threshold
            if len(self.rate_counters[guild.id][action_type][executor.id]) >= max_actions:
                await self._trigger_action(guild, executor, action_type, len(self.rate_counters[guild.id][action_type][executor.id]), severity, target)
                self.rate_counters[guild.id][action_type][executor.id] = [] # Reset

    async def _trigger_action(self, guild, user, action_type, count, severity, target):
        # 1. Create Incident
        incident = await self.db.add_incident(guild.id, user.id, action_type, severity, count, None, "pending", "pending")
        incident_id = incident['id']
        
        # 2. Mitigation
        action_taken = "warn"
        rollback_status = "not_needed"
        
        if severity in ["HIGH", "CRITICAL"]:
            await self.actions.strip_dangerous_roles(guild, user)
            success, msg = await self.actions.ban(guild, user, reason=f"Anti-Nuke: {action_type} - {severity}")
            action_taken = f"ban: {success} - {msg}"
            
            # 3. Rollback
            if action_type == "CHANNEL_DELETE":
                rollback_status = "unavailable" # Will implement full lookup
        
        # 4. Send Alert
        settings = await self.db.get_settings(guild.id)
        if settings and settings.get('alert_channel_id'):
            alert_channel = guild.get_channel(settings['alert_channel_id'])
            if alert_channel:
                embed = discord.Embed(title="🚨 ANTI-NUKE INCIDENT", color=discord.Color.red())
                embed.add_field(name="Incident ID", value=f"#{incident_id}")
                embed.add_field(name="Executor", value=f"{user.mention} ({user.id})")
                embed.add_field(name="Action", value=action_type)
                embed.add_field(name="Severity", value=severity)
                embed.add_field(name="Action Taken", value=action_taken)
                embed.add_field(name="Rollback", value=rollback_status)
                await alert_channel.send(embed=embed)
        
    async def _get_executor(self, guild, action_type, target):
        action_map = {
            "CHANNEL_CREATE": discord.AuditLogAction.channel_create,
            "CHANNEL_DELETE": discord.AuditLogAction.channel_delete,
            "ROLE_CREATE": discord.AuditLogAction.role_create,
            "ROLE_DELETE": discord.AuditLogAction.role_delete,
            "BAN": discord.AuditLogAction.ban
        }
        
        if action_type not in action_map:
            return None

        # Short retry loop for Audit Log
        for _ in range(3):
            try:
                async for entry in guild.audit_logs(limit=3, action=action_map[action_type]):
                    if (time.time() - entry.created_at.timestamp()) < 10:
                        if entry.target and entry.target.id == target.id:
                            return entry.user
            except discord.Forbidden:
                return None
            await asyncio.sleep(0.5)
        return None
