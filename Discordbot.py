from email import message
import urllib
import json
import discord
from discord.ext import commands
import os
import urllib.request
import valve.source.a2s 
from zipfile import ZipFile
import random
import time
import math


class URLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0"

opener = URLopener()

try:
    config =json.load(open('config.json'))
    print("config loaded")
except:
    config = {
        "discord":
        {
            "TOKEN":"",
            "prefix":"$"
        },
        "arkServerIP":[["123.456.7.890",12345]],
        "etherscanToken":"", 
        "whitelistchannels":[]
    }
    
    json.dump(config, open('config.json', 'w'))
    print("new config file made")
print(config)

#Discord Bot Config
TOKEN=config["discord"]["TOKEN"]

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=config["discord"]["prefix"], intents=intents)

#config
arkServerIP = config["arkServerIP"] 
etherscanToken = config["etherscanToken"]

whitelistchannels = config["whitelistchannels"] #channels with raised permissions

binanceFetchLimit = 1000        #number of things to fetch at a time
timeout = 5      #wait time on API limitation    
interval = '1m'     #time interval to fetch


#roles
try:
    roles =json.load(open('roles.json'))
    print("roles loaded")
except:
    roles = []
    
    json.dump(roles, open('roles.json', 'w'))
    print("new role file made")
print(roles)


#Ethereum wallet cache
try:
    wallet =json.load(open('wallet.json'))
    print("wallet loaded")
except:
    wallet = {}
    wallet["users"]=[]
    json.dump(wallet, open('wallet.json', 'w'))
    print("new wallet made")
print(wallet)

#Waifu cache
try:
    waifu =json.load(open('waifu.json'))
    print("waifus loaded")
except:
    waifu = {}
    waifu["users"]=[]
    json.dump(waifu, open('waifu.json', 'w'))
    print("new waifu made")
print(waifu)

def aquireJson(url):
    response = opener.open(url)
    data = json.loads(response.read())
    return data

    #returns the USD-CAD exchangerate (#of CAD per USD)
def USDfetch():
    data=aquireJson("https://www.bankofcanada.ca/valet/observations/FXUSDCAD?recent=1")
    return data["observations"][0]["FXUSDCAD"]["v"]
    
    
    #fetches price of crypto vs BUSD
def cryptofetch(crypto):
    data=aquireJson('https://api.binance.com/api/v3/klines?symbol='+crypto+'BUSD&limit=1&interval=1m')
    return float(data[0][4])
    
    #fetches price of crypto vs USDT and returns all time high
def cryptohigh(crypto):
    data=aquireJson('https://api.binance.com/api/v3/klines?symbol='+crypto+'USDT&limit='+str(binanceFetchLimit)+'&interval=1M')
    ATH=0
    for thing in data:
        if float(thing[2])>ATH:
            ATH=float(thing[2])
    return ATH
    
    
    #returns the worth of an ETH wallet
def walletWorth(wallet):
    content=aquireJson("https://api.etherscan.io/api?module=account&action=balance&address=" + wallet + "&tag=latest&apikey="+ etherscanToken)
    return float(content["result"])/1000000000000000000

    #checks if the channel is in the whitelist
def channelWhitelist(channel):
    inthelist = False
    for x in whitelistchannels:
        if channel.channel.id == x:
            inthelist = True
    return inthelist


#BOT START ---------------------------------------------------------------------------------------------------------------
@bot.event
async def on_ready():
    print('I think its time to blow this scene... get everyone and their stuff together')

    for channel in bot.get_all_channels():
        #print(channel)
        for message in roles:
            
            try:
                msg = await channel.fetch_message(message[0])
                print(str(channel)+"------------------------------")
                print(message)
                print(channel.category)
                print('FOUND')
                for emoji in message[1]:
                    await msg.add_reaction(emoji[0])
            except Exception as ex:
                #print(ex)
                continue
    print('------------------------------------------------------')
    print('OK, 3... 2... 1... LET\'S JAM')
    print('------------------------------------------------------')    


#reaction add zone
@bot.event
async def on_raw_reaction_add(reaction):
    if reaction.user_id != bot.user.id:
        for message in roles:
            if reaction.message_id == message[0]:
                print('Emoji:'+reaction.emoji.name)
                for emotes in message[1]:
                    if reaction.emoji.name == emotes[0]:
                        print(' adding role: '+str(emotes[1])+' to member '+ reaction.member.name)
                        await reaction.member.add_roles(discord.utils.get(bot.get_guild(reaction.guild_id).roles, name=emotes[1]))
    else:
        print("Wait thats me")
    
