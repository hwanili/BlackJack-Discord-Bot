import discord
import random
import datetime
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

admin_id = 
TOKEN = ""

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.slash_command(name='nuke', description='채널을 재생성합니다.')
async def nuke(ctx):
    if ctx.guild.get_role(admin_id) in ctx.author.roles:
        aposition = ctx.channel.position
        new = await ctx.channel.clone()
        await ctx.channel.delete()
        await new.edit(position=aposition)
        embed = discord.Embed(title='Nuked', description='Channel Nuked.', color=discord.Color.red())
        await new.send(embed=embed)
    else:
        embed = discord.Embed(title="권한 없음", description="관리자만 사용 가능합니다.", color=discord.Color.red())
        await ctx.respond(embed=embed)

@bot.slash_command(name='인증', description='아래 버튼을 눌러 역할을 지급합니다.')
async def btrole(ctx):
    embed = discord.Embed(title="인증하기", description="아래 버튼을 누르면 역할이 지급됩니다", color=discord.Color.green())
    await ctx.respond(embed=embed, view=RoleButton(ctx))

class RoleButton(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(label="인증하기", style=discord.ButtonStyle.green, custom_id="verification_button")
    async def charge(self, button: discord.ui.Button, interaction: discord.Interaction):
        member = interaction.guild.get_member(interaction.user.id)
        roles = discord.utils.get(interaction.guild.roles, name="인증✅")
        await member.add_roles(roles)
        await interaction.response.send_message("인증이 완료되었습니다.", ephemeral=True)

user_balances = {}
user_last_reward_date = {}

ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
cards = [{'rank': rank} for rank in ranks]

class BlackjackGame:
    def __init__(self):
        self.player_hand = []
        self.dealer_hand = []

    def deal_cards(self):
        random.shuffle(cards)
        self.player_hand = [cards.pop(), cards.pop()]
        self.dealer_hand = [cards.pop(), cards.pop()]

    def hit(self):
        self.player_hand.append(cards.pop())

    def reveal_dealer_card(self):
        return self.dealer_hand[0]

@bot.slash_command(name='블랙잭', description='블랙잭 게임을 시작합니다.')
async def start_blackjack(ctx, bet_amount: int):
    if bet_amount <= 0:
        await ctx.channel.trigger_typing()  
        embed = discord.Embed(title="오류", description="베팅 금액은 0보다 커야 합니다.", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    if ctx.author.id not in user_balances:
        user_balances[ctx.author.id] = 0

    if user_balances[ctx.author.id] < bet_amount:
        await ctx.channel.trigger_typing()  
        embed = discord.Embed(title="오류", description="잔액이 부족합니다.", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    game = BlackjackGame()
    game.deal_cards()
    
    dealer_card = game.reveal_dealer_card()
    embed = discord.Embed(title="블랙잭", description=f'딜러의 첫 번째 카드: {dealer_card["rank"]}', color=discord.Color.green())
    await ctx.respond(embed=embed)

    player_cards_str = ', '.join([card["rank"] for card in game.player_hand])
    player_total = sum([10 if card["rank"] in ['J', 'Q', 'K'] else 11 if card["rank"] == 'A' else int(card["rank"]) for card in game.player_hand])
    embed = discord.Embed(title="블랙잭", description=f'플레이어의 카드: {player_cards_str}\n합계: {player_total}\n히트 하려면 `h`, 스테이 하려면 `s`를 입력해주세요.', color=discord.Color.green())
    await ctx.send(embed=embed)

    while True:
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in ['h', 's']

        try:
            choice_msg = await bot.wait_for('message', check=check, timeout=60)
            choice = choice_msg.content.lower()

            if choice == 'h':
                game.hit()
                player_cards_str = ', '.join([card["rank"] for card in game.player_hand])
                player_total = sum([10 if card["rank"] in ['J', 'Q', 'K'] else 11 if card["rank"] == 'A' else int(card["rank"]) for card in game.player_hand])
                embed = discord.Embed(title="블랙잭", description=f'히트를 선택하셨습니다.\n플레이어의 카드: {player_cards_str}\n합계: {player_total}', color=discord.Color.green())
                await ctx.send(embed=embed)

                if player_total > 21:
                    embed = discord.Embed(title="블랙잭", description='플레이어가 버스트되었습니다.', color=discord.Color.red())
                    await ctx.send(embed=embed)
                    user_balances[ctx.author.id] -= bet_amount
                    return
            else:
                break
        except TimeoutError:
            embed = discord.Embed(title="블랙잭", description='시간이 초과되었습니다.', color=discord.Color.red())
            await ctx.send(embed=embed)
            user_balances[ctx.author.id] -= bet_amount
            return

    dealer_cards_str = ', '.join([card["rank"] for card in game.dealer_hand])
    dealer_total = sum([10 if card["rank"] in ['J', 'Q', 'K'] else 11 if card["rank"] == 'A' else int(card["rank"]) for card in game.dealer_hand])
    await ctx.respond(f'딜러의 카드: {dealer_cards_str}\n합계: {dealer_total}')

    while dealer_total < 17:
        game.hit()
        dealer_total = sum([10 if card["rank"] in ['J', 'Q', 'K'] else 11 if card["rank"] == 'A' else int(card["rank"]) for card in game.dealer_hand])

    if dealer_total > 21:
        embed = discord.Embed(title="블랙잭", description='딜러가 버스트되었습니다.', color=discord.Color.green())
        await ctx.send(embed=embed)
        user_balances[ctx.author.id] += bet_amount * 2
    elif dealer_total > player_total:
        embed = discord.Embed(title="블랙잭", description='딜러가 이겼습니다.', color=discord.Color.red())
        await ctx.send(embed=embed)
        user_balances[ctx.author.id] -= bet_amount
    elif dealer_total < player_total:
        embed = discord.Embed(title="블랙잭", description='플레이어가 이겼습니다.', color=discord.Color.green())
        await ctx.send(embed=embed)
        user_balances[ctx.author.id] += bet_amount * 2
    else:
        embed = discord.Embed(title="블랙잭", description='무승부입니다.', color=discord.Color.yellow())
        await ctx.send(embed=embed)


@bot.slash_command(name='잔액')
async def balance(ctx):
    if ctx.author.id not in user_balances:
        await ctx.channel.trigger_typing()  
        embed = discord.Embed(title="잔액",description="잔액: 0", color=discord.Color.green())
        await ctx.respond(embed=embed)
    else:
        await ctx.channel.trigger_typing()  
        embed = discord.Embed(title="잔액",description=f"잔액: {user_balances[ctx.author.id]}", color=discord.Color.green())
        await ctx.respond(embed=embed)

@bot.slash_command(name='무료돈')
async def free_money(ctx):
    if ctx.author.id not in user_balances:
        user_balances[ctx.author.id] = 0

    if ctx.author.id in user_last_reward_date and user_last_reward_date[ctx.author.id] == datetime.date.today():
        await ctx.channel.trigger_typing()  
        embed = discord.Embed(title="오류",description="오늘 이미 무료 돈을 받았습니다.", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    user_balances[ctx.author.id] += 10000
    user_last_reward_date[ctx.author.id] = datetime.date.today()

    await ctx.channel.trigger_typing()  
    embed = discord.Embed(title="무료 돈 지급",description="하루에 한 번 10000원을 받았습니다!", color=discord.Color.green())
    await ctx.respond(embed=embed)

@bot.slash_command(name='출금')
async def withdraw(ctx, target_user: discord.Member, amount: int):
    if ctx.guild.get_role(admin_id) in ctx.author.roles:
        if amount <= 0:
            await ctx.channel.trigger_typing()  
            embed = discord.Embed(title="오류",description="출금 금액은 0보다 커야 합니다.", color=discord.Color.red())
            await ctx.respond(embed=embed)
            return

        if ctx.author.id not in user_balances or user_balances[ctx.author.id] < amount:
            await ctx.channel.trigger_typing()  
            embed = discord.Embed(title="오류",description="잔액이 부족합니다.", color=discord.Color.red())
            await ctx.respond(embed=embed)
            return

        user_balances[ctx.author.id] -= amount
        if target_user.id not in user_balances:
            user_balances[target_user.id] = 0
        user_balances[target_user.id] += amount

        await ctx.channel.trigger_typing()  
        embed = discord.Embed(title="출금 완료",description=f"{ctx.author.mention}님이 {target_user.mention}님에게 {amount} 만큼의 금액을 출금하였습니다.", color=discord.Color.green())
        await ctx.respond(embed=embed)
    else:
        embed = discord.Embed(title="권한 없음", description="관리자만 사용 가능합니다.", color=discord.Color.red())
        await ctx.respond(embed=embed)

@bot.slash_command(name='입금', description='관리자가 특정 유저에게 돈을 지급합니다.')
async def give_money(ctx, target_user: discord.Member, amount: int):
    if ctx.guild.get_role(admin_id) in ctx.author.roles:
        if amount <= 0:
            await ctx.channel.trigger_typing()  
            embed = discord.Embed(title="오류", description="지급 금액은 0보다 커야 합니다.", color=discord.Color.red())
            await ctx.respond(embed=embed)
            return

        if target_user.id not in user_balances:
            user_balances[target_user.id] = 0
        user_balances[target_user.id] += amount

        await ctx.channel.trigger_typing()  
        embed = discord.Embed(title="돈 지급 완료", description=f"{ctx.author.mention}님이 {target_user.mention}님에게 {amount} 만큼의 금액을 지급하였습니다.", color=discord.Color.green())
        await ctx.respond(embed=embed)
    else:
        embed = discord.Embed(title="권한 없음", description="관리자만 사용 가능합니다.", color=discord.Color.red())
        await ctx.respond(embed=embed)

bot.run(TOKEN)
