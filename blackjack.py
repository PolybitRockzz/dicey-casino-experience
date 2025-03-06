import discord
from discord import app_commands
from discord.ui import Button, View
import random

# Card emojis for visualization
CARD_EMOJIS = {
    'hearts': {
        'A': '🂱', '2': '🂲', '3': '🂳', '4': '🂴', '5': '🂵', '6': '🂶', '7': '🂷', '8': '🂸', '9': '🂹', '10': '🂺', 'J': '🂻', 'Q': '🂽', 'K': '🂾'
    },
    'diamonds': {
        'A': '🃁', '2': '🃂', '3': '🃃', '4': '🃄', '5': '🃅', '6': '🃆', '7': '🃇', '8': '🃈', '9': '🃉', '10': '🃊', 'J': '🃋', 'Q': '🃍', 'K': '🃎'
    },
    'clubs': {
        'A': '🃑', '2': '🃒', '3': '🃓', '4': '🃔', '5': '🃕', '6': '🃖', '7': '🃗', '8': '🃘', '9': '🃙', '10': '🃚', 'J': '🃛', 'Q': '🃝', 'K': '🃞'
    },
    'spades': {
        'A': '🂡', '2': '🂢', '3': '🂣', '4': '🂤', '5': '🂥', '6': '🂦', '7': '🂧', '8': '🂨', '9': '🂩', '10': '🂪', 'J': '🂫', 'Q': '🂭', 'K': '🂮'
    }
}

CARD_VALUES = {
    'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10
}

SUITS = {
    'hearts': '♥️',
    'diamonds': '♦️',
    'clubs': '♣️',
    'spades': '♠️'
}

class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value
        self.numeric_value = CARD_VALUES[value]
    
    def __str__(self):
        return CARD_EMOJIS[self.suit][self.value]

class Deck:
    def __init__(self):
        self.cards = []
        self.build()
    
    def build(self):
        for suit in SUITS.keys():
            for value in CARD_VALUES.keys():
                self.cards.append(Card(suit, value))
    
    def shuffle(self):
        random.shuffle(self.cards)
    
    def deal(self):
        if len(self.cards) > 0:
            return self.cards.pop()
        return None

class BlackjackGame:
    def __init__(self, player, bet):
        self.player = player
        self.bet = bet
        self.deck = Deck()
        self.deck.shuffle()
        self.player_hand = []
        self.dealer_hand = []
        self.game_over = False
        self.result = None
        
        # Deal initial cards
        self.player_hand.append(self.deck.deal())
        self.dealer_hand.append(self.deck.deal())
        self.player_hand.append(self.deck.deal())
        self.dealer_hand.append(self.deck.deal())
    
    def get_hand_value(self, hand):
        value = sum(card.numeric_value for card in hand)
        # Handle aces if bust
        aces = sum(1 for card in hand if card.value == 'A')
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        return value
    
    def player_hit(self):
        self.player_hand.append(self.deck.deal())
        if self.get_hand_value(self.player_hand) > 21:
            self.stand()
    
    def stand(self):
        # Dealer draws until 17 or higher
        while self.get_hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.deal())
        
        player_value = self.get_hand_value(self.player_hand)
        dealer_value = self.get_hand_value(self.dealer_hand)
        
        # Determine winner
        if player_value > 21:
            self.result = "bust"
        elif dealer_value > 21:
            self.result = "dealer_bust"
        elif player_value > dealer_value:
            self.result = "win"
        elif dealer_value > player_value:
            self.result = "lose"
        else:
            self.result = "push"
        
        self.game_over = True
    
    def format_hand(self, hand, hide_first=False):
        if hide_first and len(hand) > 0:
            return f"🂠 {' '.join(str(card) for card in hand[1:])}"
        return " ".join(str(card) for card in hand)
    
    def get_game_embed(self, hide_dealer=True):
        player_value = self.get_hand_value(self.player_hand)
        
        if hide_dealer:
            dealer_cards = self.format_hand(self.dealer_hand, hide_first=True)
            dealer_value = "?"
        else:
            dealer_cards = self.format_hand(self.dealer_hand)
            dealer_value = self.get_hand_value(self.dealer_hand)
        
        embed = discord.Embed(
            title="<:blackjack:1347126019592556555> Blackjack",
            description=f"Bet: **{self.bet:,}** credits",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name=f"Dealer's Hand ({dealer_value})",
            value=dealer_cards,
            inline=False
        )
        
        embed.add_field(
            name=f"Your Hand ({player_value})",
            value=self.format_hand(self.player_hand),
            inline=False
        )
        
        if self.game_over:
            if self.result == "win" or self.result == "dealer_bust":
                embed.add_field(
                    name="Result",
                    value=f"You won **{self.bet:,}** credits!",
                    inline=False
                )
            elif self.result == "lose" or self.result == "bust":
                embed.add_field(
                    name="Result",
                    value=f"You lost **{self.bet:,}** credits.",
                    inline=False
                )
            elif self.result == "push":
                embed.add_field(
                    name="Result",
                    value="Push! Your bet has been returned.",
                    inline=False
                )
        
        return embed

