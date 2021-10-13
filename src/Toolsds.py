from .inits import *
from os import remove

class Tools(commands.Cog):
    #função retorna fama coletada na semana
    async def fama_coleta_semanal(self, idguild:str ,player:str):
        logger.info("Iniciando coleta de estatistica")
        #stats_ = await get_statistics_guild(idguild, range= "week", types="Gathering", subtype="All")
        try:
            stats_ = await get_statistics_guild(guild_id=idguild, range=0, types=1, limit = 100)
        except :
            logger.error("Não foi possivel  obter estatisticas")      
            return 0
        if len(stats_)>2:
            logger.debug(stats_)
            logger.info("Encontrou dados!")
            c = 0
            logger.info(f'Quantidade de players: {len(stats_)}')
            for p in stats_:
                c +=1
                pname = p["Player"]["Name"]
                pfame = p["Fame"]
                #print(f'{pname} | contagem {c}')
                if pname  == player:
                    logger.info(f"COLETA! {pname} : {pfame}")
                    return pfame
                elif len(stats_) == c:
                    logger.info(f"Player não consta no Top ranking")
                    return 1
        else:
            logger.warning("Não há dados no banco do albion")
            return 0
    #função calcula doação de coleta baseada na fama    
    async def doacao_coleta(self, fame_semanal=0, t_doar=5, taxa=0):
        '''
        calcula a taxa de doação de coleta
        fama_semanal : int
        t_doar: int
        taxa: int
        '''
        val = 0
        if t_doar == 5:
            val = round(((fame_semanal/100)* taxa)/22)
            return val
        elif  t_doar == 6:
            val = round(((fame_semanal/100)* taxa)/33)
            return val
        elif  t_doar == 7:
            val = round(((fame_semanal/100)* taxa)/44)
            return val
        elif  t_doar == 8:
            val = round(((fame_semanal/100)* taxa)/55)
            return val
        else:
            return val
    #comando muda taxa de doação
    @commands.command(name = 'mt', help= "Change guild Gathering rate")
    async def mudar_taxa(self,ctx,tax_colector=0,tax_silver = 0, min_fame=0):
        guildb = obter_dados(Guild, ctx.guild.id)
        if has_roles(ctx):
            if tax_colector !=guildb.taxa or tax_colector>0:
                guildb.taxa= int(tax_colector)
                guildb.taxac_s = True
                session.flush()
            if tax_silver != guildb.taxa_p or tax_silver>0:
                guildb.taxa_p = int(tax_silver)
                guildb.taxap_s = True
                session.flush()
            if min_fame != guildb.fame_taxa or min_fame>0:
                guildb.fame_taxa = int(min_fame)
                guildb.taxap_s = True
                session.flush()
            session.commit()
            logger.info(f"[mudartaxa] {ctx.guild.name} Taxa de coleta foi alterada para {tax_colector}%")
            await ctx.send(msg[guildb.lang]["mt"]["sucess"].format(tax_colector))

        else:
            await ctx.send(msg[guildb.lang]["not-role"])
    #comando envia dados de contribuição de taxa fixa
    @commands.command(name = 'cts', help= "Sends contribution deposit data")
    async def contribuicoes_taxas_semanais(self,ctx):
        await ctx.channel.trigger_typing()
        lang = "en-us"
        #variaveis locais inicializadas
        total = 0 #variavel de prata total arrecadado
        #totaldp = 0
        #totalsal = 0
        id_ = str(ctx.guild.id) #id do discord
        file_ = f'./balances/cts{id_}.txt' #local  onde será salvo o arquivo de texto com nome
        #taxa_file =  #[path] do banco de pagamento de taxa
        if has_roles(ctx):
            #print("role passou!")
            #verifica se a guild foi registrada
            if is_guild_reg(id_):
                #print("guild registrado")
                g = obter_dados(Guild, id_) #inicializa banco de guilds
                tx = session.query(Taxa).filter_by(guild_id = id_).all() #inicializa banco de taxas
                lang = g.lang #obtem lingua apartir do banco
                taxa_p = g.taxa_p
                # import requests 
                attachment_url = ctx.message.attachments[0].url
                # file_request = requests.get(attachment_url)
                resp = requests.get(f"{attachment_url}")
                ## obtem respose converte e decotifica para string utf8
                resp = str(resp.content, encoding="utf-8")
                #formata arquivo de balanço
                out = balance_form(resp)
                #verifica se o arquivo existe se exstir apaga
                await ctx.channel.trigger_typing()
                if os.path.exists(file_):
                    remove(file_)
                #cria arquivo para salvar
                f = open(file_, "a+",encoding='utf-8')
                #grava o content (string) do response no arquivo
                f.write(out)
                f.write("\n")
                f.flush()#libera
                f.close()#fecha arquivo
                await ctx.channel.trigger_typing()
                await asyncio.sleep(1) #aguarda alguns segundos
                #tenta ler arquivo de texto criado
                await ctx.channel.trigger_typing()
                try:
                    data= read_txt(file_)
                except:
                    await ctx.send("Error ao ler arquivo")
                    return
                #INTERFACE - cria embed do discord
                embed= discord.Embed(title=msg[lang]["tax"]["title"], color=discord.Color.dark_gold())
                desc =""
                total = 0
                await ctx.channel.trigger_typing()
                for p in data:
                    pl = p["Jogador"]
                    qt = float(p["Quantidade"])
                    total += qt
                    embed.add_field(name=pl, value=size(qt, system=si), inline=False)
                    for j in tx:
                        if j.name == pl:
                            dep = qt
                            sal = j.saldo + dep
                            j.deposito = dep
                            session.flush()
                            j.saldo = sal
                            session.flush()
                session.commit()
                await ctx.channel.trigger_typing()
                desc += msg[lang]["tax"]["info-dep"].format(size(total,system=si))
                embed.description = desc
                embed.add_field(name=msg[lang]["more"],value=msg[lang]["footer"])
                await ctx.send(embed=embed)
            else:
                await ctx.send(msg[lang]["not-reg"])
        else:
            await ctx.send(msg[lang]["not-role"])
    @commands.command(name = 'at', help= "Starts new contribution period (adds + fee to be paid)")
    async def atualiza_periodo(self, ctx, lang = "en-us"):
        id_ = str(ctx.guild.id) #id do discord
        #taxa_file = cfg["taxa_fixa"] [path] do banco de pagamento de taxa
        tx =session.query(Taxa).filter_by(guild_id = id_).all() #inicializa banco de taxas
        if has_roles(ctx) or is_guild_owner(ctx):
            #verifica se a guild foi registrada
            if is_guild_reg(id_):
                g = obter_dados(Guild, id_) #inicializa banco de guilds
                lang = g.lang #obtem lingua apartir do banco
                taxa_p = g.taxa_p
                for p in  tx:
                    if p.ciclo >=1 :
                        sal = p.saldo
                        p.ciclo += 1
                        session.flush()
                        p.saldo = sal - taxa_p
                        session.flush()
                session.commit()
                await ctx.send(f"{ctx.author.mention} A **new cycle** has started! Debit of **{size(taxa_p,system=si)}** has been added to taxpayers")
            else:
                await ctx.send(msg[lang]["not-reg"])
        else:
            await ctx.send(msg[lang]["not-role"])
    #comando retorna a taxa atual da guilda
    @commands.command(name="tax",help= "Return tax")
    async def taxa(self,ctx):
        await ctx.channel.trigger_typing()
        datag = obter_dados(Guild,ctx.guild.id)
        taxa = datag.taxa
        await ctx.send(msg[datag.lang]["tax"]["sucess"].format(taxa))
    #comando para retornar a taxa de contribuição
    @commands.command(name = 'c', help= "How much should you donate collection. Your weekly fame and the level you want to collect are needed.") #calculadora de taxa de coleta
    async def calcular_taxa_coleta(self,ctx, nick_player: str, tier, lang="en-us"):
        await ctx.channel.trigger_typing()
        idg=str(ctx.guild.id)
        tier = int("".join(filter(str.isdigit, tier)))
        if is_guild_reg(idg):
            datag = obter_dados(Guild,idg)
            guild_name = datag.name
            guild_id = datag.id
            lang = datag.lang
            if is_tax_grather_system(idg):
                taxa = datag.taxa
                
                await ctx.channel.trigger_typing()
                try:
                    fama_coleta = await self.fama_coleta_semanal(guild_id,nick_player)
                except:
                    fama_coleta = 0
                    logger.error("Não foi Possivel Obter fama de coleta")
                a_doar = await self.doacao_coleta(fama_coleta,tier,taxa)

                #logger.info(f"{type(taxa)} || {type(fama_coleta)}:{fama_coleta} ")
                if fama_coleta < 1000:
                    info_player= f"{fama_coleta}"
                else:
                    info_player = f"{size(fama_coleta,si)}"
                        #print(f"{fama_coleta}::{a_doar} :::{taxa}")
                await ctx.channel.trigger_typing()
                await ctx.send(ctx.author.mention)
                embeds = discord.Embed(title=f'{nick_player} deve contribuir com', color =  Color.darker_grey())     
                if int(a_doar) == 0:
                    cor = Color.blurple()
                    resposta = f"Tente novamente. Lembre-se não aceitamos Tiers abaixo do 5"
                else:
                        cor = Color.dark_blue()
                        embeds.add_field(name="Quantidade de recursos", value=a_doar)
                        embeds.add_field(name= "Tier dos recursos", value=f'T{tier}')
                        #resposta = f"**{nick_player}** você deve pagar **{a_doar}** unidades de recursos no **T{tier}**."
                embeds.add_field(name= "Fama Semanal", value = info_player)
                embeds.add_field(name="Observações", value= f"\n\nLembre-se de colocar os recursos no bau de doação! \nNão esqueça de contatar um oficial.", inline=False)
                    
                embeds.set_thumbnail(url="https://raw.githubusercontent.com/LeandroLimaPRO/tesourAO/main/images/paypal_qr.png")
                    
                fot2 = f"Taxa de {taxa}% contribubição da guilda.\n" + fot
                embeds.add_field(name= "Mais", value=fot2, inline=False)
                    #embeds.set_footer(text = fot)
                logger.info(f"[c]{a_doar} de T{tier}. FAMA TOTAL {fama_coleta}")
                await ctx.send(embed=embeds)
            else:
                await ctx.send(msg[lang]["not-tax"])
        else:
            await ctx.send(msg[lang]["not-reg"])
        
