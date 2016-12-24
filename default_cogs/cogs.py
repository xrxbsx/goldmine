"""The bot's cog and gear manipulator."""
import asyncio
from asyncio import as_completed
import os
from functools import partial
from setuptools import distutils
from datetime import datetime
from fnmatch import filter
from subprocess import run, PIPE
import shutil
from concurrent.futures import ThreadPoolExecutor
from time import time
import discord
from core import set_cog
from convert_to_old_syntax import cur_dir
import util.commands as commands
from util.perms import or_check_perms
from util.const import essential_cogs
from cogs.utils.dataIO import dataIO
from cogs.utils import checks
from cogs.utils.chat_formatting import pagify, box
from .cog import Cog

NUM_THREADS = 4
REPO_NONEX = 0x1
REPO_CLONE = 0x2
REPO_SAME = 0x4

class UpdateError(Exception):
    pass

class CloningError(UpdateError):
    pass

class Cogs(Cog):
    """Nice and useful commands to maintain me. 😄
    Don't pull too many gears, or I might die! 😭"""

    def __init__(self, bot):
        super().__init__(bot)
        self.path = 'data/downloader/'
        self.file_path = 'data/downloader/repos.json'
        # {name:{url,cog1:{installed},cog1:{installed}}}
        self.repos = dataIO.load_json(self.file_path)
        self.executor = ThreadPoolExecutor(NUM_THREADS)
        self._do_first_run()

    def save_repos(self):
        dataIO.save_json(self.file_path, self.repos)

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
        def_cogs = [c.replace('.py', '').replace('_', ' ').title() for c in filter(os.listdir(os.path.join(cur_dir, 'default_cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        try:
            dl_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        except OSError:
            dl_cogs = ['None! 😦']
        dis_cogs = [c.replace('_', ' ').title() for c in self.bot.disabled_cogs if c != '']
        essential_enb = essential_cogs
        for cog in self.bot.disabled_cogs:
            if cog in essential_enb:
                essential_enb.remove(cog)
        if not dl_cogs:
            dl_cogs = ['None! 😦']
        if not dis_cogs:
            dis_cogs = ['None! 😃']
        enb_cogs = [c.replace('_', ' ').title() for c in self.bot.enabled_cogs if c != ''] + essential_enb
        enb_cogs += essential_enb
        loaded_cogs = self.bot.cogs.keys()
        await self.bot.say(clist.format(*[key.join(l) for l in [def_cogs, dl_cogs, loaded_cogs, dis_cogs, enb_cogs]], key=key))

    @cog.command(name='reload', pass_context=True)
    async def cog_reload(self, ctx, *, cog_name: str):
        """Reload a cog and turn some gears.
        Usage: cog reload [cog name]"""
        def_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'default_cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        dl_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        cogs = def_cogs + dl_cogs + ['all']
        req_cog = cog_name.lower().replace(' ', '_')
        if req_cog in cogs:
            start_time = datetime.now()
            if 'default_cogs.' + req_cog in self.bot.extensions:
                status = await self.bot.say(f'**Reloading cog** `{cog_name}` (`{req_cog}`)...')
                self.bot.unload_extension('default_cogs.' + req_cog)
                self.bot.load_extension('default_cogs.' + req_cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished reloading cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            elif 'cogs.' + req_cog in self.bot.extensions:
                status = await self.bot.say(f'**Reloading cog** `{cog_name}` (`{req_cog}`)...')
                self.bot.unload_extension('cogs.' + req_cog)
                self.bot.load_extension('cogs.' + req_cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished reloading cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            elif req_cog == 'all':
                status = await self.bot.say('**Reloading all loaded cogs...**')
                for cog in def_cogs:
                    if 'default_cogs.' + cog in self.bot.extensions:
                        self.bot.unload_extension('default_cogs.' + cog)
                        self.bot.load_extension('default_cogs.' + cog)
                for cog in dl_cogs:
                    if 'cogs.' + cog in self.bot.extensions:
                        self.bot.unload_extension('cogs.' + cog)
                        self.bot.load_extension('cogs.' + cog)
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
        def_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'default_cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
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
                self.bot.load_extension('default_cogs.' + req_cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished loading cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            elif req_cog in dl_cogs:
                status = await self.bot.say(f'**Loading cog** `{cog_name}` (`{req_cog}`)...')
                self.bot.load_extension('cogs.' + req_cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished loading cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            elif req_cog == 'all':
                status = await self.bot.say('**Loading all cogs...**')
                for cog in def_cogs:
                    self.bot.load_extension('default_cogs.' + cog)
                for cog in dl_cogs:
                    self.bot.load_extension('cogs.' + cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished loading all cogs!** (took {time_taken}s)')
        else:
            await self.bot.say(f'**No such cog! Try** `{ctx.prefix}cog list`**.**')
            return False

    @cog.command(name='unload', pass_context=True, aliases=['deactivate', 'unactivate'])
    async def cog_unload(self, ctx, *, cog_name: str):
        """Unload a cog... I don't want to lose gears 😢
        Usage: cog unload [cog name]"""
        def_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'default_cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        dl_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
        cogs = def_cogs + dl_cogs + ['all']
        req_cog = cog_name.lower().replace(' ', '_')
        if req_cog == 'cogs':
            await self.bot.say('**You can\'t unload that!**')
            return
        if req_cog in cogs:
            start_time = datetime.now()
            if 'default_cogs.' + req_cog in self.bot.extensions:
                status = await self.bot.say(f'**Unloading cog** `{cog_name}` (`{req_cog}`)...')
                self.bot.unload_extension('default_cogs.' + req_cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished unloading cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            elif 'cogs.' + req_cog in self.bot.extensions:
                status = await self.bot.say(f'**Unloading cog** `{cog_name}` (`{req_cog}`)...')
                self.bot.unload_extension('cogs.' + req_cog)
                time_taken = round((datetime.now() - start_time).total_seconds(), 3)
                await self.bot.edit_message(status, f'**Finished unloading cog** `{cog_name}` (`{req_cog}`)**!** (took {time_taken}s)')
            elif req_cog == 'all':
                status = await self.bot.say('**Unloading all loaded cogs but this...**')
                for cog in def_cogs:
                    if ('default_cogs.' + cog in self.bot.extensions) and (cog != 'cogs'):
                        self.bot.unload_extension('default_cogs.' + cog)
                for cog in dl_cogs:
                    if 'cogs.' + cog in self.bot.extensions:
                        self.bot.unload_extension('cogs.' + cog)
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
        def_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'default_cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
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
        def_cogs = [c.replace('.py', '') for c in filter(os.listdir(os.path.join(cur_dir, 'default_cogs')), '*.py') if c not in ['__init__.py', 'cog.py']]
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

    @cog.group(pass_context=True)
    async def repo(self, ctx):
        """Repo management commands"""
        if ctx.invoked_subcommand is None or \
                isinstance(ctx.invoked_subcommand, commands.Group):
            await self.bot.send_cmd_help(ctx)
            return

    @repo.command(name="add", pass_context=True)
    async def _repo_add(self, ctx, repo_name: str, repo_url: str):
        """Adds repo to available repo lists

        Warning: Adding 3RD Party Repositories is at your own
        Risk."""
        await self.bot.say("Type 'I agree' to confirm "
                           "adding a 3rd party repo. This has the possibility"
                           " of being harmful. You will not receive help "
                           "or support from Dragon5232 for any cogs "
                           "installed from this repo. If you do require "
                           "support you should contact the owner of this "
                           "repo.\n\nAgain, ANY repo you add is at YOUR"
                           " discretion and the creator of this bot has "
                           "ABSOLUTELY ZERO responsibility to help if "
                           "something goes wrong.")
        answer = await self.bot.wait_for_message(timeout=15,
                                                 author=ctx.message.author)
        if answer is None:
            await self.bot.say('Not adding repo.')
            return
        elif "i agree" not in answer.content.lower():
            await self.bot.say('Not adding repo.')
            return
        self.repos[repo_name] = {}
        self.repos[repo_name]['url'] = repo_url
        try:
            self.update_repo(repo_name)
        except CloningError:
            await self.bot.say("That repository link doesn't seem to be "
                               "valid.")
            del self.repos[repo_name]
            return
        self.populate_list(repo_name)
        self.save_repos()
        data = self.get_info_data(repo_name)
        if data:
            msg = data.get("INSTALL_MSG")
            if msg:
                await self.bot.say(msg[:2000])
        await self.bot.say("Repo '{}' added.".format(repo_name))

    @repo.command(name="remove")
    async def _repo_del(self, repo_name: str):
        """Removes repo from repo list. COGS ARE NOT REMOVED."""
        if repo_name not in self.repos:
            await self.bot.say("That repo doesn't exist.")
            return
        del self.repos[repo_name]
        #shutil.rmtree(os.path.join(self.path, repo_name))
        self.save_repos()
        await self.bot.say("Repo '{}' removed.".format(repo_name))

    @cog.command(name="list")
    async def _send_list(self, repo_name=None):
        """Lists installable cogs"""
        retlist = []
        if repo_name and repo_name in self.repos:
            msg = "Available cogs:\n"
            for cog in sorted(self.repos[repo_name].keys()):
                if 'url' == cog:
                    continue
                data = self.get_info_data(repo_name, cog)
                if data:
                    retlist.append([cog, data.get("SHORT", "")])
                else:
                    retlist.append([cog, ''])
        else:
            msg = "Available repos:\n"
            for repo_name in sorted(self.repos.keys()):
                data = self.get_info_data(repo_name)
                if data:
                    retlist.append([repo_name, data.get("SHORT", "")])
                else:
                    retlist.append([repo_name, ""])

        col_width = max(len(row[0]) for row in retlist) + 2
        for row in retlist:
            msg += "\t" + "".join(word.ljust(col_width) for word in row) + "\n"
        for page in pagify(msg, delims=['\n'], shorten_by=8):
            await self.bot.say(box(page))

    @cog.command()
    async def info(self, repo_name: str, cog: str=None):
        """Shows info about the specified cog"""
        if cog is not None:
            cogs = self.list_cogs(repo_name)
            if cog in cogs:
                data = self.get_info_data(repo_name, cog)
                if data:
                    msg = "{} by {}\n\n".format(cog, data["AUTHOR"])
                    msg += data["NAME"] + "\n\n" + data["DESCRIPTION"]
                    await self.bot.say(box(msg))
                else:
                    await self.bot.say("The specified cog has no info file.")
            else:
                await self.bot.say("That cog doesn't exist."
                                   " Use cog list to see the full list.")
        else:
            data = self.get_info_data(repo_name)
            if data is None:
                await self.bot.say("That repo does not exist or the"
                                   " information file is missing for that repo"
                                   ".")
                return
            name = data.get("NAME", None)
            name = repo_name if name is None else name
            author = data.get("AUTHOR", "Unknown")
            desc = data.get("DESCRIPTION", "")
            msg = ("```{} by {}```\n\n{}".format(name, author, desc))
            await self.bot.say(msg)

    @cog.command(pass_context=True)
    async def update(self, ctx):
        """Updates cogs."""

        tasknum = 0
        num_repos = len(self.repos)

        min_dt = 0.5
        burst_inc = 0.1/(NUM_THREADS)
        touch_n = tasknum
        touch_t = time()

        def regulate(touch_t, touch_n):
            dt = time() - touch_t
            if dt + burst_inc*(touch_n) > min_dt:
                touch_n = 0
                touch_t = time()
                return True, touch_t, touch_n
            return False, touch_t, touch_n + 1

        tasks = []
        for r in self.repos:
            task = partial(self.update_repo, r)
            task = self.bot.loop.run_in_executor(self.executor, task)
            tasks.append(task)

        base_msg = 'Downloading updated cogs, please wait... '
        status = f' {task_num}/{num_repos} repos updated'
        msg = await self.bot.say(base_msg + status)

        updated_cogs = []
        new_cogs = []
        deleted_cogs = []
        error_repos = {}
        installed_updated_cogs = []

        for f in as_completed(tasks):
            tasknum += 1
            try:
                name, updates, oldhash = await f
                if updates:
                    if type(updates) is dict:
                        for k, l in updates.items():
                            tl = [(name, c, oldhash) for c in l]
                            if k == 'A':
                                new_cogs.extend(tl)
                            elif k == 'D':
                                deleted_cogs.extend(tl)
                            elif k == 'M':
                                updated_cogs.extend(tl)
            except UpdateError as e:
                name, what = e.args
                error_repos[name] = what
            edit, touch_t, touch_n = regulate(touch_t, touch_n)
            if edit:
                status = f' {task_num}/{num_repos} repos updated'
                msg = await self._robust_edit(msg, base_msg + status)
        status = 'done. '

        if not any(self.repos[repo][cog]['INSTALLED'] for
                   repo, cog, _ in updated_cogs):
            status += ' No updates to apply. '

        if new_cogs:
            status += '\nNew cogs: ' \
                   + ', '.join('%s/%s' % c[:2] for c in new_cogs) + '.'
        if deleted_cogs:
            status += '\nDeleted cogs: ' \
                   + ', '.join('%s/%s' % c[:2] for c in deleted_cogs) + '.'
        if updated_cogs:
            status += '\nUpdated cogs: ' \
                   + ', '.join('%s/%s' % c[:2] for c in updated_cogs) + '.'
        if error_repos:
            status += '\nThe following repos failed to update: '
            for n, what in error_repos.items():
                status += '\n%s: %s' % (n, what)

        msg = await self._robust_edit(msg, base_msg + status)

        registry = dataIO.load_json("data/cogs.json")

        for t in updated_cogs:
            repo, cog, _ = t
            if (self.repos[repo][cog]['INSTALLED'] and
                    registry.get('cogs.' + cog, False)):
                installed_updated_cogs.append(t)
                await self.install(repo, cog)

        if not installed_updated_cogs:
            return

        patchnote_lang = 'Prolog'
        shorten_by = 8 + len(patchnote_lang)
        for note in self.patch_notes_handler(installed_updated_cogs):
            if note is None:
                continue
            for page in pagify(note, delims=['\n'], shorten_by=shorten_by):
                await self.bot.say(box(page, patchnote_lang))

        await self.bot.say("Cogs updated. Reload updated cogs? (yes/no)")
        answer = await self.bot.wait_for_message(timeout=15,
                                                 author=ctx.message.author)
        if answer is None:
            await self.bot.say("Ok then, you can reload cogs with"
                               " `{}reload <cog_name>`".format(ctx.prefix))
        elif answer.content.lower().strip() == "yes":
            update_list = []
            fail_list = []
            for repo, cog, _ in installed_updated_cogs:
                try:
                    self.bot.unload_extension("cogs." + cog)
                    self.bot.load_extension("cogs." + cog)
                    update_list.append(cog)
                except:
                    fail_list.append(cog)
            msg = 'Done.'
            if update_list:
                msg += " The following cogs were reloaded: "\
                    + ', '.join(update_list) + "\n"
            if fail_list:
                msg += " The following cogs failed to reload: "\
                    + ', '.join(fail_list)
            await self.bot.say(msg)

        else:
            await self.bot.say("Ok then, you can reload cogs with"
                               " `{}reload <cog_name>`".format(ctx.prefix))

    def patch_notes_handler(self, repo_cog_hash_pairs):
        for repo, cog, oldhash in repo_cog_hash_pairs:
            pathsplit = self.repos[repo][cog]['file'].split('/')
            repo_path = os.path.join(*pathsplit[:-2])
            cogfile = os.path.join(*pathsplit[-2:])
            cmd = ["git", "-C", repo_path, "log", "--relative-date",
                   "--reverse", oldhash + '..', cogfile
                   ]
            try:
                log = run(cmd, stdout=PIPE).stdout.decode().strip()
                yield self.format_patch(repo, cog, log)
            except:
                pass

    @cog.command(pass_context=True)
    async def uninstall(self, ctx, repo_name, cog):
        """Uninstalls a cog"""
        if repo_name not in self.repos:
            await self.bot.say("That repo doesn't exist.")
            return
        if cog not in self.repos[repo_name]:
            await self.bot.say("That cog isn't available from that repo.")
            return
        set_cog("cogs." + cog, False)
        self.repos[repo_name][cog]['INSTALLED'] = False
        self.save_repos()
        os.remove(os.path.join("cogs", cog + ".py"))
        await self.bot.say("Cog successfully uninstalled.")

    @cog.command(name="install", pass_context=True)
    async def _install(self, ctx, repo_name: str, cog: str):
        """Installs specified cog"""
        if repo_name not in self.repos:
            await self.bot.say("That repo doesn't exist.")
            return
        if cog not in self.repos[repo_name]:
            await self.bot.say("That cog isn't available from that repo.")
            return
        install_cog = await self.install(repo_name, cog)
        data = self.get_info_data(repo_name, cog)
        if data is not None:
            install_msg = data.get("INSTALL_MSG", None)
            if install_msg:
                await self.bot.say(install_msg[:2000])
        if install_cog:
            await self.bot.say("Installation completed. Load it now? (yes/no)")
            answer = await self.bot.wait_for_message(timeout=15,
                                                     author=ctx.message.author)
            if answer is None:
                await self.bot.say("Ok then, you can load it with"
                                   " `{}load {}`".format(ctx.prefix, cog))
            elif answer.content.lower().strip() == "yes":
                set_cog("cogs." + cog, True)
                await self.
            else:
                await self.bot.say("Ok then, you can load it with"
                                   " `{}load {}`".format(ctx.prefix, cog))
        elif install_cog is False:
            await self.bot.say("Invalid cog. Installation aborted.")
        else:
            await self.bot.say("That cog doesn't exist. Use cog list to see"
                               " the full list.")

    async def install(self, repo_name, cog):
        if cog.endswith('.py'):
            cog = cog[:-3]

        path = self.repos[repo_name][cog]['file']
        cog_folder_path = self.repos[repo_name][cog]['folder']
        cog_data_path = os.path.join(cog_folder_path, 'data')

        to_path = os.path.join("cogs/", cog + ".py")

        print("Copying {}...".format(cog))
        shutil.copy(path, to_path)

        if os.path.exists(cog_data_path):
            print("Copying {}'s data folder...".format(cog))
            distutils.dir_util.copy_tree(cog_data_path,
                                         os.path.join('data/', cog))
        self.repos[repo_name][cog]['INSTALLED'] = True
        self.save_repos()
        return True

    def get_info_data(self, repo_name, cog=None):
        if cog is not None:
            cogs = self.list_cogs(repo_name)
            if cog in cogs:
                info_file = os.path.join(cogs[cog].get('folder'), "info.json")
                if os.path.isfile(info_file):
                    try:
                        data = dataIO.load_json(info_file)
                    except:
                        return None
                    return data
        else:
            repo_info = os.path.join(self.path, repo_name, 'info.json')
            if os.path.isfile(repo_info):
                try:
                    data = dataIO.load_json(repo_info)
                    return data
                except:
                    return None
        return None

    def list_cogs(self, repo_name):
        valid_cogs = {}

        repo_path = os.path.join(self.path, repo_name)
        folders = [f for f in os.listdir(repo_path)
                   if os.path.isdir(os.path.join(repo_path, f))]
        legacy_path = os.path.join(repo_path, "cogs")
        legacy_folders = []
        if os.path.exists(legacy_path):
            for f in os.listdir(legacy_path):
                if os.path.isdir(os.path.join(legacy_path, f)):
                    legacy_folders.append(os.path.join("cogs", f))

        folders = folders + legacy_folders

        for f in folders:
            cog_folder_path = os.path.join(self.path, repo_name, f)
            cog_folder = os.path.basename(cog_folder_path)
            for cog in os.listdir(cog_folder_path):
                cog_path = os.path.join(cog_folder_path, cog)
                if os.path.isfile(cog_path) and cog_folder == cog[:-3]:
                    valid_cogs[cog[:-3]] = {'folder': cog_folder_path,
                                            'file': cog_path}
        return valid_cogs

    def get_dir_name(self, url):
        splitted = url.split("/")
        git_name = splitted[-1]
        return git_name[:-4]

    def _do_first_run(self):
        invalid = []
        save = False

        for repo in self.repos:
            broken = 'url' in self.repos[repo] and len(self.repos[repo]) == 1
            if broken:
                save = True
                try:
                    self.update_repo(repo)
                    self.populate_list(repo)
                except CloningError:
                    invalid.append(repo)
                    continue
                except Exception as e:
                    print(e) # TODO: Proper logging
                    continue

        for repo in invalid:
            del self.repos[repo]

        if save:
            self.save_repos()

    def populate_list(self, name):
        valid_cogs = self.list_cogs(name)
        new = set(valid_cogs.keys())
        old = set(self.repos[name].keys())
        for cog in new - old:
            self.repos[name][cog] = valid_cogs.get(cog, {})
            self.repos[name][cog]['INSTALLED'] = False
        for cog in new & old:
            self.repos[name][cog].update(valid_cogs[cog])
        for cog in old - new:
            if cog != 'url':
                del self.repos[name][cog]

    def update_repo(self, name):
        try:
            dd = self.path
            if name not in self.repos:
                raise UpdateError("Repo does not exist in data, wtf")
            folder = os.path.join(dd, name)
            # Make sure we don't git reset our folder on accident
            if not os.path.exists(os.path.join(folder, '.git')):
                #if os.path.exists(folder):
                    #shutil.rmtree(folder)
                url = self.repos[name].get('url')
                if not url:
                    raise UpdateError("Need to clone but no URL set")
                p = run(["git", "clone", url, dd + name])
                if p.returncode != 0:
                    raise CloningError()
                self.populate_list(name)
                return name, REPO_CLONE, None
            else:
                rpcmd = ["git", "-C", dd + name, "rev-parse", "HEAD"]
                p = run(["git", "-C", dd + name, "reset", "--hard",
                        "origin/HEAD", "-q"])
                if p.returncode != 0:
                    raise UpdateError("Error resetting to origin/HEAD")
                p = run(rpcmd, stdout=PIPE)
                if p.returncode != 0:
                    raise UpdateError("Unable to determine old commit hash")
                oldhash = p.stdout.decode().strip()
                p = run(["git", "-C", dd + name, "pull", "-q"])
                if p.returncode != 0:
                    raise UpdateError("Error pulling updates")
                p = run(rpcmd, stdout=PIPE)
                if p.returncode != 0:
                    raise UpdateError("Unable to determine new commit hash")
                newhash = p.stdout.decode().strip()
                if oldhash == newhash:
                    return name, REPO_SAME, None
                else:
                    self.populate_list(name)
                    self.save_repos()
                    ret = {}
                    cmd = ['git', '-C', dd + name, 'diff', '--no-commit-id',
                           '--name-status', oldhash, newhash]
                    p = run(cmd, stdout=PIPE)
                    if p.returncode != 0:
                        raise UpdateError("Error in git diff")
                    changed = p.stdout.strip().decode().split('\n')
                    for f in changed:
                        if not f.endswith('.py'):
                            continue
                        status, cogpath = f.split('\t')
                        cogname = os.path.split(cogpath)[-1][:-3]  # strip .py
                        if status not in ret:
                            ret[status] = []
                        ret[status].append(cogname)
                    return name, ret, oldhash
        except CloningError as e:
            raise CloningError(name, *e.args) from None
        except UpdateError as e:
            raise UpdateError(name, *e.args) from None

    async def _robust_edit(self, msg, text):
        try:
            msg = await self.bot.edit_message(msg, text)
        except discord.errors.NotFound:
            msg = await self.bot.send_message(msg.channel, text)
        except:
            raise
        return msg

    @staticmethod
    def format_patch(repo, cog, log):
        header = "Patch Notes for %s/%s" % (repo, cog)
        line = "=" * len(header)
        if log:
            return '\n'.join((header, line, log))

def check_folders():
    if not os.path.exists("data/downloader"):
        print('Making repo downloads folder...')
        os.mkdir('data/downloader')

def check_files():
    repos = \
        {'community': {'url': "https://github.com/Twentysix26/Red-Cogs.git"}}

    f = "data/downloader/repos.json"
    if not dataIO.is_valid_json(f):
        print("Creating default data/downloader/repos.json")
        dataIO.save_json(f, repos)

def setup(bot):
    check_folders()
    check_files()
    c = Cogs(bot)
    bot.add_cog(c)
