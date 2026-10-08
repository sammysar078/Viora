import os
from dotenv import load_dotenv
load_dotenv()

def _ids(v): return {int(x.strip()) for x in v.split(',') if x.strip().lstrip('-').isdigit()}
API_ID=int(os.getenv('API_ID','0')); API_HASH=os.getenv('API_HASH',''); BOT_TOKEN=os.getenv('BOT_TOKEN','')
MONGO_URI=os.getenv('MONGO_URI') or os.getenv('MONGO_DB_URI') or 'mongodb://127.0.0.1:27017'; MONGO_DB=os.getenv('MONGO_DB','Viora')
BOT_USERNAME=os.getenv('BOT_USERNAME','VioraBot').lstrip('@'); OWNER_IDS=_ids(os.getenv('OWNER_IDS','')); WHISPER_ALIASES={x.strip().lstrip('@').lower() for x in os.getenv('WHISPER_ALIASES','').split(',') if x.strip()}
LIBRETRANSLATE_URL=os.getenv('LIBRETRANSLATE_URL','').rstrip('/'); LIBRETRANSLATE_API_KEY=os.getenv('LIBRETRANSLATE_API_KEY','')
PAYMENT_PROVIDER_TOKEN=os.getenv('PAYMENT_PROVIDER_TOKEN','')
PREMIUM_STARS=int(os.getenv('PREMIUM_STARS','100')); PREMIUM_DAYS=int(os.getenv('PREMIUM_DAYS','30'))
GEM_PRICE_INR=int(os.getenv('GEM_PRICE_INR','8')); GEM_PRICE_STARS=int(os.getenv('GEM_PRICE_STARS','1'))
PREMIUM_GEM_DAILY_USE=50; NORMAL_DAILY_COINS=2000; PREMIUM_DAILY_COINS=5000; NORMAL_DAILY_XP=50; PREMIUM_DAILY_XP=200
NORMAL_ROB_MAX=10000; PREMIUM_ROB_MAX=30000; NORMAL_ROB_XP_MAX=50; PREMIUM_ROB_XP_MAX=100
NORMAL_KILL=(100,200,0,10); PREMIUM_KILL=(200,400,10,20)
NORMAL_DAILY_KILLS=200; PREMIUM_DAILY_KILLS=400; NORMAL_DAILY_ROBS=150; PREMIUM_DAILY_ROBS=300
NORMAL_TAX=0.10; PREMIUM_TAX=0.05; NORMAL_PROTECT_DAYS=1; PREMIUM_PROTECT_DAYS=2
PROTECT_COST_PER_DAY=int(os.getenv('PROTECT_COST_PER_DAY','500')); CLAIM_REWARD=int(os.getenv('CLAIM_REWARD','1000'))
JOIN_SECONDS=int(os.getenv('JOIN_SECONDS','120')); CARD_TURN_SECONDS=int(os.getenv('CARD_TURN_SECONDS','60')); MAX_GAME_PLAYERS=int(os.getenv('MAX_GAME_PLAYERS','20'))
POWER_COSTS={'rampage':int(os.getenv('RAMPAGE_GEMS','5')),'cloak':int(os.getenv('CLOAK_GEMS','5')),'vault':int(os.getenv('VAULT_GEMS','5'))}
POWER_EFFECTS={'rampage':'Kill/rob limits are doubled while active.','cloak':'Your protection is hidden from non-premium users and rob attempts against you fail.','vault':'Robbers cannot take wallet funds; wallet protection is always enforced.'}
