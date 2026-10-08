import aiohttp
from .common import mention
class API:
    def __init__(self,token): self.base=f'https://api.telegram.org/bot{token}'
    async def call(self,method,**data):
        async with aiohttp.ClientSession() as s:
            async with s.post(f'{self.base}/{method}',json=data) as r:
                out=await r.json()
                if not out.get('ok'): raise RuntimeError(out.get('description','Telegram API error'))
                return out['result']
    def btn(self,text,callback_data=None,url=None,style='primary'):
        d={'text':text}
        if callback_data is not None: d['callback_data']=callback_data
        if url is not None: d['url']=url
        if style in {'primary','success','danger'}: d['style']=style
        return d
    def kb(self,*rows): return {'inline_keyboard':[list(r) for r in rows]}
    async def send(self,chat_id,text,keyboard=None,reply_to=None):
        d={'chat_id':chat_id,'text':text,'parse_mode':'HTML','disable_web_page_preview':True}
        if keyboard: d['reply_markup']=keyboard
        if reply_to: d['reply_to_message_id']=reply_to
        return await self.call('sendMessage',**d)
    async def edit(self,chat_id,message_id,text,keyboard=None):
        d={'chat_id':chat_id,'message_id':message_id,'text':text,'parse_mode':'HTML'}
        if keyboard is not None: d['reply_markup']=keyboard
        return await self.call('editMessageText',**d)
    async def answer(self,cid,text='',alert=False): return await self.call('answerCallbackQuery',callback_query_id=cid,text=text,show_alert=alert)
    async def invoice(self,chat_id,title,description,payload,currency,prices,provider_token=''):
        return await self.call('sendInvoice',chat_id=chat_id,title=title,description=description,payload=payload,currency=currency,prices=prices,provider_token=provider_token)
    async def delete(self,chat_id,message_id): return await self.call('deleteMessage',chat_id=chat_id,message_id=message_id)
