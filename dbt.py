# bot.py
import os
import random
from albion_api_client import AlbionAPI as Ao
from hurry.filesize import size, si
import discord
from discord.colour import Color
from dotenv import load_dotenv
from discord.ext import commands
import json
with open("config.json") as cfg_file:
    cfg = json.load(cfg_file)
 
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

ao = Ao()
bot = commands.Bot(command_prefix='!')

atividades= cfg["atividades"]

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'')
    atividade = random.choice(atividades)
    activity = discord.Game(name=atividade, type=3)
    await bot.change_presence(status=discord.Status.idle, activity=activity)

class Membro (commands.Cog):
    '''
    CLASSE DESTINADA À PLAYERS
    '''
    @commands.command(name = 'pi', help= "Consulta informações do player no Albion")
    async def player_info(self, ctx, nick:str):
        await ctx.channel.trigger_typing()
        print(f"[pi] {ctx.author.nick} procurando player {nick}")
        try:
            p_id = ao.get_player_id(nick)
            print(f"[pi] {ctx.author.nick} - Jogador ID:{p_id}")
        except:
            print(f"[pi] {ctx.author.nick} deu error ao consultar id")
            await ctx.send(f"{ctx.author.nick} Tente novamente, houve um problema com o trajeto.")
            return
        print(f"[pi] {ctx.author.nick} procurando informações do {nick}")
        await ctx.channel.trigger_typing()
        try:
            p_info = ao.get_player_info(p_id)
        except:
            print(f"[pi] {ctx.author.nick} deu error ao consultar as informações")
            await ctx.send(f"{ctx.author.nick} Tente novamente, houve um problema com o trajeto das informações do jogador.")
            return
        print(f"[pi] {ctx.author.nick} procurando as covas que o {nick} fez")
        await ctx.channel.trigger_typing()
        try:
            p_kills = ao.get_player_kills(p_id)
            print(f"[pi] {ctx.author.nick} Quantidade de kills: {len(p_kills)}")
        except:
            print(f"[pi] {ctx.author.nick} deu error ao consultar as kills")
            await ctx.send(f"{ctx.author.nick} Tente novamente, houve um problema com o cemiterio. Não foi possivel obter os defuntos!")
            return
        print(f"[pi] {ctx.author.nick} Quantidade de dados: {len(p_info)} do {nick}")
        if len(p_info)>0:
            
            pvp = int(round(p_info['KillFame']))
            pve = int(round(p_info['LifetimeStatistics']['PvE']['Total']))
            coleta = int(round(p_info['LifetimeStatistics']['Gathering']['All']['Total']))
            crafting = int(round(p_info['LifetimeStatistics']['Crafting']['Total']))
            total = int(round(pvp+pve+coleta+crafting))
            data_att = p_info['LifetimeStatistics']['Timestamp']

            embed = discord.Embed(title= f"🤖 {p_info['Name']} 📂", color = discord.Color.dark_blue())
            embed.description = f"Tem  🏆 **{size(total,system=si)}** 🏆  de **FAMA** total\n\n🧙🏻 Fama PVE: **{size(pve, system=si)}**\n🎯 Fama PVP: **{size(pvp, system=si)}**\n⚒ Fama de Coleta: **{size(coleta,system=si)}**\n🛠 Crafting: **{size(crafting, system=si)}**"
            embed.set_footer(text=f"Player atualizado em {data_att} pelo Albion. Bot by: LeandroLimaPRO#0227. AODATA ")
            #print(len(p_kills))
            kills =""
            for k in p_kills:
                kills= kills + f"\n**[{k['Victim']['AllianceName']}] {k['Victim']['Name']}** em {k['KillArea']} em {k['TimeStamp'][0:10]}"
            if len(p_kills)>0:
                embed.add_field(name= "⚰️ Abriu a cova de",value=kills)   
            else:
                embed.add_field(name= "Não matou Ninguém!",value="🧸")  
            await ctx.send(embed=embed)
            print(f"[pi] {ctx.author.nick} Player consultado com sucesso!\n")
        else:
            print(f"[pi] {ctx.author.nick} Player Não Encontrado!\n")

class Coletor(commands.Cog):
    def __init__(self, bot):
        global cfg
        self.bot = bot #objeto discord
        self.taxa_nova = int(cfg["taxa"]) #valor guardado da taxa
        self.a_doar = 0 # valor de doação  para o usario do comando

    def doacao_coleta(self,fame_semanal, t_doar, taxa):
        '''
        calcula a taxa de doação de coleta
        '''
        if    t_doar == 5:
            return round(((fame_semanal/100)* taxa)/22)
        elif  t_doar == 6:
            return round(((fame_semanal/100)* taxa)/33)
        elif  t_doar == 7:
            return round(((fame_semanal/100)* taxa)/44)
        elif  t_doar == 8:
            return round(((fame_semanal/100)* taxa)/55)
        else:
            return 0

    @commands.command(name = 'mudartaxa', help= "Mudar taxa de coleta da guilda")
    @commands.has_any_role("❪🚑❱Braço Direito","❪🚑❱Mestre de guilda")
    async def mudar_taxa(self,ctx,nova_taxa:int):
        cfg["taxa"] = int(nova_taxa)
        with open("config.json", "w") as cfg_file:
            json.dump(cfg,cfg_file,ident=2)
        await ctx.send(f"Taxa de coleta foi alterada para {self.taxa_nova}%")


    @commands.command(help= "Retorna taxa atual")
    async def taxa(self,ctx):
        await ctx.send(f"Taxa de coleta é de {self.taxa_nova}%")

    @commands.command(name = 'c', help = "Calcula a contribuição da semana de coleta") #calculadora de taxa de coleta
    async def calcular_taxa_coleta(self,ctx, fama_coleta_semanal: int, tier: int, help= "Quanto você deverá doar de coleta. Precisa-se da sua fama semanal e o tier que deseja coletar"):
        self.a_doar = self.doacao_coleta(fama_coleta_semanal, tier, self.taxa_nova)
        print(f"[c]{ctx.author.nick}: {self.a_doar} de T{tier}")
        if int(self.a_doar) == 0:
            cor = Color.blurple()
            resposta = f"Tente novamente. Lembre-se não aceitamos Tiers abaixo do 5"
        else:
            cor = Color.dark_blue()
            resposta = f"Contribua com **{self.a_doar}** de recursos no **T{tier}**."

        embeds = discord.Embed(title=ctx.author.nick, color =  cor)
        embeds.description = f"{resposta}\n\nLembre-se de colocar os recursos no bau de doação! \nNão esqueça de contatar um oficial."
        fot = f".:Taxa de {self.taxa_nova}%:. | Bot by: @LeandroLimaPRO#0227"
        embeds.set_footer(text = fot)
        await ctx.send(embed=embeds)


bot.add_cog(Coletor(bot))
bot.add_cog(Membro(bot))
bot.run(TOKEN)
