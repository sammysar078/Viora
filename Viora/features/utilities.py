import re, io, math, ast, operator, aiohttp, os, tempfile, subprocess
from pyrogram import filters
from Viora.core.common import target_from_reply,mention,amount
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Mod:operator.mod,ast.Pow:operator.pow,ast.USub:operator.neg}
def calc_node(n):
 if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)):return n.value
 if isinstance(n,ast.BinOp) and type(n.op) in OPS:return OPS[type(n.op)](calc_node(n.left),calc_node(n.right))
 if isinstance(n,ast.UnaryOp) and type(n.op) in OPS:return OPS[type(n.op)](calc_node(n.operand))
 raise ValueError
def safe_calc(s): return calc_node(ast.parse(s,mode='eval').body)
async def register(app,c):
 db=c['db']; api=c['api']; e=c['economy']
 @app.on_message(filters.command('calc'))
 async def calc(_,m):
  s=' '.join(m.command[1:]).strip().lower()
  try:
   pct=re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)\s*(?:%|percent)\s*(?:of|ka)?\s*([0-9]+(?:\.[0-9]+)?)',s)
   hindi=re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)\s*ka\s*([0-9]+(?:\.[0-9]+)?)\s*%',s)
   if pct: out=float(pct.group(2))*float(pct.group(1))/100
   elif hindi: out=float(hindi.group(1))*float(hindi.group(2))/100
   else: out=safe_calc(s)
   await m.reply(f'🧮 <code>{out:g}</code>')
  except Exception: await m.reply('❌ Invalid calculation.')
 @app.on_message(filters.command('c'))
 async def ccalc(_,m): return await calc(_,m)
 @app.on_message(filters.command('font'))
 async def font(_,m):
  if len(m.command)<3:return await m.reply('/font 1|2|3|4 <text>')
  st=int(m.command[1]); text=' '.join(m.command[2:]); maps=[str.maketrans('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ','ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖᑫʳˢᵗᵘᵛʷˣʸᶻᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᑫᴿˢᵀᵁⱽᵂˣʸᶻ')]
  if st==1:out=''.join(f'𝙎𝙩𝙮𝙡𝙚 {x}' for x in []) or text.swapcase()
  elif st==2:out=' '.join(''.join(f'[{ch}]' for ch in w) for w in text.split())
  elif st==3:out=''.join('ᴬ' if x=='A' else x for x in text)
  else:out=text.translate(maps[0])
  await m.reply(out)
 @app.on_message(filters.command('tr'))
 async def tr(_,m):
  if not c['config'].LIBRETRANSLATE_URL:return await m.reply('🌐 Translation API is not configured.')
  if len(m.command)<3:return await m.reply('/tr <language> <text>')
  async with aiohttp.ClientSession() as s:
   data={'q':' '.join(m.command[2:]),'source':'auto','target':m.command[1]};
   if c['config'].LIBRETRANSLATE_API_KEY:data['api_key']=c['config'].LIBRETRANSLATE_API_KEY
   async with s.post(c['config'].LIBRETRANSLATE_URL+'/translate',data=data) as r: out=await r.json()
  await m.reply(out.get('translatedText','❌ Translation failed.'))
 @app.on_message(filters.command('admins') & filters.group)
 async def admins(_,m):
  rows=[]
  async for x in app.get_chat_members(m.chat.id,filter=__import__('pyrogram').enums.ChatMembersFilter.ADMINISTRATORS): rows.append(mention(x.user))
  await m.reply('👮 <b>Admins</b>\n'+'\n'.join(rows))
 @app.on_message(filters.command('owner'))
 async def owner(_,m): await m.reply('👑 Owners: '+', '.join(map(str,c['config'].OWNER_IDS)) if c['config'].OWNER_IDS else 'Not configured')
 @app.on_message(filters.command('report') & filters.reply)
 async def report(_,m):
  await db.reports.insert_one({'chat_id':m.chat.id,'reporter':m.from_user.id,'message_id':m.reply_to_message.id,'created_at':__import__('datetime').datetime.utcnow()}); await m.reply('🚨 Report sent to Viora admins.')
 @app.on_message(filters.command('detail'))
 async def detail(_,m):
  t=target_from_reply(m) or m.from_user; rows=await db.name_history.find({'user_id':t.id}).sort('at',-1).limit(20).to_list(20); await m.reply(f'🔎 <b>{mention(t)}</b>\n'+('\n'.join(f"{x.get('name','')} @{x.get('username','')}" for x in rows) or 'No history recorded by Viora yet.'))
 @app.on_message(filters.command('isdeleted'))
 async def deleted(_,m):
  if len(m.command)<2:return await m.reply('/isdeleted <user id>')
  try: u=await app.get_users(int(m.command[1])); await m.reply(f'🟢 User resolves as {mention(u)}; not deleted/inaccessible.')
  except: await m.reply('🔴 Telegram could not resolve this user ID. This is not proof of deletion.')
 @app.on_message(filters.command('voice'))
 async def voice(_,m):
  try:
   import edge_tts, tempfile, os
   text=' '.join(m.command[1:]) or (m.reply_to_message.text if m.reply_to_message else '')
   if not text:return await m.reply('/voice <text>')
   f=tempfile.NamedTemporaryFile(suffix='.mp3',delete=False).name; await edge_tts.Communicate(text,'en-US-AriaNeural').save(f); await m.reply_audio(f); os.unlink(f)
  except Exception as ex: await m.reply('🔊 TTS is unavailable on this server.')
 @app.on_message(filters.command('q'))
 async def quote(_,m):
  src=m.reply_to_message
  if not src:
   text=' '.join(m.command[1:]).strip()
   if not text:return await m.reply('❌ Reply to a photo/media or use /q <text>.')
   from PIL import Image, ImageDraw, ImageFont
   img=Image.new('RGB',(800,450),'white'); draw=ImageDraw.Draw(img); font=ImageFont.load_default()
   lines=[]; words=text.split(); line=''
   for w in words:
    test=(line+' '+w).strip()
    if draw.textlength(test,font=font)>700: lines.append(line); line=w
    else: line=test
   if line: lines.append(line)
   y=180
   for line in lines[:6]: draw.text((50,y),line,fill='black',font=font); y+=30
   f=tempfile.NamedTemporaryFile(suffix='.webp',delete=False).name; img.save(f,'WEBP')
   try: await m.reply_sticker(f)
   finally: os.unlink(f)
   return
  try:
   if src.photo:
    path=await src.download()
    from PIL import Image
    img=Image.open(path).convert('RGBA'); img.thumbnail((512,512))
    f=tempfile.NamedTemporaryFile(suffix='.webp',delete=False).name; img.save(f,'WEBP')
    try: await m.reply_sticker(f)
    finally: os.unlink(f); os.unlink(path)
    return
   if src.animation or src.video:
    path=await src.download(); out=tempfile.NamedTemporaryFile(suffix='.webm',delete=False).name
    cmd=['ffmpeg','-y','-i',path,'-t','3','-vf','scale=512:512:force_original_aspect_ratio=decrease,fps=30','-an','-c:v','libvpx-vp9','-b:v','0','-crf','45',out]
    subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
    try: await m.reply_sticker(out)
    finally: os.unlink(path); os.unlink(out)
    return
  except Exception: pass
  await m.reply('❌ This media cannot be converted to a sticker.')
 @app.on_message(filters.command('own'))
 async def own(_,m):
  src=m.reply_to_message
  if not src:
   return await m.reply('🎨 Reply to a photo or sticker and use /own.')
  await m.reply(
   '🎨 To create your personal Viora sticker pack, send the sticker/photo to @Stickers and use the pack creation flow there. '
   'Telegram does not expose sticker-pack creation as a normal high-level Pyrogram type in this runtime.'
  )
