import os
import json
import logging
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, backref
from sqlalchemy import Column, Integer, String, Float,Boolean ,ForeignKey, BigInteger
from dotenv import load_dotenv

from services.data_json import *


#carrega arquivo .env
load_dotenv()
# atribui constantes 
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
STRINGSQL = os.getenv('STRING_SQL')
cfg = init_json("./data/config.json") #[path] configurações do bot
msg = init_json("./data/msg.json")


engine = create_engine(STRINGSQL, echo=False)
Base = declarative_base()
Session = sessionmaker(engine)
session = Session()

class Guild(Base):
    __tablename__ = 'guild'

    id = Column(BigInteger, primary_key=True)
    id_ao = Column(String)
    name = Column(String)
    lang = Column(String)
    top = Column(Boolean)
    taxap_s = Column(Boolean)
    taxac_s = Column(Boolean)
    canal_top = Column(BigInteger)
    canal_blacklist = Column(BigInteger)
    canal_taxa = Column(BigInteger)
    canal_info = Column(BigInteger)
    taxa_p =  Column(Integer)
    taxa =  Column(Integer)
    fame_taxa = Column(Integer)
    members = relationship("Members", back_populates='guild',cascade="all, delete, delete-orphan")
    blacklist = relationship("Blacklist", back_populates='guild', cascade="all, delete, delete-orphan")
    cargos  = relationship("Cargos", back_populates='guild',cascade="all, delete, delete-orphan")
    
    #field_data = relationship('members', backref="guild", uselist=False)
    ##relação

    def __repr__(self):
       return f"<Guild(id='{self.id}' |  name='{self.name}' | lang='{self.lang}' | members='{self.members}' | blacklist='{self.blacklist}')>"

class Members(Base):
    __tablename__ = 'members'
    name = Column(String, primary_key=True)
    id_ao = Column(String)
    fame = Column(BigInteger)
    guild_id = Column(BigInteger, ForeignKey("guild.id"))
    isention = Column(Boolean)
    #relacões
    guild =  relationship("Guild", back_populates="members", primaryjoin="Guild.id == Members.guild_id", uselist=False)
    taxa = relationship("Taxa", back_populates="member", cascade="all, delete, delete-orphan", uselist=False)
    def __repr__(self):
        return f"<Members(name='{self.name}'\n| guild='{self.guild.id} - {self.guild.name}' \n| taxa='{self.taxa}')>"

class Cargos(Base):
    __tablename__ = 'cargos'
    id = Column(Integer,autoincrement=True, primary_key=True) 
    name = Column(String)
    guild_id = Column(BigInteger, ForeignKey("guild.id"))
    guild =  relationship("Guild", back_populates="cargos")
    def __repr__(self):
        return f"<Cargos(name = '{self.name}'| {self.guild})>"

class Taxa(Base):
    __tablename__ = 'taxa'
    name = Column(String, ForeignKey("members.name"), primary_key=True)
    deposito = Column(Float)
    saldo = Column(Float)
    ciclo = Column(Float)
    member = relationship("Members", back_populates="taxa")
    guild_id = Column(BigInteger,ForeignKey("guild.id"))
    def __repr__(self):
        return "<Taxa(name='%s' | deposito='%s'| saldo='%s' | ciclo='%s')>" % (self.name, self.deposito,  self.saldo, self.ciclo)

class Blacklist(Base):
    __tablename__ = 'blacklist'
    
    name = Column(String,primary_key=True)
    reason = Column(String)
    police = Column(String)
    guild_id = Column(BigInteger, ForeignKey("guild.id"))
    guild = relationship("Guild", back_populates="blacklist")
    def __repr__(self):
        return "<Blacklist(name='%s' | motivo='%s'| police='%s')>" % (self.name, self.reason, self.police)

#verifica se a guild foi registrada
def is_guild_reg (id):
    return session.query(exists().where(Guild.id == id)).scalar() #retorna bool se existir
#verifica se a guilda tem sistema taxa de prata ativa
def is_tax_silver_system(id):
    return session.query(exists().where(Guild.id == id and Guild.taxp_s ==True)).scalar() #retorna bool se existir
#verifica se a guilda tem sistema de taxa de coleta ativa
def is_tax_grather_system(id):
    return session.query(exists().where(Guild.id == id and Guild.taxc_s ==True)).scalar()
#verifica se o player está na tabela membros
def is_player_exist(guild_id,nick_player):  
    return session.query(exists().where(Members.name == nick_player and Members.guild_id == guild_id)).scalar() #retorna bool se existir  
#verifica se o player tem contribuição
def is_tax_exist(nick_player):  
    return session.query(exists().where(Taxa.name == nick_player)).scalar() #retorna bool se existir
#verifica se o player está blacklistado
def is_blacklisted_from_guild(guild_id, nick_player):  
    return session.query(exists().where(
        Blacklist.name == nick_player 
        and Blacklist.guild_id == guild_id)).scalar() #retorna bool se existir

#verifica se existe o cargo
def is_cargo(guild_id, cargo):
    return session.query(exists().where(
        Cargos.name == cargo 
        and Cargos.guild_id == guild_id)).scalar() #retorna bool se existir

#lista todos os cargos da guilda
def cargos_list(guild_id):
    return session.query(Cargos).filter(Cargos.guild_id == guild_id).all()

#salvar dados no banco de dados (objetos)
def add_dados(mapper):
    print(mapper)
    session.add(mapper)
    session.commit()
#pegar objeto do banco de dados GUILD, MEMBRO, TAXA, CARGO, BLACKLIST
def obter_dados(mapper, pk):
    return session.query(mapper).get(pk)

def deletar_dados(mapper,pk):
    deletar = session.query(mapper).get(pk)
    session.delete(deletar)
    session.commit()


### admin
#remove player da taxa.json
def remove_tax(id,nick):
    if is_guild_reg(id):
        deletar_dados(Taxa,nick)
        return True
    else:
        logging.warning(f"GUILD <{id}> Não registrada. Não foi possivel remover: {nick}")
        return False
#checa player isention
def check_isention(id,nick):
    if is_guild_reg(id):
        return session.query(exists().where(
            Members.name == "nick" 
            and Members.isention == True)).scalar() 
    else:
        logging.warning(f"GUILD <{id}> Não registrada")
        return False

#remove player da isention
def remove_isention(id,nick):
    if is_guild_reg(id):
        if check_isention(id,nick):
            try:
               result = obter_dados(Members,nick)
               result.isention = False
               session.commit()
            except :
                return False
        else:
           logging.warning(f"GUILD <{id}> Não registrada")
           return False 
    else:
        logging.warning(f"GUILD <{id}> Não registrada")
        return False    
#adiciona player na isenção
def add_isention(id,nick):
    if is_guild_reg(id):
        if check_isention(id,nick):
            try:
               result = obter_dados(Taxa,nick)
               result.isention = True
               session.commit()
               return True
            except :
                return False
        else:
           logging.warning(f"GUILD <{id}> Não registrada")
           return False 
    else:
        logging.warning(f"GUILD <{id}> Não registrada")
        return False    