class BlackjackView(View):
    def __init__(self, game, interaction, client):
        super().__init__(timeout=180)  # 3 minute timeout
        self.game = game
        self.interaction = interaction
        self.client = client
        self.message = None
    
    async def on_timeout(self):
        if not self.game.game_over:
            self.game.stand()
            await self.update_message()
            await self.send_result()
            self.stop()
    
    async def update_message(self):
        if self.message:
            embed = self.game.get_game_embed(hide_dealer=not self.game.game_over)
            await self.message.edit(embed=embed, view=self if not self.game.game_over else None)
    
    async def send_result(self):
        # Get user's current balance
        response = self.client.supabase.table('members').select('credits,wins,losses').eq('username', str(self.interaction.user.name)).execute()
        
        if not response.data:
            return
        
        user_data = response.data[0]
        current_credits = user_data['credits']
        wins = user_data.get('wins', 0)
        losses = user_data.get('losses', 0)
        
        # Calculate new balance and stats
        new_credits = current_credits
        new_wins = wins
        new_losses = losses
        
        if self.game.result in ["win", "dealer_bust"]:
            new_credits += self.game.bet
            new_wins += 1
            result_text = "You won!"
            color = discord.Color.green()
        elif self.game.result in ["lose", "bust"]:
            new_credits -= self.game.bet
            new_losses += 1
            result_text = "You lost."
            color = discord.Color.red()
        else:  # push
            result_text = "It's a push!"
            color = discord.Color.blue()
        
        # Update database
        self.client.supabase.table('members').update({
            'credits': new_credits,
            'wins': new_wins,
            'losses': new_losses
        }).eq('username', str(self.interaction.user.name)).execute()
        
        # Create result embed
        result_embed = discord.Embed(
            title="<:blackjack:1347126019592556555> Blackjack Results",
            description=result_text,
            color=color
        )
        
        result_embed.add_field(
            name="Game Summary",
            value=f"Dealer's Hand: **{self.game.get_hand_value(self.game.dealer_hand)}**\nYour Hand: **{self.game.get_hand_value(self.game.player_hand)}**",
            inline=False
        )
        
        result_embed.add_field(
            name="Credits",
            value=f"Bet: **{self.game.bet:,}**\nNew Balance: **{new_credits:,}**",
            inline=False
        )
        
        result_embed.set_author(name=self.interaction.user.display_name, icon_url=self.interaction.user.display_avatar.url)
        result_embed.set_footer(text="Thanks for playing! 🃏")
        
        await self.interaction.followup.send(embed=result_embed)
    
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        self.game.player_hit()
        await self.update_message()
        
        if self.game.game_over:
            self.stop()
            await self.send_result()
    
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        self.game.stand()
        await self.update_message()
        self.stop()
        await self.send_result()

async def setup_blackjack_command(client):
    @client.tree.command(
        name="blackjack",
        description="Play a game of blackjack"
    )
    @app_commands.describe(
        bet="Amount of credits to bet (minimum 10)"
    )
    async def blackjack(interaction: discord.Interaction, bet: int):
        try:
            # Defer the response immediately to prevent timeout
            await interaction.response.defer(ephemeral=False)
            
            # Validate bet amount
            if bet <= 0:
                embed = discord.Embed(
                    title="Invalid Bet",
                    description="Please bet a positive amount of credits!",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Check minimum bet requirement
            if bet < 10:
                embed = discord.Embed(
                    title="Minimum Bet Required",
                    description="You must bet at least 10 credits to play blackjack!",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Get user's current balance
            response = client.supabase.table('members').select('credits').eq('username', str(interaction.user.name)).execute()
            
            if not response.data:
                embed = discord.Embed(
                    title="Account Required",
                    description="Please check your balance first to create an account!",
                    color=discord.Color.yellow()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            current_credits = response.data[0]['credits']
            
            if current_credits < bet:
                embed = discord.Embed(
                    title="Insufficient Credits",
                    description=f"You don't have enough credits! Your balance: **{current_credits:,}** credits",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Create a new blackjack game
            game = BlackjackGame(interaction.user, bet)
            view = BlackjackView(game, interaction, client)
            
            # Check for natural blackjack
            if game.get_hand_value(game.player_hand) == 21:
                if game.get_hand_value(game.dealer_hand) == 21:
                    game.result = "push"
                else:
                    game.result = "win"
                    # Blackjack pays 3:2
                    game.bet = int(game.bet * 1.5)
                game.game_over = True
            
            # Send initial game state
            embed = game.get_game_embed(hide_dealer=not game.game_over)
            message = await interaction.followup.send(embed=embed, view=view if not game.game_over else None)
            view.message = message
            
            # If game is already over (natural blackjack), send result
            if game.game_over:
                await view.send_result()
                view.stop()
                
        except Exception as e:
            print(f"Error in blackjack command: {e}")
            error_embed = discord.Embed(
                title="Error",
                description="An error occurred while processing your game. Please try again later.",
                color=discord.Color.dark_red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)