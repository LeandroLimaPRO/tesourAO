from .inits import *

#obtem novos jogadores
async def get_new_players_in_guild(guild):
        logger.debug(f"Iniciando obtenção de novos players: {guild}")
        if guild.id_ao is not None or not "":
            members = await get_guild_members(guild.id_ao)
            for p in members:
                p_name = p["Name"]
                p_fame = p["KillFame"] +p["LifetimeStatistics"]["PvE"]["Total"]+ p["LifetimeStatistics"]["Crafting"]["Total"] + p["LifetimeStatistics"]["Gathering"]["All"]["Total"]
                if not is_player_exist(guild.id,p_name):
                    new_player = Members(
                        guild_id=guild.id,
                        name=p_name,
                        fame = p_fame
                    )
                    session.add(new_player)
                    session.flush()
                    new_player_tax = Taxa(name = p_name,
                     guild_id = guild.id, 
                     saldo = 0, 
                     deposito = 0,
                     ciclo = 0)
                    session.add(new_player_tax)
                    session.flush()
                    logger.debug(f"<{p_name}> adicionado")
                else:
                    pl = obter_dados(Members,p_name)
                    pl.fame = p_fame
                    session.flush()
            session.commit()
            logger.info("Processo de obtenção de players realizado")
        else:
            logger.debug(f"<{guild.name}> não pode verificar novos players devido a falta do ID DO ALBION. Tente atualizar com <?rg>")        