#reaction remove zone
@bot.event
async def on_raw_reaction_remove(reaction):
    if reaction.user_id != bot.user.id:    
        for message in roles:
            if reaction.message_id == message[0]:
                print('Emoji:'+reaction.emoji.name)
                for emotes in message[1]:
                    if reaction.emoji.name == emotes[0]:
                        print(' removing role: '+str(emotes[1])+' to member '+ bot.get_user(reaction.user_id).name)
                        await (bot.get_guild(reaction.guild_id)).get_member(reaction.user_id).remove_roles(discord.utils.get(bot.get_guild(reaction.guild_id).roles, name=emotes[1]))
    else:
        print("Wait thats me")


@bot.command(name='died', help = 'Dies.')
async def died(ctx):
    await ctx.send("I DIED")

@bot.command(name='usd', help = 'Returns the USD-CAD exchange rate.')
async def usd(ctx):
    
    await ctx.send("The exchange rate is currently " + str(USDfetch()) + "CAD to 1 USD" )


@bot.command(name='crypto', help = 'Returns the price of given cryptocurrency')
async def crypto(ctx, coin, *args):
    coin=coin.upper()
    coinprice = cryptofetch(coin)
    usdprice = USDfetch()
    #print(usdprice)
    response = "1 "+coin+" = " + str(round(float(coinprice) * float(usdprice),2)) + " CAD = " + str(coinprice) + " USD"
    if(len(args)>0):
        response = response + '\n'
        response = response + str(float(args[0]))+" "+coin+" = " + str(round(float(coinprice) * float(usdprice)*float(args[0]),2)) + " CAD = " + str(round(coinprice*float(args[0]),2)) + " USD"
    await ctx.send(response) 

@bot.command(name='eth', help = 'Returns the price of Ethereum')
async def eth(ctx, *args):
    ethprice = cryptofetch('ETH')
    usdprice = USDfetch()
    #print(usdprice)
    response = "1 ETH = " + str(round(float(ethprice) * float(usdprice),2)) + " CAD = " + str(ethprice) + " USD"
    if(len(args)>0):
        response = response + '\n'
        response = response + str(float(args[0]))+" ETH = " + str(round(float(ethprice) * float(usdprice)*float(args[0]),2)) + " CAD = " + str(round(ethprice*float(args[0]),2)) + " USD"
    await ctx.send(response) 

@bot.command(name='doge', help = 'Returns the price of Dogecoin')
async def doge(ctx, *args):
    dogeprice = float(cryptofetch('DOGE'))
    usdprice = USDfetch()
    #print(usdprice)
    response = "1 DOGE = " + str(round(float(dogeprice) * float(usdprice),2)) + " CAD = " + str(dogeprice) + " USD" + '\n'
    if(len(args)>0):
        response = response + str(float(args[0]))+" DOGE = " + str(round(float(dogeprice) * float(usdprice)*float(args[0]),2)) + " CAD = " + str(round(dogeprice*float(args[0]),2)) + " USD" + '\n'
    response = response + 'such profit'
    await ctx.send(response) 

@bot.command(name='arklist', help = 'lists online ARK players')
async def arklist(ctx):
    response="Online Players: "
    for IP in arkServerIP:
        try:
            with valve.source.a2s.ServerQuerier(IP) as server:
                players = server.players()
            for player in players["players"]:
                if player["name"] != "":
                    response = response + player["name"]+"," 
                    print(player["name"])
        except:
            print(IP[0]+ ":" + str(IP[1]) + " doesnt exist")
    await ctx.send(response)

@bot.command(name='setwallet', help = 'sets ethereum wallet')
async def setwallet(ctx, walletaddress):
    
    output = {"discID": str(ctx.message.author.id), "ETHwallet": walletaddress}
    for i in wallet["users"]:
        print("----------------")
        print(i["discID"] + " " + i["ETHwallet"])
        if str(i["discID"])==str(ctx.message.author.id):
            print("deleting....")
            wallet["users"].remove(i)
    wallet["users"].append(output)
    json.dump(wallet, open('wallet.json', 'w'))
    await ctx.send("Wallet set")

# @bot.command(name='payout', help = 'estimated time until next eth payout')
# async def payout(ctx):
    # await ctx.send()

