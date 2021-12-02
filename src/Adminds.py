from datetime import time
from logging import Logger
from discord import player
from discord.errors import HTTPException
from .inits import *

#obtem novos jogadores
async def get_new_players_in_guild(guild):
        logger.debug(f"Iniciando obtenção de novos players: {guild.name}")
        if guild.id_ao is not None or not "":
            members = await get_guild_members(guild.id_ao)
            n_p  = 0
            a_p = 0
            new_players = []
            for p in members:
                
                p_name = p["Name"]
                p_fame = p["KillFame"] +p["LifetimeStatistics"]["PvE"]["Total"]+ p["LifetimeStatistics"]["Crafting"]["Total"] + p["LifetimeStatistics"]["Gathering"]["All"]["Total"]

                if not (p_name):

                    new_player = Members(
                        guild_id=guild.id,
                        name=p_name,
                        fame = p_fame,
                        is_blacklist = False,
                        is_cargo = False
                    )
                    session.add(new_player)
                    session.flush()
                    new_player_tax = Taxa(
                     name = p_name,
                     guild_id = guild.id, 
                     saldo = 0, 
                     deposito = 0,
                     ciclo = 0)
                    session.add(new_player_tax)
                    session.flush()
                    logger.debug(f"<{p_name}> adicionado")
                    new_players.append(p_name)
                    n_p += 1
                else:
                    pl = obter_dados(Members,p_name)
                    #print(pl)
                    if bool(pl):
                        pl.fame = p_fame
                        pl.guild_id = guild.id
                        pl.taxa.guild_id = guild.id
                        session.flush()
                    logger.debug(f"<{p_name}> atualizando fama: {p_fame}")
                    a_p += 1
            session.commit()
            logger.info(f"Processo de obtenção de players realizado. NOVOS: {n_p} ATUALIZADOS: {a_p}")
            return new_players
        else:
            logger.debug(f"<{guild.name}> não pode verificar novos players devido a falta do ID DO ALBION. Tente atualizar com <?rg>")        

#obtem novos jogadores
async def remove_players_in_guild(guild):
        #db_memb = session.query(Members).filter_by(guild_id = guild_id)
        if guild.id_ao is not None or not "":
            members = await get_guild_members(guild.id_ao)
            db_memb = session.query(Members).filter_by(guild_id = guild.id).all()
            p_list = []
            del_p = 0
            del_players = []
            for p in members:
                p_list.append(p["Name"])
            for memb in db_memb:
                if memb.name not in p_list:
                    del_players.append(f"{memb.name} discord {memb.nick_discord}")
                    try:
                        session.delete(memb)
                    except SQLAlchemyError as e:
                        session.rollback()
                        logger.error(e)
                    session.flush()
                    del_p +=1
                    
            logger.info(F"Processo de delete de players realizado. DELETADO {del_p}")
            session.commit()
            return del_players
        else:
            logger.debug(f"<{guild.name}> não pode verificar novos players devido a falta do ID DO ALBION. Tente atualizar com <?rg>")        