#obtem novos jogadores
async def remove_players_in_guild(guild):
        #db_memb = session.query(Members).filter_by(guild_id = guild_id)
        if guild.id_ao is not None or not "":
            members = await get_guild_members(guild.id_ao)
            db_memb = session.query(Members).filter_by(guild_id = guild.id).all()
            p_list = []
            for p in members:
                p_list.append(p["Name"])
            for memb in db_memb:
                if memb.name not in p_list:
                    deletar_dados(Members,memb.name)
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
    async def help_guild_register(self, ctx, lang="en-us"):    
        embed = discord.Embed(title=msg[lang]["tutorial"]["title"], color = discord.Color.green())
        embed.add_field(name=msg[lang]["tutorial"]["1"]["n"], value=msg[lang]["tutorial"]["1"]["v"],inline=False)
        embed.add_field(name=msg[lang]["tutorial"]["2"]["n"], value=msg[lang]["tutorial"]["2"]["v"],inline=False)
        embed.add_field(name=msg[lang]["more"], value=msg[lang]["footer"],inline=False)
        await ctx.send(embed=embed)
    
    #comando para registrar discord e guild ok
    @commands.command(name="rg", help="Register guild and discord in bot. note: If the name has a space, replace the space with '_' . Ex: ?rg S A M U -> ?rg S_A_M_U")
    async def guild_register(self, ctx, guildname="",language="pt-br"):
        if language != "pt-br" or language != "en-us":
            language = "en-us";
        await ctx.channel.trigger_typing()
        logger.info(bool(is_guild_owner(ctx)))
        id_albion = ""
        if is_guild_owner(ctx):
            if len(guildname)<1:
                guildname=ctx.guild.name
            else:
                guildname = guildname.replace("_", " ")
            try:
                await ctx.channel.trigger_typing()
                id_guild = await get_guild_id(guildname)
            except:
                id_guild = ""
                logger.error(msg["pt-br"]["rg"]["fail-ao"].format(guildname))
                await ctx.send(msg[language]["rg"]["fail-ao"].format(guildname))
            await ctx.channel.trigger_typing()
            #cf =  rguild(str(ctx.guild.id),id_guild, guildname,language)
            if is_guild_reg(ctx.guild.id):
                result = obter_dados(Guild,ctx.guild.id)
                result.name = guildname
                session.flush()
                result.id_ao = id_guild
                session.flush()
                result.lang = language
                session.commit()
                await ctx.send(msg[language]["rg"]["updated"].format(guildname))
            else:
                new = Guild(
                    id = ctx.guild.id,
                    name = guildname,
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
                    await ctx.send(msg[language]["rg"]["fail"].format(guildname) + ctx.author.mention) 
                else:
                    logger.info(msg["pt-br"]["rg"]["sucess"].format(guildname))
                    await ctx.send(msg[language]["rg"]["sucess"].format(guildname))
                    if new.id_ao != None != "":
                        await ctx.send(msg["pt-br"]["rg"]["players"]["search"].format(new.id_ao))
                        await get_new_players_in_guild(new)
                    else:
                        await ctx.send(msg["pt-br"]["rg"]["players"]["fail"])
        else:
            await ctx.send(msg[language]["rg"]["is-owner"] + ctx.author.mention)
    
    #comando para listar guilds registradas ok
    @commands.command(name="lg", help="Lists guilds registered in the bot")
    @commands.is_owner()
    async def guilds_list(self,ctx):
        '''
        LISTA GUILDS
        '''
        #print(commands.Bot.owner.name)
        try:
            datag = session.query(Guild).all()
        except discord.errors.HTTPException as e:
            logger.error(f"Bad request guild list: {e}")
        else:
            bf =""
            for g in datag:
                bf += g.name
                bf += "\n"
            logger.info("[lg] Ok!")
            await ctx.send(bf)
    
    #comando para cadastrar cargos(roles) ok
    @commands.command(name="rr", help="Requires prior registration. Add management positions")
    async def register_role(self,ctx, roles:str, language ="en-us"):
        #        '''
        #        REGISTRA CARGO NO BOT
        #        DEVE TER PERMISSÃO ADMIN
        #        '''
        idg = ctx.guild.id
        if is_guild_reg(idg):
            guildg = obter_dados(Guild,idg)
            if  guildg is None:
                    await ctx.send("<DB Error> not get GUILD! Try it")
                    return
            if is_guild_owner(ctx):
                    if roles not in cargos_list(idg):
                        new = Cargos(
                            name = roles,
                            guild_id = ctx.guild.id
                        )
                        add_dados(new)
                        logger.info(f"[rr] {ctx.guild.name} o {ctx.author.nick} registrou o cargo {roles}.")
                        await ctx.send(msg[guildg.lang]["rr"]["sucess"].format(ctx.guild.name,ctx.author.mention,roles))
                    else:
                        await ctx.send(f"<{roles}> has already been added!")
            else:
                await ctx.send(msg[guildg.lang]["rr"]["not-role"].format(ctx.guild.name, ctx.author.mention)) 
        else:
            await ctx.send(msg[language]["not-reg"])
    
    #comando para listar cargos adicionados ok
    @commands.command("lr", help="list added positions")
    async def lista_cargos(self,ctx):
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
            await ctx.send("Roles Not registred!\n[Owner Server] Use **?rr** for registration role administration.")
    
    #comando para adicionar isenção no player ok
    @commands.command("ai", help="Add player insention of tax")
    async def add_player_i(self,ctx, nick_player):
        if is_guild_reg(ctx.guild.id):
            if has_roles(ctx):
                add_isention(ctx.guild.id,nick_player)
                await ctx.send(f"{nick_player} added in insention!")
                remove_tax(ctx.guild.id,nick_player)
                await ctx.send(f"{nick_player} is removed from tax system!")
            else:
                await ctx.send("Not available role!")
        else:
            await ctx.send(msg["en-us"]["not-reg"])  
    
    #remove player da isenção ok 
    @commands.command("ri", help="remove player insention of tax system")
    async def re_player_i(self,ctx, nick_player):
        if is_guild_reg(ctx.guild.id):
            if has_roles(ctx):
                remove_isention(ctx.guild.id,nick_player)
                await ctx.send(f"{nick_player} is removed insention of tax system") 
            else:
                await ctx.send("Not available role!")
        else:
            await ctx.send(msg["en-us"]["not-reg"])
    #remove player da isenção ok
    @commands.command("rtax", help="remove player tax system")
    async def re_player_t(self,ctx, nick_player):
        if is_guild_reg(ctx.guild.id):
            if has_roles(ctx):
                gd = session.query(Members).get(ctx.guild.id)
                new_tax = session.query(Taxa).filter_by(name = nick_player,guild_id = ctx.guild.id).first()
                new_tax.deposito = 0
                session.flush()
                new_tax.saldo = gd.taxa_p
                session.flush()
                new_tax.ciclo = 1
                session.commit()
                await ctx.send(f"{nick_player} is removed from tax") 
            else:
                await ctx.send("Not available role!")
        else:
            await ctx.send(msg["en-us"]["not-reg"])                
    
    #checa taxa ok
    @commands.command("ti", help="check tax of player")
    async def ck_player_t(self,ctx, nick_player, lang="en-us"):
        dsid = str(ctx.guild.id)
        if is_guild_reg(dsid):
            dg = session.query(Guild).get(dsid)
            lang = dg.lang
            if is_tax_silver_system(dsid):
                if is_tax_exist(nick_player):
                    p = session.query(Taxa).get(nick_player)
                    m = session.query(Members).get(nick_player)
                    deposito = p.deposito
                    saldo = p.saldo
                    ciclo = p.ciclo
                    if not m.isention:
                        if saldo >0:
                            embed = discord.Embed(title= msg[lang]["tax"]["title"],color=discord.Color.green())
                            embed.add_field(name=msg[lang]["tax"]["saldo"], value=size(saldo,system=si))
                        else:
                            embed = discord.Embed(title= msg[lang]["tax"]["ck-title"],color=discord.Color.red())
                            embed.add_field(name=msg[lang]["tax"]["saldo"], value=f'{size(-saldo,system=si)}')
                        embed.description= nick_player
                        #embed.add_field(name=msg[lang]["tax"]["depo"], value=size(deposito,system=si))
                        embed.add_field(name=msg[lang]["tax"]["cicle"], value=ciclo)
                    else:
                        embed = discord.Embed(title= msg[lang]["tax"]["title"],color=discord.Color.blue())
                        embed.description= msg[lang]["tax"]["isention"]
                    
                    embed.add_field(name=msg[lang]["more"], value= msg[lang]["footer"], inline=False)

                    await ctx.send(embed=embed)
                else:
                    await ctx.send(msg[lang]["tax"]["not-pl"])
            else:
                await ctx.send(msg[lang]["tax"]["not-tax"])
        else:
            await ctx.send(msg[lang]["tax"]["no-reg"])
    '''
     TAREFAS DE TRANSMISSÕES DO TOP - TASKS
    '''
    # SISTEMA DE CONTRIBUIÇÃO
    @tasks.loop(hours=6)
    async def contrib_tax(self):
        datag = session.query(Guild).filter_by(top = True).all()
        #client = discord.Client()
        ss = 0
        for g in datag:
            lang = g.lang
            try:
                channel = bot.get_channel(g.canal_taxa)
            except :
                logger.error("Fail get channel for send contrib!")
                return
            logger.warning(f'Iniciando sistema de contribuição da guilda: {g.name}')
            taxa = session.query(Taxa).filter(Taxa.guild_id == g.id, Taxa.saldo < 0 ).all()
            embed = discord.Embed(title=msg[lang]["title_tax"], color = discord.Color.dark_magenta())
            desc = "\n"
            desc += f"Quantidade de inadiplente: {len(taxa)}\n\n\n"
            for p in taxa:
                desc += f'**{p.name}** \n {size(-p.saldo,system=si)}\n\n'
                ss+= int(p.saldo)
            desc += "\n\n\n" + msg[lang]["tax"]["info"].format(size(-ss,system=si))
            embed.add_field(name=msg[lang]["more"], value=msg[lang]["footer"], inline=False)
            embed.description= desc
            embed.set_footer(text = msg[lang]["tax"]["foot"])
            logger.info(f'Fim do sistema de contribuição da guilda: {g.name}')
            try:
                await channel.send(embed=embed)
            except:
                logger.debug(f"<{g.name}> Não foi possivel encontrar canal")
                
    #top pve
    @tasks.loop(hours=12)
    async def players_top_pve(self):
            logger.info("Trabalhando para emitir top semanal pve")
            datag = session.query(Guild).filter_by(top = True).all()
            for g in datag:
                if  g.top == True:
                    client = discord.Client()
                    if(g.canal_top is not None and g.id_ao is not None):
                        channel = bot.get_channel(g.canal_top)
                        logger.info(f"<{g.name}> Aguardando dados do Albion")
                        try:
                            d = await self.ranking_semanal(g.id_ao)
                        except:
                            logger.debug(f"<{g.name}> Não foi possivel enviar informações do top ranking")
                            await channel.send("Please verify re-register in bot. No get data from albion.")
                        embed = discord.Embed(title= msg[g.lang]["title_c"].format(g.name), color=discord.Color.gold())
                        for p in d:
                            if d[p]["Fame"] >1000:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=size(d[p]["Fame"],system=si), inline=False)
                            else:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=d[p]["Fame"], inline=False)
                        
                        embed.add_field(name= msg[g.lang]["more"], value=msg[g.lang]["footer"], inline=False)
                        
                        try:
                            await channel.send(embed=embed)
                        except:
                            logger.error("Não foi possivel enviar mensagem")

                        logger.info("Trabalho realizado com sucesso!")

    
    #top coletores
    @tasks.loop(hours=12)
    async def players_top_g(self):
            
            datag = session.query(Guild).filter_by(top = True).all()
            logger.info("Trabalhando para emitir top semanal coletor")
            for g in datag:
                if  g.top == True:
                    #client = discord.Client()
                    if(g.canal_top is not None and g.id_ao is not None):
                        channel = bot.get_channel(g.canal_top)
                        logger.info(f"<{g.name}>Aguardando dados do Albion")
                        try:
                            d = await self.ranking_semanal(g.id_ao, tipo_ranking= 1)
                        except:
                            logger.error("Não foi possivel enviar informações do top ranking")
                            await channel.send("Please verify re-register in bot. No get data from albion.")
                        embed = discord.Embed(title= msg[g.lang]["title_pve"].format(g.name), color=discord.Color.gold())
                        for p in d:
                            if d[p]["Fame"] >1000:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=size(d[p]["Fame"],system=si), inline=False)
                            else:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=d[p]["Fame"], inline=False)
                            
                        embed.add_field(name=msg[g.lang]["more"], value=msg[g.lang]["footer"], inline=False)

                        try:
                            await channel.send(embed=embed)
                        except:
                            logger.error("Não foi possivel enviar mensagem")

                        logger.info("Trabalho realizado com sucesso!")


    
    #obtem gerencia jogaores
    @tasks.loop(hours=8)
    async def gerencia_jogadores(self):    
        list_guild_reg = session.query(Guild).filter(Guild.id_ao != "" or Guild.id_ao != None).all()
        for guild in list_guild_reg:
            logger.info(f"Verificando removendo jogadores que sairam <{guild.name}>")
            await remove_players_in_guild(guild)
            logger.info(f"Verificando novos jogadores da guild <{guild.name}>")
            await get_new_players_in_guild(guild)
            logger.info(f"Sucess <{guild.name}>")
        logger.info("Tarefa de gerenciamento de jogadores concluido!")
        
    '''
    @tasks.loop(hours=12)
    async def players_top_pvp(self):
            
            datag = init_json(guilds)
            logger.info("Trabalhando para emitir top semanal pvp")
            for g in datag:
                #print(f' Quantidade de servidores: {len(datag)}')
                if "top" in datag[g]:
                    client = discord.Client()
                    channel = bot.get_channel(datag[f"{g}"]["canal_top"])
                    logger.info("Aguardando dados do Albion")
                    try:
                        d = await self.get_guild_top_kills(datag[f"{g}"]["id"], tipo_ranking= 1)
                        embed = discord.Embed(title= msg[datag[g]["lang"]]["title_pve"].format(datag[f"{g}"]["name"]), color=discord.Color.gold())
                        for p in d:
                            if d[p]["Fame"] >1000:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=size(d[p]["Fame"],system=si), inline=False)
                            else:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=d[p]["Fame"], inline=False)
                           
                        embed.add_field(name=msg[datag[g]["lang"]]["more"], value=msg[datag[g]["lang"]]["footer"], inline=False)
                        logger.info("Trabalho realizado com sucesso!")
                        await channel.send(embed=embed)
                    except:
                        logger.error("Não foi possivel enviar informações do top ranking")

    #negativados - lista de devedores de taxas_fixas
    
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
    async def registra_canal_top(self,ctx):
        if is_guild_reg(ctx.guild.id):
            datag = obter_dados(Guild,ctx.guild.id)
            if has_roles(ctx):
                
                datag.top = True
                session.flush()
                datag.canal_top = ctx.channel.id
                session.commit()
                logger.info(f"Canal para transmitir top semanal: {ctx.channel.name}")
                await ctx.send(f"Canal para transmitir top semanal: {ctx.channel.name}")
            else:
                await ctx.send(msg[datag.lang]["rg"]["is-owner"])
        else:
            await ctx.send(msg["en-us"]["not-reg"])
    
    #comando registra canal taxa
    @commands.command("rtx", help="Register channel for tax transmission")
    async def registra_canal_taxa(self,ctx, tax = 0, min_fame=0):
        if is_guild_reg(ctx.guild.id):
            datag = obter_dados(Guild,ctx.guild.id)
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
                await ctx.send(f"Canal para transmitir taxa: {ctx.channel.name}")
            else:
                await ctx.send(msg[datag.lang]["rg"]["is-owner"])
        else:
            await ctx.send(msg["en-us"]["not-reg"])
    
    #comando registra canal blacklist
    @commands.command("rb", help="Register channel for blacklist transmission")
    async def registra_canal_black(self,ctx):
        if is_guild_reg(ctx.guild.id):
            datag = obter_dados(Guild,ctx.guild.id)
            if has_roles(ctx):
                datag.canal_blacklist = ctx.channel.id
                session.commit()
                logger.info(f"({ctx.guild.id}) - Canal para transmitir blacklist: {ctx.channel.name}")
                await ctx.send(f"({ctx.guild.id}) - Canal para transmitir blacklist: {ctx.channel.name}")
            else:
                await ctx.send(msg[datag.lang]["rg"]["is-owner"])
        else:
            await ctx.send(msg["en-us"]["not-reg"])
    
    #comando registra canal 
    '''
    @commands.command("rgi", help="Register channel for guild info transmission")
    async def registra_canal_guild_info(self,ctx):
        if is_guild_reg(ctx.guild.id):
            datag = obter_dados(Guild,ctx.guild.id)
            if has_roles(ctx):
                datag.canal_info = ctx.channel.id
                session.commit()
                logger.info(f"({ctx.guild.id}) - Canal para transmitir info: {ctx.channel.name}")
                await ctx.send(f"({ctx.guild.id}) - Canal para transmitir info: {ctx.channel.name}")
            else:
                await ctx.send(msg[datag.lang]["rg"]["is-owner"])
        else:
            await ctx.send(msg["en-us"]["not-reg"])
    '''
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

    @commands.command("gpl", help = "list all players in guild")
    async def teste_top(self,ctx):
        players = session.query(Members).filter(Guild.id == ctx.guild.id).all()
        if not players:
            await ctx.send("Your guild has no players, or has not been registered in our junk")
        else:
            msg = ""
            count = len(players)
            embed = discord.Embed(title= f"Players({count}) List", color=discord.Color.gold())
            print(count)
            for p in players:
                msg += f"{p.name} \n"
            embed.description =  msg
            await ctx.send(embed=embed)
        logger.info("Fim de busca - players")


    @commands.command("gpc", help = "check player in guild")
    async def teste_top(self,ctx, nick):
        print(nick)
        player = obter_dados(Members,nick)
        if not player:
            embed = discord.Embed(title= f"player is no your guild, or has not been registered in our junk", color=discord.Color.red())
            #await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title= f"{player.name} is in {player.guild.name}", color=discord.Color.blue())
            # v= size(player.fame,system='si')
            # embed.description = f"Fame: {v}" 
        await ctx.send(embed=embed)
        logger.info("Fim de busca - players")