@bot.command(name='profit', help = 'returns an estimate of the profitability based on nanopool hashrate')
async def profit(ctx):
    profit = aquireJson("https://api.nanopool.org/v1/eth/approximated_earnings/1")
    cad = float(USDfetch())
    response="No associated wallet"
    for i in wallet["users"]: 
        if str(i["discID"])==str(ctx.message.author.id):
            hashrate = aquireJson("https://api.nanopool.org/v1/eth/avghashratelimited/" + i["ETHwallet"] + "/24")
            response= "For wallet " + i["ETHwallet"]+"\n"
            response= response+ "with a hashrate of " + str(round(hashrate["data"],2)) + "MH/s" +"\n"
            response= response+ "Daily profit: " + str(round(hashrate["data"] * profit["data"]["day"]["dollars"], 2)) + "USD or " + str(round(hashrate["data"] * profit["data"]["day"]["dollars"] * cad, 2)) + "CAD" + "\n"
            response= response+ "Weekly profit: " + str(round(hashrate["data"] * profit["data"]["week"]["dollars"], 2)) + "USD or " + str(round(hashrate["data"] * profit["data"]["week"]["dollars"] * cad, 2)) + "CAD" + "\n"
            response= response+ "Monthly profit: " + str(round(hashrate["data"] * profit["data"]["month"]["dollars"], 2)) + "USD or " + str(round(hashrate["data"] * profit["data"]["month"]["dollars"] * cad, 2)) + "CAD"
        
    await ctx.send(response)    
        

@bot.command(name='w', help = 'waifu gatcha for the thristy fucking weebs')
async def w(ctx):
    output=""
    for i in waifu["users"]:
        print("----------------")
        print(str(i["discID"]) + " " + str(i["aquass"]))
        if str(i["discID"])==str(ctx.message.author.id):
            i["aquass"] = i["aquass"] + 1
            output = i["aquass"]
    if output == "":
        output = 1
        waifu["users"].append({"discID": str(ctx.message.author.id), "aquass": 1})
    json.dump(waifu, open('waifu.json', 'w'))
    
    titleoutput="Aquass"
    if output == 2:
        titleoutput=titleoutput + ", again"
    elif output > 2:
        titleoutput=titleoutput + ", again, it's been " + str(output) + " fucking times now, you goddamn degenerate."
    embed = discord.Embed(title=titleoutput)
    embed.add_field(name="Anime", value="Konosuba", inline=False)
    embed.set_image(url="https://media.discordapp.net/attachments/723433303973036105/820409200601333760/aquass.gif")
    await ctx.send(embed=embed)

@bot.command(name='balance', help = 'returns balance in the Ethereum wallet of the associated user')
async def balance(ctx):
    eth= float(cryptofetch('ETH'))
    cad= float(USDfetch())
    response="No associated wallet"
    for i in wallet["users"]: 
        if str(i["discID"])==str(ctx.message.author.id):
            bal=float(walletWorth(i["ETHwallet"]))
            response= "Wallet " + i["ETHwallet"]+ " contains" + "\n"
            response = response + str(bal) + "ETH" + "\n"
            response = response + "Valued at " + str(round(eth*bal,2)) + "USD or " + str(round(eth*bal*cad,2)) + "CAD"
    await ctx.send(response)
        
@bot.command(name='estimate', help = 'estimates days required to mine an amount of money based on hashrate and current balance')
async def estimate(ctx, amount, *args):
    amount=float(amount)
    bal = ""
    bal2 = ""
    saved =""
    profit = aquireJson("https://api.nanopool.org/v1/eth/approximated_earnings/1")
    cad = float(USDfetch())
    eth = float(cryptofetch('ETH'))
    flag= False
    if len(args)>0:
        if (args[0] == "us" or args[0] == "usd" or args[0] == "US" or args[0] == "USD"):
            amount = float(amount) * cad
    for i in wallet["users"]: 
        if str(i["discID"])==str(ctx.message.author.id):
            bal=float(walletWorth(i["ETHwallet"]))
            hashrate = aquireJson("https://api.nanopool.org/v1/eth/avghashratelimited/" + i["ETHwallet"] + "/24")
            bal2 = float(aquireJson("https://api.nanopool.org/v1/eth/balance/" + i["ETHwallet"] + "/")["data"])
            flag= True
            daily=hashrate["data"] * profit["data"]["day"]["dollars"]*cad
            saved=bal+bal2
    saved=saved*eth*cad
    days=round((amount-saved)/daily,1)
    await ctx.send("About " + str(days) + " days")

