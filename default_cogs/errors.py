"""Error handlers."""
import traceback
import asyncio
import discord
import util.commands as commands
from util.const import *
from util.func import bdel
from .cog import Cog

arg_err_map = {
    commands.MissingRequiredArgument: 'out enough arguments',
    commands.BadArgument: ' an invalid argument',
    commands.TooManyArguments: ' too many arguments'
}

class Errors(Cog):
    """Error handling gears."""
    def __init__(self, bot):
        self.csend = bot.csend
        self.say = bot.send_message
        self.store = bot.store
        self.user = bot.user
        super().__init__(bot)

    async def on_error(self, ev_name, *ev_args, **ev_kwargs):
        kw_args = ', ' + (', '.join([k + '=' + str(ev_kwargs[k]) for k in ev_kwargs])) if ev_kwargs else ''
        self.logger.error(f'Event handler {ev_name} errored! Called with ' +
                          (', '.join([bdel(str(i), 'Command raised an exception: ') for i in ev_args]) if ev_args else 'nothing') + kw_args)
        traceback.print_exc()

    async def on_command_error(self, exp, ctx):
        try:
            myself = ctx.message.server.me
        except AttributeError:
            myself = self.user
        if self.bot.selfbot:
            try:
                cmdfix = self.store['properties']['global']['selfbot_prefix']
            except KeyError:
                cmdfix = myself.name[0].lower() + '.'
        else:
            cmdfix = await self.store.get_cmdfix(ctx.message)
        cproc = ctx.message.content.split(' ')[0]
        cprocessed = bdel(cproc, cmdfix)
        c_key = str(exp)
        bc_key = bdel(c_key, 'Command raised an exception: ')
        eprefix = 's'
        try:
            cmid = ctx.message.server.id
        except AttributeError:
            cmid = ctx.message.author.id
            eprefix = 'dm'
        if isinstance(exp, commands.CommandNotFound):
            self.logger.error(str(ctx.message.author) + ' in ' + ctx.message.server.name + ': command \'' + cprocessed + '\' not found')
        elif isinstance(exp, commands.CommandInvokeError):
            self.logger.error(str(ctx.message.author) + ' in ' + ctx.message.server.name + f': [cmd {cprocessed}] ' + bc_key)
            traceback.print_exception(type(exp.original), exp.original, exp.original.__traceback__)
            traceback.print_exception(type(exp), exp, exp.__traceback__)
        else:
            self.logger.error(str(ctx.message.author) + ' in ' + ctx.message.server.name + ': ' + str(exp) + ' (%s)' % type(exp).__name__)
            traceback.print_exception(type(exp), exp, exp.__traceback__)
        if isinstance(exp, commands.NoPrivateMessage):
            await self.csend(ctx, npm_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.CommandNotFound):
            pass
        elif isinstance(exp, commands.DisabledCommand):
            await self.csend(ctx, ccd_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.CommandOnCooldown):
            await self.say(exp.ctx.message.author, coc_fmt.format(ctx.message.author, cprocessed, cmdfix, bdel(c_key, 'You are on cooldown. Try again in ')))
        elif isinstance(exp, commands.PassException):
            pass
        elif isinstance(exp, commands.ReturnError):
            await self.csend(ctx, exp.text)
        elif isinstance(exp, commands.CommandPermissionError):
            _perms = ''
            if exp.perms_required:
                perm_list = [i.lower().replace('_', ' ').title() for i in exp.perms_required]
                if len(perm_list) > 1:
                    perm_list[-1] = '**and **' + perm_list[-1] # to cancel bold
                _perms = ', '.join(perm_list)
            else:
                _perms = 'Not specified'
            await self.csend(ctx, cpe_fmt.format(ctx.message.author, cprocessed, cmdfix, _perms))
        elif isinstance(exp, commands.OrCommandPermissionError):
            _perms = ''
            if exp.perms_ok:
                perm_list = [i.lower().replace('_', ' ').title() for i in exp.perms_ok]
                if len(perm_list) > 1:
                    perm_list[-1] = '**or **' + perm_list[-1] # to cancel bold
                _perms = ', '.join(perm_list)
            else:
                _perms = 'Not specified'
            await self.csend(ctx, ocpe_fmt.format(ctx.message.author, cprocessed, cmdfix, _perms))
        elif isinstance(exp, commands.CommandInvokeError):
            if isinstance(exp.original, discord.HTTPException):
                key = bdel(bc_key, 'HTTPException: ')
                if key.startswith('BAD REQUEST'):
                    key = bdel(bc_key, 'BAD REQUEST')
                    if key.endswith('Cannot send an empty message'):
                        await self.csend(ctx, emp_msg.format(ctx.message.author, cprocessed, cmdfix))
                    elif c_key.startswith('Command raised an exception: HTTPException: BAD REQUEST (status code: 400)'):
                        if (eprefix == 'dm') and (ctx.invoked_with == 'user'):
                            await self.csend(ctx, '**No matching users, try again! Name, nickname, name#0000 (discriminator), or ID work. Spaces do, too!**')
                        else:
                            await self.csend(ctx, big_msg.format(ctx.message.author, cprocessed, cmdfix))
                    else:
                        await self.csend(ctx, msg_err.format(ctx.message.author, cprocessed, cmdfix, key))
                elif c_key.startswith('Command raised an exception: HTTPException: BAD REQUEST (status code: 400)'):
                    if (eprefix == 'dm') and (ctx.invoked_with == 'user'):
                        await self.csend(ctx, '**No matching users, try again! Name, nickname, name#0000 (discriminator), or ID work. Spaces do, too!**')
                    else:
                        await self.csend(ctx, big_msg.format(ctx.message.author, cprocessed, cmdfix))
                elif c_key.startswith('Command raised an exception: RuntimeError: PyNaCl library needed in order to use voice'):
                    await self.csend(ctx, '**The bot owner hasn\'t enabled voice!**')
                else:
                    await self.csend(ctx, msg_err.format(ctx.message.author, cprocessed, cmdfix, key))
            elif isinstance(exp.original, NameError):
                if isinstance(exp.original, UnboundLocalError):
                    key = bdel(bc_key, "UnboundLocalError: local variable '")
                    key = key.replace("' referenced before assignment", '')
                    await self.csend(ctx, nam_err.format(ctx.message.author, cprocessed, cmdfix, key))
                else:
                    key = bdel(bc_key, "NameError: name '")
                    key = key.replace("' is not defined", '')
                    await self.csend(ctx, nam_err.format(ctx.message.author, cprocessed, cmdfix, key.split("''")[0]))
            elif isinstance(exp.original, asyncio.TimeoutError):
                await self.csend(ctx, tim_err.format(ctx.message.author, cprocessed, cmdfix))
            elif (cprocessed in self.bot.commands['calc'].aliases) or (cprocessed == 'calc'):
                await self.csend(ctx, ast_err.format(ctx.message.author, cprocessed, cmdfix))
            else:
                await self.csend(ctx, '⚠ Error in `%s`!\n```' % (cmdfix + cprocessed) + bc_key + '```')
        elif type(exp) in [commands.MissingRequiredArgument, commands.TooManyArguments, commands.BadArgument]:
            if ctx.invoked_subcommand is None:
                tgt_cmd = self.bot.commands[cprocessed]
            else:
                tgt_cmd = ctx.invoked_subcommand
            try:
                r_usage = bdel(bdel(bdel(tgt_cmd.help.split('\n')[-1], 'Usage: '),
                                         tgt_cmd.name), cprocessed)
            except AttributeError:
                r_usage = ''
            await self.csend(ctx, arg_err.format(ctx.message.author, cprocessed, cmdfix, cmdfix +
                             cprocessed + r_usage, arg_err_map[type(exp)]))
        else:
            await self.csend(ctx, '⚠ Error in `%s`!\n```' % (cmdfix + cprocessed) + bc_key + '```')

def setup(bot):
    bot.add_cog(Errors(bot))
