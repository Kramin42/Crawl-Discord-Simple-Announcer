#!/usr/bin/env python3 
import discord
import asyncio
import socketio
import datetime
import json

with open('TOKEN', 'r') as f:
    TOKEN = f.read().strip()
print('Using token:', TOKEN)

with open('CHANNEL', 'r') as f:
    CHANNEL = f.read().strip()
print('Using channel ID:', CHANNEL)

with open('USERNAMES', 'r') as f:
    USERNAMES = [name.strip().lower() for name in f.read().split('\n') if name.strip()!='']
print('crawl usernames:', ', '.join(USERNAMES))

CRAWLAPI_SERVER = 'http://crawlapi.mooo.com/'

client = discord.Client()

loop = asyncio.get_event_loop()

sio = socketio.AsyncClient()

# formatter

def format_milestone(data):
    return data['name'] + \
        ' (L' + data['xl'] + ' ' + data['char'] + ') '+ \
        data['milestone'] + \
        ' (' + (data['oplace'] if ('oplace' in data and 'left' in data['milestone']) else data['place']) + \
        ') ['+data['src']+' '+data['v']+']'

def format_gameover(data):
    loc_string = ''
    if data['ktyp'] != 'winning' and data['ktyp'] != 'leaving':
        if ':' in data['place']:
            loc_string = ' on ' + data['place']
        else:
            loc_string = ' in ' + data['place']

    duration = str(datetime.timedelta(seconds=int(data['dur'])))
    
    return data['name'] + ' the ' + data['title'] + \
        ' (L' + data['xl'] + ' ' + data['char'] + ')' + \
        (' worshipper of ' + data['god'] if 'god' in data else '') + ', ' + \
        (data['vmsg'] if 'vmsg' in data else data['tmsg']) + \
        loc_string + ', with ' + \
        data['sc'] + ' points after ' + data['turn'] + ' turns and ' + duration + '.'

def format_event(event):
    data = event['data']
    data['src'] = event['src_abbr'].upper();
    if event['type'] == 'milestone':
        return format_milestone(data)
    else:
        return format_gameover(data)

# Discord handlers

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

# Socketio handlers

@sio.on('connect')
async def sio_on_connect():
    print('connected to socketio server')

@sio.on('crawlevent')
async def sio_on_crawlevent(data):
    for event in json.loads(data):
        if event['data']['name'].lower() in USERNAMES:
            await client.send_message(client.get_channel(CHANNEL), format_event(event))

async def start_sio():
    await sio.connect(CRAWLAPI_SERVER)
    await sio.wait()

try:
    loop.run_until_complete(asyncio.gather(
        client.start(TOKEN),
        start_sio()
    ))
except KeyboardInterrupt:
    print('Bye')
finally:
    loop.close()