@bot.command(name='dragon', hidden = True)
async def dragon(ctx):
    await ctx.send("Crouching Tiger..... \n||HIDDEN DRAGON||")

@bot.command(name = 'whitelisttest', hidden = True)
async def whitelisttest(ctx):
    if (channelWhitelist(ctx)):
        await ctx.send("true")

@bot.command(name = 'ath', help = 'returns all time high')
async def ath(ctx, coin, *args):
    coin=coin.upper()
    coinprice = cryptofetch(coin)
    coinhighprice = cryptohigh(coin)
    usdprice = USDfetch()
    #print(usdprice)
    response = "The all time high price of "+coin+" is " + str(round(float(coinhighprice) * float(usdprice),2)) + " CAD or " + str(coinhighprice) + " USD"+"\n"
    if len(args)>0:
        if args[0]=="fomo":
            response = response + "The current price of "+coin+" is " + str(round(float(coinprice) * float(usdprice),2)) + " CAD or " + str(coinprice) + " USD" +"\n"
            response = response + "It's currently " + str(round(float(100*coinprice/coinhighprice),1)) +"% of the highest price."
    await ctx.send(response)

    
@bot.command(name = 'pfpbundle', help = 'returns everyone\'s profile pictures in a zip folder')
async def pfpbundle(ctx):
    tempName = str(int(1000 * random.random()))
    zipParts = 1
    zipName = 'bundled_pfp' + tempName + 'Part'+ str(zipParts)+'.zip'
    zipObj = ZipFile(zipName, 'w')
    for user in ctx.guild.members:
        if os.stat(zipName).st_size>7000000:
            zipObj.close()
            await ctx.send(file=discord.File(zipName))
            os.remove(zipName)
            zipParts = zipParts+1
            zipName = 'bundled_pfp' + tempName + 'Part'+ str(zipParts)+'.zip'
            zipObj = ZipFile(zipName, 'w')

        opener.retrieve(str(user.avatar_url_as(format='png', static_format='png', size=128)), tempName+'temppfp.png')
        zipObj.write(tempName+'temppfp.png', arcname = (user.display_name + '.png'))
        os.remove(tempName+'temppfp.png')
        
            

    zipObj.close()
    await ctx.send('Total Parts: '+str(zipParts), file=discord.File(zipName))
    os.remove(zipName)
    
@bot.command(name = 'roleadd', help = 'adds a new role. syntax: $roleadd ["role name"] [emoji]')
async def roleadd(ctx, role, emoji):
    if ctx.author.guild_permissions.administrator:
        roles =json.load(open('roles.json'))
        await ctx.guild.create_role(name=role)
        for channel in ctx.guild.channels:
            for rolemessage in roles:
                msg = ''
                try:
                    msg = await channel.fetch_message(rolemessage[0])
                    await msg.add_reaction(emoji)
                    rolemessage[1].append([emoji,role])
                except:
                    continue
        await ctx.send('created')
        json.dump(roles, open('roles.json', 'w'))
    else:
        await ctx.send('insufficient permissions')

@bot.command(name='savecalc', help = 'calculates savings growth with given income', usage = '-s starting savings (default 0),\n -p percent interest annually (default 8%),\n -y number of years (default 10),\n -t target amount (default $1,000,000),\n -si savings rate increase per year(default 0)')
async def savecalc(ctx, savings, *args):
    i = 0
    percent=1.08
    years=10
    targetamount=1000000
    si=0
    total=float(0)
    goalyears=0
    goalamount=0
    
    while(i<len(args)-1):
        if (args[i]=='-p'):
            percent = 1+float(args[i+1])/100
        elif(args[i]=='-y'):
            years = int(args[i+1])
        elif(args[i]=='-t'):
            targetamount=int(args[i+1])
        elif(args[i]=='-si'):
            si=int((args[i+1]))
        elif(args[i]=='-s'):
            total=int((args[i+1]))
        i=i+1
    i=0
    while((goalyears==0 or goalamount==0) and i<1000):
        total=total*percent
        total=total+int(savings)
        savings=int(savings)+si
        i=i+1 
        if(i==years):
            goalyears=total
        if(goalamount==0 and total>targetamount):
            goalamount=i
    response = "After " + str(years) + " years you would have saved $" + str(round(goalyears,2)) +"\n"
    response = response + "You would have saved $" + str(targetamount) + " after " + str(goalamount) + " years"
    await ctx.send(response)

bot.run(TOKEN)
