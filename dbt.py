# bot.py
import os
import random
import discord
from dotenv import load_dotenv
from discord.ext import commands
import json
try:
    f = open("config.json", "w+")
except:
    print("ERROR AO ABRIR CONFIGURAÇÕES")

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='?')

atividades= ["Albion Online","Coletando difuntos no Albion", "Coletando Trash", "Tô aqui!"]
taxa_nova = 20
def doacao_coleta(fame_semanal, t_doar, taxa):
    if    t_doar == 5:
        return round(((fame_semanal/100)*taxa)/22)
    elif  t_doar == 6:
        return round(((fame_semanal/100)*taxa)/33)
    elif  t_doar == 7:
        return round(((fame_semanal/100)*taxa)/44)
    elif  t_doar == 8:
        return round(((fame_semanal/100)*taxa)/55)
    else:
        return 0

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'')
    atividade = random.choice(atividades)
    activity = discord.Game(name=atividade, type=3)
    await bot.change_presence(status=discord.Status.idle, activity=activity)


@bot.command(name = 'mudartaxa', help= "Mudar taxa de coleta da guilda")
@commands.has_any_role("❪🚑❱Braço Direito","❪🚑❱Mestre de guilda")
async def mudar_taxa(ctx,nova_taxa:int):
    global taxa_nova
    taxa_nova = nova_taxa
    await ctx.send(f"Taxa de coleta foi alterada para {taxa_nova}%")


@bot.command(help= "Retorna taxa atual")
async def taxa(ctx):
    global taxa_nova
    await ctx.send(f"Taxa de coleta é de {taxa_nova}%")
@bot.command(name = 'c', help = "Calcula a contribuição da semana de coleta") #calculadora de taxa de coleta
async def calcular_taxa_coleta(ctx, fama_coleta_semanal: int, tier: int, help= "Quanto você deverá doar de coleta. Precisa-se da sua fama semanal e o tier que deseja coletar"):
    a_doar = doacao_coleta(fama_coleta_semanal, tier, taxa_nova)
    
    if a_doar == 0:
        cor = 0xff0000 #cor vermelha
        resposta = "Tente novamente. Lembre-se não aceitamos Tiers abaixo do 5"
    else:
        cor = 0x00ff00 #cor azul
        resposta = f'contribua com {a_doar} de recursos no T{tier}.'

    embeds = discord.Embed(title=ctx.author.nick + " " + resposta, color = cor)
    embeds.description = "Lembre-se de colocar os recursos no bau de doação! \nNão esqueça de contatar um oficial."
    fot = f".:Taxa de {taxa_nova}%:. | Bot by: @LeandroLimaPRO#0227"
    embeds.set_footer(text = fot)
    await ctx.send(embed=embeds)



bot.run(TOKEN)