from pyrogram import filters
from Viora.config import POWER_COSTS,POWER_EFFECTS
async def register(app,c):
 p=c['powers']
 @app.on_message(filters.command('powers'))
 async def powers(_,m): await m.reply('⚡ <b>Viora Powers</b>\n'+'\n'.join(f"• {k.title()} — {v} gems/day\n  {POWER_EFFECTS[k]}" for k,v in POWER_COSTS.items())+'\n\n/pinfo <power>\n/act <power> <days>\n/mypowers or /mp\n/ph')
 @app.on_message(filters.command('pinfo'))
 async def pinfo(_,m):
  n=' '.join(m.command[1:]).lower(); key=next((x for x in POWER_COSTS if x in n),None); await m.reply(f'⚡ <b>{key.title()}</b>\nCost: {POWER_COSTS[key]} gems/day\n{POWER_EFFECTS[key]}' if key else '❌ Unknown power.')
 @app.on_message(filters.command('act'))
 async def act(_,m):
  if len(m.command)<3:return await m.reply('/act <power> <days>')
  ok,msg=await p.activate(m.from_user.id,m.command[1],int(m.command[2])); await m.reply(f'✅ Activated until {msg:%Y-%m-%d %H:%M UTC}.' if ok else '❌ '+msg)
 @app.on_message(filters.command(['mypowers','mp']))
 async def mp(_,m):
  rows=await p.active(m.from_user.id); await m.reply('⚡ Active powers:\n'+'\n'.join(f"• {k.title()} — {v['until']:%Y-%m-%d %H:%M UTC}" for k,v in rows.items()) if rows else 'No active powers.')
 @app.on_message(filters.command('ph'))
 async def ph(_,m): await m.reply('⚡ /powers list powers, /pinfo gives details, /act activates, /mypowers shows active powers.')