class Admin(commands.Cog):
    '''
        METODOS PRIVATIVOS
    '''

    #obtem ranking semanal do albion
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
    
        #Obtem devedores - SISTEMA DE CONTRIBUIÇÃO
    # OBTEM LISTA DE DEVEDORES -SISTEMAS DE TAXAS
    async def calculate_guild_tax (self,taxa_d,gd,memb):
        c_m =len(memb)
        taxa_n = []
        for p in taxa_d:
            taxa_n.append(p.name)
        min_fame = gd.fame_taxa
        c_taxa = gd.taxa_p
        logger.info(f'Quantidade de players: {c_m}')
        count_tx = len(taxa_n)
        isentions = session.query(Members).filter_by(guild_id = gd.id, isention = True).all()
        p_o = session.query(Members).filter_by(guild_id =gd.id).all()
        listpl = []
        for p in p_o:
            listpl.append(p.name)
        for p in memb:
            pn = p["Name"]
            taxa_n.append(pn)
            pf = p["KillFame"] +p["LifetimeStatistics"]["PvE"]["Total"]+ p["LifetimeStatistics"]["Crafting"]["Total"] + p["LifetimeStatistics"]["Gathering"]["All"]["Total"]
            if p not in listpl:
                new_player = Members(name = pn, guild_id = id)
                add_dados(new_player)
                logger.debug(f"Player adicionado ao banco: {new_player}")


            if pn not in taxa_n and pf >= min_fame:
                if pn not in isentions:
                    new_contrib = Taxa(name=pn, depositos = 0, saldo = -c_taxa, ciclo = 1)
                    add_dados(new_contrib)
                else:
                    logger.debug(f"{pn} é isento")
            else:
                logger.debug(f"Não incluido: {pn}")
        #se o player sair,é removido do banco de dados
        for p in taxa_d:
            if p not in taxa_n:
                deletar_dados(Taxa,p)
                deletar_dados(Members,p)
                logger.warning(f'>{gd["name"]}  player: {p} removido por ter saido da guilda! Ou ser da lista de isencao')
        dev = session.query(Taxa).filter_by(guild_id=gd.id)
        c_m = session.query(Members).filter_by(guild_id = gd.id).count()
        count_tx = dev.count()
        logger.info(f'\n>>>Total de membors: {c_m}>>> \nTotal no sistema de taxas: {count_tx} \n>>> Diferença: {c_m - count_tx} \n>>>Total de devedores: {count_tx}')
        return dev
    
    #comando de ajuda de instalação do bot
    @commands.command(name="h", help="Tutorial for instalation bot in server")
    async def help_guild_register(self, ctx, lang="english"):
        g = obter_dados(Guild,ctx.guild.id)
        if g.lang:
            lang = g.lang
        mdb = init_json(cfg['msg_path'])
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        for ml in  mdb['tutorial']:
            #for m in ml:
                embed = discord.Embed(title=tr.translate(ml.get('title')),color=discord.Color.dark_green())
                ms = ""
                if ml.get('command'):
                    ms += tr.translate(ml.get('command')) + "\n"
                
                ms += tr.translate(ml.get('desc')) + "\n"
                embed.description = ms

                if ml.get('commands'):

                    for com in ml['commands']:
                        embed = discord.Embed(title=tr.translate(com.get('c')),color=discord.Color.dark_green())
                        ms = ""
                        ms += str(tr.translate(com.get("d"))) + "\n"
                        ms += str(com.get("u"))
                        embed.description = ms

                        await ctx.send(embed=embed)
                else:
                    await ctx.send(embed=embed)
                        
    @commands.command(name="list_language")
    async def lista_liguagens(self,ctx):
            tr = GoogleTranslator()
            m = ""
            lg = tr.get_supported_languages()
            for l in lg:
                m += str(l) + "\n"
            await ctx.send(m)
    #comando para registrar discord e guild ok
    @commands.command(name="rg", help="Register guild and discord in bot. note: If the name has a space, replace the space with '_' . Ex: ?rg S A M U -> ?rg S_A_M_U")
    async def guild_register(self, ctx, guildname="",language="english"):
        msg = init_json(cfg['msg_path'])
        tr = mudarLingua(language)
        if not tr:
            lista = "\n"
            for l  in GoogleTranslator().supported_languages:
                lista += l + "\n"
            await ctx.send(f"Is language not available. please try another language: {lista}")
            return 0
        else:
            await ctx.channel.trigger_typing()
            logger.info(bool(is_guild_owner(ctx)))
            id_albion = ""

            if is_guild_owner(ctx):
                if len(guildname)<1:
                    guildname=ctx.guild.name
                else:
                    guildname = guildname.replace("_", " ")
                await ctx.channel.trigger_typing()
                try:    
                    id_guild = await get_guild_id(guildname)
                except aiohttp.ContentTypeError as e:
                    id_guild = ""
                    logger.error(e)
                    logger.error(msg["rg"]["fail-ao"].format(guildname))
                    await ctx.send(tr.translate(msg["rg"]["fail-ao"].format(guildname)))

                await ctx.channel.trigger_typing()
                logger.info(f"Registrando: {ctx.guild.id}")
                if id_guild:
                    try:
                        guild = get_guild_info(id_guild)
                    except aiohttp.ContentTypeError as e:
                        guild = False
                        logger.error(e)
                # SALVA DADOS EM VARIAVEIS
                if guild:
                        id_ali = guild['AllianceId']
                else:
                    id_ali = ""
                if is_guild_reg(ctx.guild.id):

                    result = obter_dados(Guild,ctx.guild.id)
                    result.name = guildname
                    session.flush()
                    result.id_ao = id_guild
                    session.flush()
                    result.id_ali = id_ali
                    session.flush()
                    result.lang = language
                    session.commit()
                    
                    await ctx.send(tr.translate(msg["rg"]["players"]["search"].format(result.id_ao)))
                    try:
                        
                        await get_new_players_in_guild(result)

                    except: 
                        await ctx.send(tr.translate(msg["rg"]["players"]["fail"]))

                    await ctx.send(tr.translate(msg["rg"]["updated"].format(guildname)))
                else:
                    new = Guild(
                        id = ctx.guild.id,
                        name = guildname,
                        id_ali = id_ali,
                        id_ao = id_guild,
                        lang = language,
                        top = False,
                        taxap_s = False,
                        taxac_s = False
                    )
                    await ctx.channel.trigger_typing()
                    try:
                        add_dados(new)
                    except:
                        await ctx.send(tr.translate(msg["rg"]["fail"].format(guildname)) + ctx.author.mention) 
                    else:
                        logger.info(msg["rg"]["sucess"].format(guildname))
                        await ctx.send(tr.translate(msg["rg"]["sucess"].format(guildname)))
                        if new.id_ao != None != "":
                            await ctx.send(tr.translate(msg["rg"]["players"]["search"].format(new.id_ao)))
                            await get_new_players_in_guild(new)
                        else:
                            await ctx.send(tr.translate(msg["rg"]["players"]["fail"]))
            else:
                await ctx.send(tr.translate(tr.translate(msg["rg"]["is-owner"]) + ctx.author.mention))
    
    #comando para listar guilds registradas ok
    @commands.command(name="lg", help="Lists guilds registered in the bot")
    @commands.is_owner()
    async def guilds_list(self,ctx, lang ="english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        '''
        LISTA GUILDS
        '''
        #print(commands.Bot.owner.name)
        try:
            datag = session.query(Guild).all()
        except discord.errors.HTTPException as e:
            msg = f"Bad request guild list: {e}"
            logger.error(tr.translate(msg))
        else:
            bf =""
            for g in datag:
                bf += g.name
                bf += "\n"
            logger.info("[lg] Ok!")
            await ctx.send(bf)
    
    #comando para cadastrar cargos(roles) ok
    @commands.command(name="rr", help="Requires prior registration. Add management positions")
    async def register_role(self,ctx, roles:str, language ="english"):
        #        '''
        #        REGISTRA CARGO NO BOT
        #        DEVE TER PERMISSÃO     
        #        '''
        msg = init_json(cfg['msg_path'])
        tr = mudarLingua(language)

        idg = ctx.guild.id
        if is_guild_reg(idg):
            guildg = obter_dados(Guild,idg)
            if  guildg is None:
                    await ctx.send("<DB Error> not get GUILD! Try it")
                    return
            tr = GoogleTranslator(source='auto', target=guildg.lang)
            if has_roles(ctx):
                    if roles not in cargos_list(idg):
                        new = Cargos(
                            name = roles,
                            guild_id = ctx.guild.id
                        )
                        add_dados(new)
                        logger.info(f"[rr] {ctx.guild.name} o {ctx.author.nick} registrou o cargo {roles}.")
                        await ctx.send(tr.translate(msg["rr"]["sucess"].format(ctx.guild.name,ctx.author.mention,roles)))
                    else:
                        await ctx.send(tr.translate(f"<{roles}> has already been added!"))
            else:
                await ctx.send(tr.translate(msg["rr"]["not-role"].format(ctx.guild.name, ctx.author.mention)))
        else:
            await ctx.send(tr.translate(msg["not-reg"]))
    
    #comando para listar cargos adicionados ok
    @commands.command("lr", help="list added positions")
    async def lista_cargos(self,ctx, lang="english"):
        msg = init_json(cfg['msg_path'])
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        g = obter_dados(Guild,ctx.guild.id)
        if g.lang:
            lang = g.lang
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        '''
        LISTA CARGOS COM PERMISSÕES CADASTRADOS NO BOT (POR SERVIDOR)
        '''
        bf=""
        ro = session.query(Cargos).filter(Cargos.guild_id == ctx.guild.id).all()
        #print(f"<<{ro}>> {len(ro)}")
        for r in ro:
            #print(r.name)
            bf+= r.name
            bf+="\n"
        if (len(ro)>0):
            logger.info("[lr] ok!")
            await ctx.send(bf)
        else:
            await ctx.send(tr.translate("Roles Not registred!\n[Owner Server] Use **?rr** for registration role administration."))
    
    #comando para adicionar isenção no player ok
    @commands.command("ai", help="Add player insention of tax")
    async def add_player_i(self,ctx, nick_player, lang = "english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if is_guild_reg(ctx.guild.id):
            guild = obter_dados(Guild,ctx.guild.id)
            lang = guild.lang

            tr = mudarLingua(lang)
            if not tr:
                await ctx.send(tr)
                return

            if has_roles(ctx):
                add_isention(ctx.guild.id,nick_player)
                await ctx.send(tr.translate(f"{nick_player} added in insention!"))
                remove_tax(ctx.guild.id,nick_player)
                await ctx.send(tr.translate(f"{nick_player} is removed from tax system!"))
            else:
                await ctx.send(tr.translate("Not available role!"))
        else:
            await ctx.send(tr.translate(msg["en-us"]["not-reg"])) 
    
    #remove player da isenção ok 
    @commands.command("ri", help="remove player insention of tax system")
    async def re_player_i(self,ctx, nick_player, lang = "english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if is_guild_reg(ctx.guild.id):
            guild = obter_dados(Guild,ctx.guild.id)
            if guild.lang:
                lang = guild.lang
            tr = mudarLingua(lang)
            if not tr:
                await ctx.send(tr)
                return
            if has_roles(ctx):
                remove_isention(ctx.guild.id,nick_player)
                await ctx.send(tr.translate(f"{nick_player} is removed insention of tax system"))
            else:
                await ctx.send(tr.translate("Not available role!"))
        else:
            await ctx.send(tr.translate(msg["not-reg"]))
    #remove player da isenção ok
    @commands.command("rtax", help="remove player tax system")
    async def re_player_t(self,ctx, nick_player, lang = "english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if is_guild_reg(ctx.guild.id):
            guild = obter_dados(Guild,ctx.guild.id)
            if guild.lang:
                lang = guild.lang
                tr = mudarLingua(lang)
                if not tr:
                    await ctx.send(tr)
                    return
            if has_roles(ctx):
                gd = session.query(Members).get(ctx.guild.id)
                new_tax = session.query(Taxa).filter_by(name = nick_player,guild_id = ctx.guild.id).first()
                new_tax.deposito = 0
                session.flush()
                new_tax.saldo = gd.taxa_p
                session.flush()
                new_tax.ciclo = 1
                session.commit()
                await ctx.send(tr.translate(f"{nick_player} is removed from tax"))
            else:
                await ctx.send(tr.translate("Not available role!"))
        else:
            await ctx.send(tr.translate(msg["not-reg"]))                
    
    #checa taxa ok
    @commands.command("ti", help="check tax of player")
    async def ck_player_t(self,ctx, nick_player, lang="en-us"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        dsid = str(ctx.guild.id)
        if is_guild_reg(dsid):
            dg = session.query(Guild).get(dsid)
            lang = dg.lang
            tr = mudarLingua(lang)
            if not tr:
                await ctx.send(tr)
                return
            if is_tax_silver_system(dsid):
                if is_tax_exist(nick_player):
                    p = session.query(Taxa).get(nick_player)
                    m = session.query(Members).get(nick_player)
                    deposito = p.deposito
                    saldo = p.saldo
                    ciclo = p.ciclo
                    if not m.isention:
                        if saldo >0:
                            embed = discord.Embed(title= tr.translate(msg["tax"]["title"]),color=discord.Color.green())
                            embed.add_field(name=tr.translate(msg["tax"]["saldo"]), value=size(saldo,system=si))
                        else:
                            embed = discord.Embed(title= tr.translate(msg["tax"]["ck-title"]),color=discord.Color.red())
                            embed.add_field(name=tr.translate(msg["tax"]["saldo"]), value=f'{size(-saldo,system=si)}')
                        embed.description= nick_player
                        #embed.add_field(name=tr.translate(msg["tax"]["depo"], value=size(deposito,system=si))
                        embed.add_field(name=tr.translate(msg["tax"]["cicle"]), value=ciclo)
                    else:
                        embed = discord.Embed(title= tr.translate(msg["tax"]["title"]),color=discord.Color.blue())
                        embed.description= tr.translate(msg["tax"]["isention"])
                    
                    embed.add_field(name=tr.translate(msg["more"]), value= tr.translate(msg["footer"]), inline=False)

                    await ctx.send(embed=embed)
                else:
                    await ctx.send(tr.translate(msg["tax"]["not-pl"]))
            else:
                await ctx.send(tr.translate(msg["tax"]["not-tax"]))
        else:
            await ctx.send(tr.translate(msg["tax"]["no-reg"]))
    '''
     TAREFAS DE TRANSMISSÕES DO TOP - TASKS
    '''
    # SISTEMA DE CONTRIBUIÇÃO
    @tasks.loop(hours=6)
    async def contrib_tax(self):
        lang = "english"
        tr = mudarLingua(lang)
        datag = session.query(Guild).filter_by(top = True).all()
        #client = discord.Client()
        ss = 0
        for g in datag:
            lang = g.lang
            tr = mudarLingua(lang)

            try:
                channel = bot.get_channel(g.canal_taxa)
            except :
                logger.error("Fail get channel for send contrib!")
                return
            if not tr:
                await channel.send(tr)
                return
            logger.warning(f'Iniciando sistema de contribuição da guilda: {g.name}')
            taxa = session.query(Taxa).filter(Taxa.guild_id == g.id, Taxa.saldo < 0 ).all()
            embed = discord.Embed(title=tr.translate(msg["title_tax"]), color = discord.Color.dark_magenta())
            desc = "\n"
            desc += f"Quantidade de inadiplente: {len(taxa)}\n\n\n"
            for p in taxa:
                desc += f'**{p.name}** \n {size(-p.saldo,system=si)}\n\n'
                ss+= int(p.saldo)
            desc += "\n\n\n" + tr.translate(msg["tax"]["info"].format(size(-ss,system=si)))
            embed.add_field(name=tr.translate(msg["more"]), value=tr.translate(msg["footer"]), inline=False)
            embed.description= desc
            embed.set_footer(text = tr.translate(msg["tax"]["foot"]))
            logger.info(f'Fim do sistema de contribuição da guilda: {g.name}')
            try:
                await channel.send(embed=embed)
            except:
                logger.debug(f"<{g.name}> Não foi possivel encontrar canal")
                
    #top pve
    @tasks.loop(hours=24)
    async def players_top_pve(self):
            lang = "english"
            tr = mudarLingua(lang)
            logger.info("Trabalhando para emitir top semanal pve")
            datag = session.query(Guild).filter_by(top = True).all()
            for g in datag:
                lang = g.lang
                tr = mudarLingua(lang)
                if  g.top == True:
                    client = discord.Client()
                    if(g.canal_top is not None and g.id_ao is not None):
                        try:
                            channel = bot.get_channel(g.canal_top)
                        except:
                            logger.warning(f"Canal não localizado da guilda {g.name}")
                            return
                        if not tr:
                            await channel.send(tr)
                            return
                        logger.info(tr.translate(f"<{g.name}> Aguardando dados do Albion"))
                        try:
                            d = await self.ranking_semanal(g.id_ao)
                        except:
                            logger.debug(f"<{g.name}> Não foi possivel enviar informações do top ranking")
                            await channel.send(tr.translate(f"<{g.name}> Please verify re-register in bot. No get data from albion."))
                        embed = discord.Embed(title= tr.translate(msg["title_c"].format(g.name)), color=discord.Color.gold())
                        for p in d:
                            if d[p]["Fame"] >1000:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=size(d[p]["Fame"],system=si), inline=False)
                            else:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=d[p]["Fame"], inline=False)
                        
                        embed.add_field(name= tr.translate(msg["more"]), value=tr.translate(msg["footer"]), inline=False)
                        
                        try:
                            await channel.send(embed=embed)
                        except:
                            logger.error("Não foi possivel enviar mensagem")

                        logger.info("Trabalho realizado com sucesso!")

    
    #top coletores
    @tasks.loop(hours=24)
    async def players_top_g(self):
            lang = "english"
            tr = mudarLingua(lang)

            datag = session.query(Guild).filter_by(top = True).all()
            logger.info("Trabalhando para emitir top semanal coletor")
            for g in datag:
                lang = g.lang
                tr = mudarLingua(lang)
                if  g.top == True:
                    #client = discord.Client()
                    if(g.canal_top is not None and g.id_ao is not None):
                        try:
                            channel = bot.get_channel(g.canal_top)
                        except:
                            logger.warning(f"Canal não localizado da guilda {g.name}")
                        if not tr:
                            await channel.send(tr)
                            return
                        logger.info(f"<{g.name}>Aguardando dados do Albion")
                        try:
                            d = await self.ranking_semanal(g.id_ao, tipo_ranking= 1)
                        except:
                            logger.error("Não foi possivel enviar informações do top ranking")
                            await channel.send(tr.translate("Please verify re-register in bot. No get data from albion."))
                        embed = discord.Embed(title= tr.translate(msg["title_pve"].format(g.name)), color=discord.Color.gold())
                        for p in d:
                            if d[p]["Fame"] >1000:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=size(d[p]["Fame"],system=si), inline=False)
                            else:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=d[p]["Fame"], inline=False)
                            
                        embed.add_field(name=tr.translate(msg["more"]), value=tr.translate(msg["footer"]), inline=False)

                        try:
                            await channel.send(embed=embed)
                        except:
                            logger.error("Não foi possivel enviar mensagem")

                        logger.info("Trabalho realizado com sucesso!")


    
    #obtem gerencia jogaores
    @tasks.loop(hours=8)
    async def gerencia_jogadores(self):
        tr = mudarLingua("english")
        sttot = dt.now()    
        list_guild_reg = session.query(Guild).filter(Guild.id_ao != "",Guild.id_ao != None).all()
        for guild in list_guild_reg:
            st = dt.now()
            logger.info(f"Verificando removendo jogadores que sairam <{guild.name}>")
            saiu = await remove_players_in_guild(guild)
            #print(saiu)
            logger.info(f"Verificando novos jogadores da guild <{guild.name}>")
            entrou = await get_new_players_in_guild(guild)
            #print(entrou)
            logger.info(f"({dt.now() - st}) Sucess <{guild.name}>")
            #print(guild.canal_info)
            if guild.canal_info:
                tr = mudarLingua(guild.lang)   
                try:
                    channel = bot.get_channel(guild.canal_info)
                except HTTPException as e:
                    channel = False
                    logger.error(e)
                if channel:
                    desc = ""
                    embed = discord.Embed(title= tr.translate("Jogadores que sairam da guild"), color=discord.Color.red())
                    for player in saiu:
                         desc += f"{player} \n"
                    embed.description = desc
                    try:
                        await channel.send(embed=embed)
                    except HTTPException as e:
                        channel = False
                        logger.error(e)
                    desc = ""
                    del embed
                    embed = discord.Embed(title= tr.translate("Jogadores que Entraram da guild"), color=discord.Color.gold())
                    for player in entrou:
                         desc += f"{player} \n"
                    embed.description = desc
                    try:
                        await channel.send(embed=embed)
                    except HTTPException as e:
                        channel = False
                        logger.error(e)

        logger.info(f"Tarefa de gerenciamento de jogadores concluido! ({dt.now() - sttot})")
        

    @tasks.loop(hours=24)
    async def players_top_pvp(self):
            
            lang = "english"
            tr = mudarLingua(lang)
            datag = session.query(Guild).filter_by(top = True).all()
            logger.info("Trabalhando para emitir top semanal PVP")
            for g in datag:
                logger.info(f"Iniciando {g.name}")
                lang = g.lang
                tr = mudarLingua(lang)
                if(g.canal_top is not None and g.id_ao is not None):
                    #print(f"{g.name} : {g.canal_top} > {g.id_ao}")

                    try:
                        channel = bot.get_channel(g.canal_top)
                    except:
                        logger.warning(f"Canal não localizado da guilda {g.name}")
                    if not tr:
                        await channel.send(tr)
                        return
                    logger.info("Aguardando dados do Albion")
                    try:
                        tops = await get_guild_top_kills(g.id_ao)
                    except aiohttp.ContentTypeError as e:
                        tops = False
                        logger.error(e)
                        await channel.send(tr.translate("Não foi possivel obter TOP PVP - Não foi possivel comunicar com albion"))
                    if bool(tops):
                        embed = discord.Embed(title= tr.translate(msg["title_pvp"].format(g.name)), color=discord.Color.gold())
                        #aqui
                        k = 0
                        for kill in tops:
                            k += 1
                            if isinstance(kill,dict):
                                totalFame = kill['TotalVictimKillFame']
                                if totalFame >1000:
                                    totalFame =  size(totalFame, system=si)
                                data = date_format(kill['TimeStamp'])
                                killer = kill['Killer']['Name']
                                vitima = kill['Victim']['Name']
                                text = f"{k}º {killer} -  ☠️ {vitima}"
                                
                                text = tr.translate(text)
                                    
                                val = f"{totalFame} Fama em {data}"

                                if kill['numberOfParticipants']:
                                    assistencia = kill['numberOfParticipants']
                                    if assistencia > 0:
                                        val += f" com {assistencia} assistências"
                                
                            embed.add_field(name= text , value=val, inline=False)
                                
                        embed.add_field(name=tr.translate(msg["more"]), value=tr.translate(msg["footer"]), inline=False)
                        try:
                            await channel.send(embed=embed)
                        except:
                            logger.error("Canal não existe")
                    logger.info("Trabalho realizado!")

    #negativados - lista de devedores de taxas_fixas
    '''
    @tasks.loop(hours=6)
    async def negativados(self):
        #1 - verifica se TODOS os player tem contribuições (TAXA.JSON)
        
        datag = session.query(Guild).filter_by(taxap_s = True).all()
        for g in datag:
            channel = bot.get_channel(datag.canal_taxa)
            embed = discord.Embed(title= f'NEGATIVADOS [{datag.name}]', color=discord.Color.red())
            data = session.query(Taxa).filter_by(guild_id = g.id).all()
            #1.1 - ADICIONA LISTA :
            for p in data:
                saldo = data.saldo
                #debito = deposito - taxa_fixa*ciclo
                taxa = g.taxa_p
                #PLAYER com debito  de debito   = SE deposito < taxa_fixa*ciclo
                if saldo < taxa:  
                    embed.add_field(name = p)
                    embed.add_field(value = saldo)  
                    #2 - ENVIA A LISTA DOS PLAYERS EM DEBITOS
            embed.add_field(name= "Mais", value=fot, inline=False)
            await channel.send(embed=embed)
    '''
    '''
        Registro de canal para transmisção dos top
    '''
    #comando registra canal top
    @commands.command("rt", help="Register channel for TOP's transmission")
    async def registra_canal_top(self,ctx, lang = "english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if is_guild_reg(ctx.guild.id):
            datag = obter_dados(Guild,ctx.guild.id)
            lang = datag.lang
            tr = mudarLingua(lang)
            if not tr:
                await ctx.send(tr)
                return
            if has_roles(ctx):
                
                datag.top = True
                session.flush()
                datag.canal_top = ctx.channel.id
                session.commit()
                logger.info(f"Canal para transmitir top semanal: {ctx.channel.name}")
                await ctx.send(tr.translate(f"Canal para transmitir top semanal: {ctx.channel.name}"))
            else:
                await ctx.send(tr.translate(msg["rg"]["is-owner"]))
        else:
            await ctx.send(tr.translate(msg["en-us"]["not-reg"]))
    
    #comando registra canal taxa
    @commands.command("rtx", help="Register channel for tax transmission")
    async def registra_canal_taxa(self,ctx, tax = 0, min_fame=0, lang = "english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if is_guild_reg(ctx.guild.id):
            datag = obter_dados(Guild,ctx.guild.id)
            lang = datag.lang
            tr = mudarLingua(lang)
            if not tr:
                await ctx.send(tr)
                return
            if has_roles(ctx):
                datag.taxap_s = True
                session.flush()
                datag.canal_taxa = ctx.channel.id
                session.flush()
                datag.taxa_p = tax
                session.flush()
                datag.fame_taxa = min_fame
                session.commit()
                logger.info(f"Canal para transmitir taxa: {ctx.channel.name}")
                await ctx.send(tr.translate(f"Canal para transmitir taxa: {ctx.channel.name}"))
            else:
                await ctx.send(tr.translate(msg["rg"]["is-owner"]))
        else:
            await ctx.send(tr.translate(msg["en-us"]["not-reg"]))
    
    #comando registra canal blacklist
    @commands.command("rb", help="Register channel for blacklist transmission")
    async def registra_canal_black(self,ctx, lang="english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if is_guild_reg(ctx.guild.id):
            datag = obter_dados(Guild,ctx.guild.id)
            lang = datag.lang
            tr = mudarLingua(lang)
            if not tr:
                await ctx.send(tr)
                return
            if has_roles(ctx):
                datag.canal_blacklist = ctx.channel.id
                session.commit()
                logger.info(tr.translate(f"({ctx.guild.id}) - Canal para transmitir blacklist: {ctx.channel.name}"))
                await ctx.send(tr.translate(f"({ctx.guild.id}) - Canal para transmitir blacklist: {ctx.channel.name}"))
            else:
                await ctx.send(tr.translate(msg["rg"]["is-owner"]))
        else:
            await ctx.send(tr.translate(msg["en-us"]["not-reg"]))
    
    #comando registra canal 
    
    @commands.command("rgi", help="Register channel for guild info transmission")
    async def registra_canal_guild_info(self,ctx):
        lang = "english"
        tr = mudarLingua(lang)
        if is_guild_reg(ctx.guild.id):
            datag = obter_dados(Guild,ctx.guild.id)
            tr = mudarLingua(datag.lang)
            if has_roles(ctx):
                datag.canal_info = ctx.channel.id
                session.commit()
                logger.info(f"({ctx.guild.id}) - Canal para transmitir info: {ctx.channel.name}")
                await ctx.send(f"({ctx.guild.id}) - Canal para transmitir info: {ctx.channel.name}")
            else:
                await ctx.send(tr.translate(msg["rg"]["is-owner"]))
        else:
            await ctx.send(msg["not-reg"])
    
    '''
        COMANDOS TASKS
    '''
    #ativa task top pve
    @commands.command("stpve", help= "Starts task of presenting weekly top every 8h")
    @commands.is_owner()
    async def start_top_pve(self,ctx):
        logger.info("Iniciou tarefa de emitir top semanal pve!")
        await ctx.send(self.players_top_pve.start())
    
    #ativa task top coletor
    @commands.command("stg", help= "Starts task of presenting weekly top collection every 8h")
    @commands.is_owner()
    async def start_top_g(self,ctx):
        logger.info("Iniciou tarefa de emitir top coleta semanal coleta!") 
        await ctx.send(self.players_top_g.start())
   
    @commands.command("stt", help= "Starts task of tax silver every 12h")
    @commands.is_owner()
    async def start_contrib(self,ctx):
        logger.info("Iniciou tarefa de emitir devedores!") 
        await ctx.send(self.contrib_tax.start())
   
    @commands.command("stp", help= "Starts task of player for tick 12h")
    @commands.is_owner()
    async def start_gplayer(self,ctx):
        logger.info("Iniciou tarefa de gerenciar players!") 
        await ctx.send(self.gerencia_jogadores.start())

    @commands.command("stpvp", help= "Starts task of player for tick 12h")
    @commands.is_owner()
    async def start_process(self,ctx):
        await ctx.send(self.players_top_pvp.start())
        logger.info("Pronto")
        
        
    @commands.command("gpl", help = "list all players in guild")
    async def guild_players_list(self,ctx, lang = "english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if is_guild_reg(ctx.guild.id):
            guild = obter_dados(Guild,ctx.guild.id)
            lang = guild.lang
            tr = mudarLingua(lang)
            if not tr:
                await ctx.send(tr)
                return
            players = guild.members
            #print(players)
            if not players:
                #print(ctx.guild.id)
                players = session.query(Members).filter_by(guild_id = 827945906175082526).all()
                #print(players)
            if not players:
                await ctx.send(tr.translate("Your guild has no players, or has not been registered in our junk"))
            else:
                msg = ""
                count = len(players)
                embed = discord.Embed(title= tr.translate(f"Players({count}) List"), color=discord.Color.gold())
                #print(count)
                for p in players:
                    msg += f"{p.name} \n"
                embed.description =  msg
                await ctx.send(embed=embed)
            logger.info("Fim de busca - players")
        else:
            await ctx.send(tr.translate("Sua guild não foi encontrada nos meus bagulhos"))


    @commands.command("gpc", help = "check player in guild")
    async def guild_players_check(self,ctx, nick, lang= "english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return

        #print(nick)
        if is_guild_reg(ctx.guild.id):
            guild = obter_dados(Guild,ctx.guild.id)
            #print(guild)
            player = obter_dados(Members,nick)
            lang = guild.lang
            tr = mudarLingua(lang)
            if not tr:
                await ctx.send(tr)
                return
            if guild.id != player.guild.id:
                player = None
            if not player:
                embed = discord.Embed(title= tr.translate(f"player is no your guild, or has not been registered in our junk"), color=discord.Color.red())
                #await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title= tr.translate(f"{player.name} is in {player.guild.name}"), color=discord.Color.blue())
                # v= size(player.fame,system='si')
                # embed.description = f"Fame: {v}" 
            await ctx.send(embed=embed)
            logger.info("Fim de busca - players")

    @commands.command("remove_guild", help = "remove guild")
    @commands.is_owner()
    async def remove_guild(self, ctx, id_g = None, lang = 'english'):
        id = ctx.guild.id
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if(id_g):
            id= id_g
        deletar_dados(Guild,id)
        await ctx.send(tr.translate("sua guild foi removida"))
        

    @commands.command()
    async def teste(self,ctx):
        #print(ctx.author)
        #print(type(ctx.author))
        try:
            await ctx.author.edit(nick = "LeTurn")
        except HTTPException as e:
            logger.error(e)
        await ctx.send(type(ctx.author))