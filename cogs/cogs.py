"""The bot's cog and gear manipulator."""
import asyncio
import os
from datetime import datetime
from fnmatch import filter
from convert_to_old_syntax import cur_dir
import util.commands as commands
from util.perms import or_check_perms
from util.const import essential_cogs
from .cog import Cog

class Cogs(Cog):
    """Nice and useful commands to maintain me. 😄
    Don't pull too many gears, or I might die! 😭"""

    @commands.group(pass_context=True, aliases=['cogs', 'module', 'modules'])
    async def cog(self, ctx):
        """Manage all of my cogs and gears.
        Usage: cog {stuff}"""
        await or_check_perms(ctx, ['bot_owner'])
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @cog.command(name='list')
    async def cog_list(self):
        """List all cogs available.
        Usage: cog list"""
        key = '\n+ '
        clist = '''```diff
- Available (Default){key}{0}
----------------------------------------------
- Available (Downloaded){key}{1}
----------------------------------------------
- Loaded{key}{2}
----------------------------------------------
- Disabled{key}{3}
----------------------------------------------
- Enabled{key}{4}```'''
        def_cogs = [c.replace('.py', '').replace('_', ' ').title() for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        try:
            dl_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'downloaded_cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        except OSError:
            dl_cogs = ['None! 😦']
        dis_cogs = [c.replace('_', ' ').title() for c in self.bot.disabled_cogs if c != '']
        enb_cogs = [c.replace('_', ' ').title() for c in self.bot.enabled_cogs if c != '']
        if not dl_cogs:
            dl_cogs = ['None! 😦']
        if not dis_cogs:
            dis_cogs = ['None! 😃']
        if not enb_cogs:
            enb_cogs = ['None! 😦']
        loaded_cogs = self.bot.cogs.keys()
        await self.bot.say(clist.format(*[key.join(l) for l in [def_cogs, dl_cogs, loaded_cogs, dis_cogs, enb_cogs]], key=key))

    @cog.command(name='reload', pass_context=True)
    async def cog_reload(self, ctx, *, cog_name: str):
        """Reload a cog and turn some gears.
        Usage: cog reload [cog name]"""
        def_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        dl_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        cogs = def_cogs + dl_cogs + ['all']
        req_cog = cog_name.lower().replace(' ', '_')
        if req_cog in cogs:
            start_time = datetime.now()
            if 'cogs.' + req_cog in self.bot.extensions:
                status = await self.bot.say(f'**Reloading cog** `{cog_name}` (`{req_cog}`)...')
                self.bot.unload_extension('cogs.' + req_cog)
                self.bot.load_extension('cogs.' + req_cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished reloading cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            elif 'downloaded_cogs.' + req_cog in self.bot.extensions:
                status = await self.bot.say(f'**Reloading cog** `{cog_name}` (`{req_cog}`)...')
                self.bot.unload_extension('downloaded_cogs.' + req_cog)
                self.bot.load_extension('downloaded_cogs.' + req_cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished reloading cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            elif req_cog == 'all':
                status = await self.bot.say('**Reloading all loaded cogs...**')
                for cog in def_cogs:
                    if 'cogs.' + cog in self.bot.extensions:
                        self.bot.unload_extension('cogs.' + cog)
                        self.bot.load_extension('cogs.' + cog)
                for cog in dl_cogs:
                    if 'downloaded_cogs.' + cog in self.bot.extensions:
                        self.bot.unload_extension('downloaded_cogs.' + cog)
                        self.bot.load_extension('downloaded_cogs.' + cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished reloading all loaded cogs!** (took {time_taken}s)')
            else:
                await self.bot.say('**That cog isn\'t already loaded, so I\'ll load it.**')
                self.cog_load.invoke(ctx)
        else:
            await self.bot.say(f'**No such cog! Try** `{ctx.prefix}cog list`**.**')
            return False

    @cog.command(name='load', pass_context=True, aliases=['activate', 'enactivate', 'inactivate']) # idek but lets be safe ¯\_(ツ)_/¯
    async def cog_load(self, ctx, *, cog_name: str):
        """Load a cog and polish some gears.
        Usage: cog load [cog name]"""
        def_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        dl_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        cogs = def_cogs + dl_cogs + ['all']
        req_cog = cog_name.lower().replace(' ', '_')
        if req_cog in cogs:
            start_time = datetime.now()
            if req_cog in [c.lower() for c in self.bot.cogs.keys()]:
                await self.bot.say(f'**Cog** `{cog_name}` (`{req_cog}`) **already loaded!**')
                return False
            elif req_cog in def_cogs:
                status = await self.bot.say(f'**Loading cog** `{cog_name}` (`{req_cog}`)...')
                self.bot.load_extension('cogs.' + req_cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished loading cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            elif req_cog in dl_cogs:
                status = await self.bot.say(f'**Loading cog** `{cog_name}` (`{req_cog}`)...')
                self.bot.load_extension('downloaded_cogs.' + req_cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished loading cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            elif req_cog == 'all':
                status = await self.bot.say('**Loading all cogs...**')
                for cog in def_cogs:
                    self.bot.load_extension('cogs.' + cog)
                for cog in dl_cogs:
                    self.bot.load_extension('downloaded_cogs.' + cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished loading all cogs!** (took {time_taken}s)')
        else:
            await self.bot.say(f'**No such cog! Try** `{ctx.prefix}cog list`**.**')
            return False

    @cog.command(name='unload', pass_context=True, aliases=['deactivate', 'unactivate'])
    async def cog_unload(self, ctx, *, cog_name: str):
        """Unload a cog... I don't want to lose gears 😢
        Usage: cog unload [cog name]"""
        def_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        dl_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        cogs = def_cogs + dl_cogs + ['all']
        req_cog = cog_name.lower().replace(' ', '_')
        if req_cog == 'cogs':
            await self.bot.say('**You can\'t unload that!**')
            return
        if req_cog in cogs:
            start_time = datetime.now()
            if 'cogs.' + req_cog in self.bot.extensions:
                status = await self.bot.say(f'**Unloading cog** `{cog_name}` (`{req_cog}`)...')
                self.bot.unload_extension('cogs.' + req_cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished unloading cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            elif 'downloaded_cogs.' + req_cog in self.bot.extensions:
                status = await self.bot.say(f'**Unloading cog** `{cog_name}` (`{req_cog}`)...')
                self.bot.unload_extension('downloaded_cogs.' + req_cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished unloading cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            elif req_cog == 'all':
                status = await self.bot.say('**Unloading all loaded cogs but this...**')
                for cog in def_cogs:
                    if ('cogs.' + cog in self.bot.extensions) and (cog != 'cogs'):
                        self.bot.unload_extension('cogs.' + cog)
                for cog in dl_cogs:
                    if 'downloaded_cogs.' + cog in self.bot.extensions:
                        self.bot.unload_extension('downloaded_cogs.' + cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished unloading all loaded cogs!** (took {time_taken}s)')
            else:
                await self.bot.say(f'**Cog** `{cog_name}` (`{req_cog}`) **not loaded!**')
                return False
        else:
            await self.bot.say(f'**No such cog! Try** `{ctx.prefix}cog list`**.**')
            return False

    @cog.command(name='enable', pass_context=True)
    async def cog_enable(self, ctx, *, cog_name: str):
        """Enable a cog so I load it every future start!
        Usage: cog enable [cog name]"""
        def_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        dl_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        cogs = def_cogs + dl_cogs
        req_cog = cog_name.lower().replace(' ', '_')
        if req_cog in cogs:
            if req_cog in self.bot.enabled_cogs:
                await self.bot.say(f'**Cog** `{cog_name}` (`{req_cog}`) **already enabled!**')
            else:
                start_time = datetime.now()
                status = await self.bot.say(f'**Enabling cog** `{cog_name}` (`{req_cog}`)...')
                if req_cog in self.bot.disabled_cogs:
                    self.bot.disabled_cogs.remove(req_cog)
                    with open(self.bot.dis_cogs_path, 'w+') as f:
                        f.write('\r\n'.join(self.bot.disabled_cogs))
                else:
                    self.bot.enabled_cogs.append(req_cog)
                    with open(self.bot.ex_cogs_path, 'w+') as f:
                        f.write('\r\n'.join(self.bot.enabled_cogs))
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished enabling cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
        else:
            await self.bot.say(f'**No such cog! Try** `{ctx.prefix}cog list`**.**')
            return False

    @cog.command(name='disable', pass_context=True)
    async def cog_disable(self, ctx, *, cog_name: str):
        """Disable a cog so it doesn't load every start.
        Usage: cog disable [cog name]"""
        def_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        dl_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        cogs = def_cogs + dl_cogs
        req_cog = cog_name.lower().replace(' ', '_')
        if req_cog == 'cogs':
            await self.bot.say('**You can\'t disable that!**')
            return
        if req_cog in cogs:
            if (req_cog in self.bot.enabled_cogs) or (req_cog in list(set(essential_cogs) - set(self.bot.disabled_cogs))):
                start_time = datetime.now()
                status = await self.bot.say(f'**Disabling cog** `{cog_name}` (`{req_cog}`)...')
                if req_cog in essential_cogs:
                    self.bot.disabled_cogs.append(req_cog)
                    with open(self.bot.dis_cogs_path, 'w+') as f:
                        f.write('\r\n'.join(self.bot.disabled_cogs))
                else:
                    self.bot.enabled_cogs.remove(req_cog)
                    with open(self.bot.ex_cogs_path, 'w+') as f:
                        f.write('\r\n'.join(self.bot.enabled_cogs))
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished disabling cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            else:
                await self.bot.say(f'**Cog** `{cog_name}` (`{req_cog}`) **not enabled!**')
                return
        else:
            await self.bot.say(f'**No such cog! Try** `{ctx.prefix}cog list`**.**')
            return False

def setup(bot):
    c = Cogs(bot)
    bot.add_cog(c)
