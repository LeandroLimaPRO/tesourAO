from discord.errors import HTTPException
from .inits import *

class Blaclist_member(commands.Cog):
    
    #comando blacklista players
    @commands.command("b", help="blacklista player")
    async def blacklist(self, ctx, player:str, reason="Motivo", lang="english"):
        tr = mudarLingua(lang)
        fot = "\n" + tr.translate(tr.translate(msg["footer"]))

        if has_roles(ctx) or is_guild_owner(ctx):
            if is_guild_reg(ctx.guild.id):
                datag = obter_dados(Guild,ctx.guild.id)
                lang = datag.lang
                tr = mudarLingua(lang)
                chann = datag.canal_blacklist
                fot = "\n" + tr.translate(msg["footer"])
                if chann:
                    try:   
                        channel = bot.get_channel(chann)
                    except: 
                        await ctx.send(tr.translate(msg["blacklist"]["not-reg"]) + fot)
                        return
                else:
                    await ctx.send(tr.translate("O canal de blacklist não foi cadastrado. Por favor use o comando *?rb* no canal desejado"))
                    return 0
                if not is_blacklisted_from_guild(ctx.guild.id,player):
                    try:
                        memb = obter_dados(Members,player)
                    except SQLAlchemyError as e:
                        logger.error(e)
                        memb = False
                    
                    if memb:
                        memb.is_blacklist = True
                        session.flush()
                    data = Blacklist(name=player, 
                                    reason=reason,
                                    police=ctx.author.nick, 
                                    guild_id=ctx.guild.id
                                    )
                    print(data)
                    try:
                        add_dados(data)
                    except SQLAlchemyError as e:
                        logger.error(e)
                        return
                    embed= discord.Embed(title= "BlackList", color=discord.Color.dark_red())
                    embed.add_field(name=tr.translate("Player"), value=player)
                    embed.add_field(name= tr.translate("Reason"), value=reason)
                    embed.add_field(name= tr.translate(msg["more"]), value=tr.translate(msg["footer"]), inline=False)
                    logger.debug(f"Blacklist *{player}* motivo: *{reason}*")    
                    try:
                        #logger.info("tentando enviar msg")
                        await channel.send(embed=embed)
                        await ctx.send(embed=embed)
                    except:
                        logger.debug("Não foi possivel enviar msg")
                else:
                    await ctx.send(tr.translate(msg["blacklist"]["check"]["bl"]) + fot)
            else:
                 await ctx.send(tr.translate(msg["not-reg"]) + fot)   
        else:
            await ctx.send(tr.translate(msg["not-role"]) + fot)

    @commands.command("br", help="Remove player to blacklist")
    async def blacklist_remove(self, ctx, player:str, lang="english"):
        tr = mudarLingua(lang)
        fot = "\n" + tr.translate(msg["footer"])
        if has_roles(ctx) or is_guild_owner(ctx):
            if is_guild_reg(ctx.guild.id):
                datag = obter_dados(Guild,ctx.guild.id)
                tr = mudarLingua(datag.lang)
                try:
                    chann = datag.canal_blacklist
                    channel = bot.get_channel(chann)
                except KeyError:
                    fot = "\n" + tr.translate(msg["footer"])
                    await ctx.send(tr.translate(msg["blacklist"]["not-reg"]) + fot)
                    return
                if is_blacklisted_from_guild(ctx.guild.id,player):
                    memb = obter_dados(Members,player)
                    if memb:
                        memb.is_blacklist = False
                        session.flush()
                        memb_bl = session.query(Blacklist).filter(Blacklist.guild_id==datag.id,Blacklist.name==memb.name).first()
                        session.delete(memb_bl)
                        session.commit()
                    embed= discord.Embed(title= tr.translate(msg["blacklist"]["title-r"]), color=discord.Color.blue())
                    embed.add_field(name="Player", value=player)
                    embed.add_field(name= tr.translate(msg["more"]), value=tr.translate(msg["footer"]), inline=False)
                    logger.info(f"*{player}* foi removido do blacklist")    
                    await channel.send(embed=embed)
                    await ctx.send(embed=embed)
                else:
                    fot = "\n" + tr.translate(msg["footer"])
                    await ctx.send(tr.translate(msg["blacklist"]["check"]["not-bl"]) + fot)
            else:
                await ctx.send(tr.translate(msg["not-reg"])+ fot)   
        else:
            await ctx.send(tr.translate(msg["not-role"]))
    #comando check blacklist
    @commands.command("cb", help="checa player no blacklist")
    async def check_blacklist(self, ctx, player:str, lang="english"):
        tr = mudarLingua(lang)
        fot = "\n" + tr.translate(msg["footer"])
        if has_roles(ctx) or is_guild_owner(ctx):
            if is_guild_reg(ctx.guild.id):
                datag = obter_dados(Guild,ctx.guild.id)
                tr = mudarLingua(datag.lang)
                fot = "\n" + tr.translate(msg["footer"])
                if is_blacklisted_from_guild(ctx.guild.id,player):
                    data = obter_dados(Blacklist,player)
                    embed= discord.Embed(title= "BlackListed", color=discord.Color.dark_red())
                    embed.add_field(name=tr.translate("Player"), value=data.name)
                    embed.add_field(name=tr.translate("Reason"), value=data.reason)
                    embed.add_field(name= tr.translate(msg["more"]), value=tr.translate(msg["footer"]), inline=False)
                    #logger.info(f"Blacklist *{player}* motivo: *{datareason}*")    
                    await ctx.send(embed=embed)
                else:
                    embed= discord.Embed(title= tr.translate(msg["blacklist"]["check"]["not-bl"]), color=discord.Color.green())
                    embed.description= f"*{player}*"
                    embed.add_field(name= tr.translate(msg["more"]), value=tr.translate(msg["footer"]), inline=False)
                    await ctx.send(embed=embed)
            else:
                await ctx.send(tr.translate(msg["not-reg"])+ fot)   
        else:
            await ctx.send(tr.translate(msg["not-role"]) + fot)
            
    