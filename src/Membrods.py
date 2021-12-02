from discord.errors import HTTPException
from .inits import *

class Membro (commands.Cog):
    '''
    CLASSE DESTINADA À PLAYERS
    '''
    '''
        METODOS PRIVATIVOS
    '''
    #função obtem ranking semanal do albion
    async def ranking_semanal(self,gid, tipo_ranking=0, sub_g = 0, region=0):
        '''
        gid:            ID Guild Albion
        tipo_ranking :  PvE, 1= Gatherering
        sub_g:          All | Fiber | Hide | Ore | Rock | Wood
        region:         Total | Royal | Outlands | Hellgate
        obtem o top 10 players pve da guilda
        '''
        #print(f'{sub_g} : {sub_g}: {region}')
        data_ranking = await get_statistics_guild(gid, types=tipo_ranking, subtype=sub_g,  region =region)
        d_p={}
        i = 0
        for p in data_ranking:
            i +=1
            d_p[i] = { "Name": p["Player"]["Name"],
                        "Fame": p["Fame"]
                        }
            d_p.update(d_p)
        logger.debug(f"Dados dos players no top pve semanal \n\n{d_p}")
        return d_p

    '''
        COMANDOS UTEIS
    '''
    #comando consulta player no albion
    @commands.command(name = 'pi', help= "Consulta informações do player no Albion")
    async def player_info(self, ctx, nick:str, lang="english"):
        await ctx.channel.trigger_typing()
        #atribui lingua de resposta (pt ou en)
        tr = mudarLingua(lang)
        mensao = ctx.author.mention
        cor = discord.Color.green()
        if is_guild_reg(ctx.guild.id):
                g = obter_dados(Guild,ctx.guild.id)
                lang = g.lang
                tr = mudarLingua(lang)
                player = obter_dados(Members, nick)
                fot = tr.translate(msg["footer"])
                if bool(player):
                    cor = discord.Color.blue()
                    embed = discord.Embed(title= tr.translate(msg["pi"]["title"].format(player.name)), color = cor)
                    embed.description = tr.translate(f"Este jogador está registrado!")
                    if player.is_blacklist:
                        cor= discord.Color.red()
                        embed.description = tr.translate(f"Este jogador está blacklistado!")
                        embed.add_field(name = tr.translate(f"Por {player.blacklist.reason}"), value = tr.translate(f"Police: {player.blacklist.police}"))
                    embed.color = cor
                    embed.add_field(name = tr.translate(f"Discord"), value = tr.translate(f"{player.nick_discord}"))
                    embed.add_field(name=tr.translate(msg["more"]), value=fot, inline=False)
                    await ctx.send(embed=embed)
        logger.debug(f"[pi] {ctx.author} procurando player {nick}")
        #tenta obter id do player
        #await ctx.send("Wait looking in Albion's junk! It might take a while.")
        try:
            p_id = await get_player_id(nick)
        except:
            logger.error(f"[pi] {ctx.author} deu error ao consultar id")
            await ctx.send(tr.translate(f"{ctx.author.mention} Não foi possivel obter id do {nick}. Tente Novamente"))
            return
        
        logger.info(f"[pi] {ctx.author} - Jogador ID:{p_id}")
        logger.info(f"[pi] {ctx.author} procurando informações do {nick}")
        await ctx.channel.trigger_typing()
        #tenta obter informações do player
        try:
            p_info = await get_player_info(p_id)
        except:
            logger.error(f"[pi] {ctx.author} deu error ao consultar as informações")
            await ctx.send(tr.translate(f"{ctx.author.mention} Não foi possivel obter informações do jogador. Tente novamente"))
            return
        logger.debug(f"[pi] {ctx.author} procurando as covas que o {nick} fez")
        await ctx.channel.trigger_typing()
        #tenta obter as kills do player
        try:
            p_kills = await get_player_kills(p_id)
        except aiohttp.ContentTypeError as e:
            logger.warning(f"[pi] {ctx.author} deu error ao consultar as kills. {e}")
            await ctx.send(tr.translate(f"{ctx.author.nick} Não foi possivel obter cemiterio de defuntos do player. Aguarde"))
            p_kills = {}
        logger.debug(f"[pi] {ctx.author} Quantidade de dados: {len(p_info)} do {nick}")
        #se houver informações
        if len(p_info)>0:

            pvp = round(p_info['KillFame'])
            pve = round(p_info['LifetimeStatistics']['PvE']['Total'])
            coleta = round(p_info['LifetimeStatistics']['Gathering']['All']['Total'])
            crafting = round(p_info['LifetimeStatistics']['Crafting']['Total'])
            total = round(pvp+pve+coleta+crafting)
            data_att = p_info['LifetimeStatistics']['Timestamp']
            embed = discord.Embed(title= tr.translate(msg["pi"]["title"].format(p_info['Name'])), color = cor)
            embed.description = tr.translate(msg["pi"]["desc"].format(size(total,system=si)))

            embed.add_field(name= tr.translate(msg["pi"]["f-pve"]), value=size(pve,system=si))

            embed.add_field(name= tr.translate(msg["pi"]["f-pvp"]), value= size(pvp,system=si))

            embed.add_field(name= tr.translate(msg["pi"]["f-col"]), value= size(coleta,system=si))

            embed.add_field(name= tr.translate("🛠 Crafting:"), value= size(crafting,system=si))
            kills =""
            for k in p_kills:
                kills= kills + "\n" +tr.translate(msg["pi"]["kill"].format(k['Victim']['AllianceName'],k['Victim']['Name'],k['TimeStamp'][0:10]))
            if len(p_kills)>0:
                embed.add_field(name= tr.translate(msg["pi"]["kills"]),value=kills, inline=False)   
            else:
                embed.add_field(name= tr.translate(msg["pi"]["nkills"]),value="🧸", inline=False)  
            embed.set_thumbnail(url="https://raw.githubusercontent.com/LeandroLimaPRO/tesourAO/main/images/paypal_qr.png")
            fot = tr.translate(msg["footer"])
            fot2 = tr.translate(msg["pi"]["att"].format(data_att)) + fot
            embed.add_field(name=tr.translate(msg["more"]), value=fot2, inline=False)
            logger.info(f"[pi] {ctx.author} Player consultado com sucesso!\n")
            await ctx.send(embed=embed)
            await ctx.send(mensao + tr.translate(f"Agora você pode usar **{prefix}rme [nick_albion]** para registra-se à guilda"))

        else:
            logger.warning(f"[pi] {ctx.author} Player Não Encontrado!\n")

    @commands.command("rme", help= "Registra player da guilda")
    async def register_me(self, ctx, nick_name, lang = 'english'):
        tr= mudarLingua(lang)
        logger.info("Iniciando registro de player")
        if is_guild_reg(ctx.guild.id):
            guild = obter_dados(Guild,ctx.guild.id)
            tr = mudarLingua(guild.lang)
            try:
                jogador = obter_dados(Members,nick_name)
            except SQLAlchemyError as e:
                jogador = False
                logger.error(e)
            if not bool(jogador):
                id = await get_player_id(nick_name)
                if id:
                    try:
                        jogador = await get_player_info(id)
                    except aiohttp.ContentTypeError as e:
                        jogador = False
                        logger.error(e)
                    if bool(jogador):
                        name = jogador['Name']
                        guild_name = jogador['GuildName']
                        if guild.name == guild_name:
                            nmDs = ctx.author.name + "#" + ctx.author.discriminator
                            new = Members(name = name, guild_id = guild.id, ref_discord = ctx.author.id ,nick_discord = nmDs)
                            newtax = Taxa(name=name, guild_id = guild.id, saldo = 0, deposito = 0, ciclo = 0)
                            print(new)
                            try:
                                add_dados(new)
                            except SQLAlchemyError as e:
                                session.rollback()
                                logger.error(f"Não foi possivel adicionar. {e}")
                                await ctx.send(tr.translate("Não foi possivel Adicionar seus dados."))
                                return
                            add_dados(newtax)
                            await ctx.send(tr.translate(f"Bem vindo a {guild_name}! Sr(a) {new.name}"))
                            return
                else:
                    await ctx.send(tr.translate("Este jogador ainda não foi registrado no sistema. Aguarde 24 Horas, para que o albion nos atualize"))
                    return
            else:
                if not jogador.is_blacklist:
                    jogador.nick_discord = ctx.author.name + "#" + ctx.author.discriminator
                    jogador.ref_discord = ctx.author.id
                    jogador.id_guild = ctx.guild.id
                    jogador.taxa.id_guild = ctx.guild.id
                    try:
                        session.commit()
                    except SQLAlchemyError as e:
                        logger.error(e)
                        session.rollback()
                        await ctx.send(tr.translate("Não foi possivel atualizar seus dados."))
                        return
                    try:
                        await ctx.author.edit(nick = "LeTurn")
                    except HTTPException as e:
                        await ctx.send(tr.translate("Não foi possivel Editar Seu Nick seus dados.Você está um cargo acima do meu."))
                        logger.error(e)
                    await ctx.send(tr.translate(f"Bem vindo a {guild.name}! Sr(a) {jogador.name}"))
                else:
                    await ctx.send(tr.translate(f"Solicitação negada. Está blaclistado motivo: {jogador.blaclist.reason}"))
        else:
            await ctx.send(tr.translate("Guild não registrada no sistema"))    
    
    
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
                    deletar_dados(Blacklist,player)
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