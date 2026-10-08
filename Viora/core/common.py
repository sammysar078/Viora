import re, math
from datetime import datetime, timezone

def now(): return datetime.now(timezone.utc)
def today(): return now().date().isoformat()
def money(n): return f"${int(n):,}"
def gems(n_micro):
    n=int(n_micro); return f"{n//1000}.{(n%1000)//100:g} 💎" if n%1000 else f"{n//1000} 💎"
def amount(s):
    if isinstance(s,(int,float)): return int(s)
    s=str(s).strip().lower().replace(',','').replace('$','')
    m=re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)([km]?)',s)
    if not m: raise ValueError('Invalid amount')
    x=float(m.group(1))*({'':1,'k':1000,'m':1000000}[m.group(2)])
    if x<1 or x>10**12 or not math.isfinite(x): raise ValueError('Invalid amount')
    return int(x)
def parse_amount(s): return amount(s)
def fmt_money(n): return money(n)
def chunk(seq,n): return [seq[i:i+n] for i in range(0,len(seq),n)]
def target_from_reply(message):
    if not message.reply_to_message or not message.reply_to_message.from_user: return None
    return message.reply_to_message.from_user
def target(message): return target_from_reply(message)
def mention(user): return user.mention if getattr(user,'mention',None) else f"<a href='tg://user?id={user.id}'>{user.first_name or user.id}</a>"
def human(seconds):
    seconds=max(0,int(seconds)); d,r=divmod(seconds,86400); h,r=divmod(r,3600); m,s=divmod(r,60)
    return ' '.join(x for x in [f'{d}d' if d else '',f'{h}h' if h else '',f'{m}m' if m else '',f'{s}s' if s and not d and not h else ''] if x) or '0s'
