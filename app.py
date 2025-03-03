from typing import Final
import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from supabase import create_client, Client
from random import randint

# Load environment variables
load_dotenv()

# Discord setup
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
CLIENT_ID: Final[str] = os.getenv('CLIENT_ID')
SUPABASE_URL: Final[str] = os.getenv('SUPABASE_URL')
SUPABASE_KEY: Final[str] = os.getenv('SERVICE_ROLE_KEY')

# Initialize Discord client
class CasinoBot(discord.Client):
    def __init__(self):
        # Set up intents for the bot
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        # Initialize the client with proper intents and application ID
        super().__init__(intents=intents, application_id=CLIENT_ID)
        self.tree = app_commands.CommandTree(self)
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def setup_hook(self):
        await self.tree.sync()

client = CasinoBot()

@client.tree.command(name="balance", description="Checks your casino credit balance.")
async def balance(interaction: discord.Interaction):
    try:
        # Query the members table for the user
        response = client.supabase.table('members').select('credits,wins,losses').eq('username', str(interaction.user.name)).execute()
        
        # Create embed
        if response.data and len(response.data) > 0:
            # User exists, show their balance in a green embed
            user_data = response.data[0]
            credits = user_data['credits']
            wins = user_data.get('wins', 0)
            losses = user_data.get('losses', 0)
            total_games = wins + losses
            win_ratio = (wins / total_games * 100) if total_games > 0 else 0

            embed = discord.Embed(
                title="Casino Balance",
                description=f"💰 **{credits:,}** credits",
                color=discord.Color.green()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.add_field(
                name="Statistics",
                value=f"Total Games: **{total_games:,}**\nWins: **{wins:,}**\nLosses: **{losses:,}**\nWin Rate: **{win_ratio:.1f}%**",
                inline=False
            )
            embed.set_footer(text="Thanks for playing!")
            await interaction.response.send_message(embed=embed)
        else:
            # Create new user account with initial values
            new_user = {
                'username': str(interaction.user.name),
                'credits': 0,
                'bias': 1,
                'wins': 0,
                'losses': 0
            }
            client.supabase.table('members').insert(new_user).execute()
            
            # Show welcome embed for new user
            embed = discord.Embed(
                title="Welcome to the Casino!",
                description="Your account has been created! You start with 0 credits.\nUse casino commands or contact the administrator to earn more credits!",
                color=discord.Color.blue()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.add_field(
                name="Statistics",
                value="Total Games: **0**\nWins: **0**\nLosses: **0**\nWin Rate: **0.0%**",
                inline=False
            )
            embed.set_footer(text="Welcome aboard! 🎰")
            await interaction.response.send_message(embed=embed)
            
    except Exception as e:
        print(f"Error checking balance: {e}")
        embed = discord.Embed(
            title="Error",
            description="An error occurred while checking your balance. Please try again later.",
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(
    name="roulette",
    description="Place a bet on roulette (red/black/1-18/19-36/1-12/13-24/25-36)."
)
@app_commands.describe(
    amount="Amount of credits to bet",
    choice="Choose your bet type"
)
@app_commands.choices(choice=[
    app_commands.Choice(name='red', value='red'),
    app_commands.Choice(name='black', value='black'),
    app_commands.Choice(name='1-18', value='low'),
    app_commands.Choice(name='19-36', value='high'),
    app_commands.Choice(name='1-12', value='first'),
    app_commands.Choice(name='13-24', value='second'),
    app_commands.Choice(name='25-36', value='third')
])
async def roulette(interaction: discord.Interaction, amount: int, choice: str):
    try:
        # Defer the response immediately to prevent timeout
        await interaction.response.defer(ephemeral=False)

        # Validate bet amount
        if amount <= 0:
            await interaction.followup.send("Please bet a positive amount of credits!", ephemeral=True)
            return

        # Check minimum bet requirement
        if amount < 10:
            embed = discord.Embed(
                title="Minimum Bet Required",
                description="You must bet at least 10 credits to play roulette!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Get user's current balance
        response = client.supabase.table('members').select('credits').eq('username', str(interaction.user.name)).execute()

        if not response.data:
            await interaction.followup.send("Please check your balance first to create an account!", ephemeral=True)
            return

        current_credits = response.data[0]['credits']

        if current_credits < amount:
            await interaction.followup.send(f"You don't have enough credits! Your balance: {current_credits:,} credits", ephemeral=True)
            return

        # European Roulette numbers
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        low_numbers = list(range(1, 19))
        high_numbers = list(range(19, 37))
        first_dozen = list(range(1, 13))
        second_dozen = list(range(13, 25))
        third_dozen = list(range(25, 37))

        # Generate a random number (0-36) for fair odds
        result_number = randint(0, 36)

        # Determine if player won based on their choice
        won = False
        if choice in ['red', 'black']:
            won = (choice == 'red' and result_number in red_numbers) or \
                  (choice == 'black' and result_number in black_numbers)
            win_multiplier = 1  # 1:1 payout for red/black
        elif choice in ['low', 'high']:
            won = (choice == 'low' and result_number in low_numbers) or \
                  (choice == 'high' and result_number in high_numbers)
            win_multiplier = 1  # 1:1 payout for high/low
        else:  # Dozen bets
            won = (choice == 'first' and result_number in first_dozen) or \
                  (choice == 'second' and result_number in second_dozen) or \
                  (choice == 'third' and result_number in third_dozen)
            win_multiplier = 2  # 2:1 payout for dozen bets

        # Calculate new balance
        new_credits = current_credits + (amount * win_multiplier) if won else current_credits - amount

        # Update user's credits in database
        try:
            client.supabase.table('members').update({'credits': new_credits}).eq('username', str(interaction.user.name)).execute()
            
            # Create result embed
            number_color = 'green' if result_number == 0 else \
                          'red' if result_number in red_numbers else 'black'
            number_range = '0' if result_number == 0 else \
                          '1-18' if result_number in low_numbers else '19-36'
            embed = discord.Embed(
                title="<:roulettewheel:1344046246259855410> Roulette Results",
                description=f"The ball landed on **{result_number}** ({number_color}, {number_range})!",
                color=discord.Color.green() if won else discord.Color.red()
            )
            embed.add_field(
                name="Bet Details",
                value=f"Amount: **{amount:,}** credits\nBet: **{choice}**",
                inline=False
            )
            embed.add_field(
                name="Result",
                value=f"{'Won' if won else 'Lost'}: **{amount:,}** credits\nNew Balance: **{new_credits:,}** credits",
                inline=False
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="🎲 Good luck next time!")

            await interaction.followup.send(embed=embed)

        except Exception as db_error:
            print(f"Database error in roulette command: {db_error}")
            error_embed = discord.Embed(
                title="Error",
                description="An error occurred while updating your balance. Please check your balance to verify the transaction.",
                color=discord.Color.dark_red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    except Exception as e:
        print(f"Error in roulette command: {e}")
        error_embed = discord.Embed(
            title="Error",
            description="An error occurred while processing your bet. Please try again later.",
            color=discord.Color.dark_red()
        )
        await interaction.followup.send(embed=error_embed, ephemeral=True)

@client.tree.command(
    name="give",
    description="Give credits to a user (Admin only)"
)
@app_commands.describe(
    user="The user to give credits to",
    amount="Amount of credits to give"
)
async def give(interaction: discord.Interaction, user: discord.User, amount: int):
    try:
        # Check if the command user is the admin
        if str(interaction.user.name) != "swastikbiswas":
            embed = discord.Embed(
                title="Unauthorized",
                description="You do not have permission to use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Validate amount
        if amount <= 0:
            await interaction.response.send_message("Please specify a positive amount of credits!", ephemeral=True)
            return

        # Get target user's data
        response = client.supabase.table('members').select('credits').eq('username', str(user.name)).execute()

        if response.data and len(response.data) > 0:
            # User exists, update their credits
            current_credits = response.data[0]['credits']
            new_credits = current_credits + amount
            
            # Update credits in database
            client.supabase.table('members').update({'credits': new_credits}).eq('username', str(user.name)).execute()
            
            # Create success embed
            embed = discord.Embed(
                title="Credits Given",
                description=f"Successfully given credits to {user.mention}!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Details",
                value=f"Amount: **{amount:,}** credits\nNew Balance: **{new_credits:,}** credits",
                inline=False
            )
            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
            embed.set_footer(text="💰 Credits transferred successfully!")
            
            await interaction.response.send_message(embed=embed)
        else:
            # User doesn't exist, create account with given credits
            new_user = {
                'username': str(user.name),
                'credits': amount
            }
            client.supabase.table('members').insert(new_user).execute()
            
            # Create success embed for new user
            embed = discord.Embed(
                title="Account Created",
                description=f"Created new account for {user.mention} with initial credits!",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Details",
                value=f"Initial Credits: **{amount:,}**",
                inline=False
            )
            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
            embed.set_footer(text="🎰 Welcome to the Casino!")
            
            await interaction.response.send_message(embed=embed)
            
    except Exception as e:
        print(f"Error in give command: {e}")
        error_embed = discord.Embed(
            title="Error",
            description="An error occurred while processing the command. Please try again later.",
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)

@client.tree.command(
    name="withdraw",
    description="Withdraw credits from a user (Admin only)"
)
@app_commands.describe(
    user="The user to withdraw credits from",
    amount="Amount of credits to withdraw"
)
async def withdraw(interaction: discord.Interaction, user: discord.User, amount: int):
    try:
        # Check if the command user is the admin
        if str(interaction.user.name) != "swastikbiswas":
            embed = discord.Embed(
                title="Unauthorized",
                description="You do not have permission to use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Validate amount
        if amount <= 0:
            await interaction.response.send_message("Please specify a positive amount of credits to withdraw!", ephemeral=True)
            return

        # Get target user's data
        response = client.supabase.table('members').select('credits').eq('username', str(user.name)).execute()

        if response.data and len(response.data) > 0:
            # User exists, check if they have enough credits
            current_credits = response.data[0]['credits']
            if current_credits < amount:
                embed = discord.Embed(
                    title="Insufficient Credits",
                    description=f"{user.mention} only has **{current_credits:,}** credits.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Update credits in database
            new_credits = current_credits - amount
            client.supabase.table('members').update({'credits': new_credits}).eq('username', str(user.name)).execute()
            
            # Create success embed
            embed = discord.Embed(
                title="Credits Withdrawn",
                description=f"Successfully withdrawn credits from {user.mention}!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Details",
                value=f"Amount: **{amount:,}** credits\nNew Balance: **{new_credits:,}** credits",
                inline=False
            )
            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
            embed.set_footer(text="💰 Credits withdrawn successfully!")
            
            await interaction.response.send_message(embed=embed)
        else:
            # User doesn't exist
            embed = discord.Embed(
                title="User Not Found",
                description=f"Could not find an account for {user.mention}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
    except Exception as e:
        print(f"Error in withdraw command: {e}")
        error_embed = discord.Embed(
            title="Error",
            description="An error occurred while processing the command. Please try again later.",
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)

# Run the bot
client.run(TOKEN)