import secrets
from pyrogram import filters
from Viora.core.common import amount,money
async def register(app,c):
 db=c['db']; e=c['economy']; p=c['premium']
 async def admin(m):
  try:
   x=await app.get_chat_member(m.chat.id,m.from_user.id); return bool(x.privileges and (x.privileges.can_manage_chat or x.privileges.can_change_info))
  except:return False
 @app.on_message(filters.command('create_coupon') & filters.group)
 async def create(_,m):
  if not await admin(m) or not await p.active(m.from_user.id):return await m.reply('❌ Group admin + Premium required.')
  if len(m.command)<3:return await m.reply('/create_coupon <code> <amount>')
  code=m.command[1].upper()
  try:n=amount(m.command[2])
  except:return await m.reply('❌ Invalid amount.')
  if not await e.remove(m.from_user.id,n):return await m.reply('❌ Not enough balance.')
  try: await db.coupons.insert_one({'chat_id':m.chat.id,'code':code,'amount':n,'remaining':n,'creator':m.from_user.id,'created_at':__import__('datetime').datetime.utcnow()})
  except Exception: await e.add(m.from_user.id,n); return await m.reply('❌ Coupon code already exists.')
  await m.reply(f'🎟️ Coupon <code>{code}</code> created with {money(n)}.')
 @app.on_message(filters.command('coupon') & filters.group)
 async def coupon(_,m):
  if len(m.command)<2:return await m.reply('/coupon <code>')
  code=m.command[1].upper(); row=await db.coupons.find_one_and_update({'chat_id':m.chat.id,'code':code,'remaining':{'$gt':0}},{'$set':{'remaining':0},'$setOnInsert':{}},return_document=__import__('pymongo').ReturnDocument.BEFORE)
  if not row:return await m.reply('❌ Invalid or already claimed coupon.')
  try: await db.coupon_claims.insert_one({'chat_id':m.chat.id,'code':code,'user_id':m.from_user.id,'at':__import__('datetime').datetime.utcnow()})
  except Exception: await db.coupons.update_one({'_id':row['_id']},{'$set':{'remaining':row['remaining']}}); return await m.reply('❌ Already claimed.')
  await e.add(m.from_user.id,row['remaining']); await m.reply(f'🎉 Coupon claimed: {money(row["remaining"])}')
 @app.on_message(filters.command('del_coupon') & filters.group)
 async def delete(_,m):
  if not await admin(m):return await m.reply('❌ Admin only.')
  if len(m.command)<2:return await m.reply('/del_coupon <code>')
  row=await db.coupons.find_one_and_delete({'chat_id':m.chat.id,'code':m.command[1].upper()});
  if row and row.get('remaining',0): await e.add(row['creator'],row['remaining'])
  await m.reply('✅ Deleted.' if row else '❌ Not found.')
 @app.on_message(filters.command('status') & filters.group)
 async def status(_,m):
  rows=await db.coupons.find({'chat_id':m.chat.id}).sort('created_at',-1).limit(20).to_list(20); await m.reply('🎟️ Coupons\n'+'\n'.join(f"{x['code']} — {money(x['remaining'])} left" for x in rows) or 'No coupons.')
 @app.on_message(filters.command('coupons'))
 async def coupons(_,m): return await status(_,m)
