#!/usr/bin/env python3
"""
Discord bot for Fulmine-Sparks image generation service.
Demonstrates real-world bot integration with base64 images.
"""

import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project to path
import sys
sys.path.insert(0, os.path.dirname(__file__))

from fulmine_spark.services.image_generation import image_generation_service
from fulmine_spark.services.moderation import moderation_service
from fulmine_spark.config import settings

# Create bot with command prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """Called when bot is ready."""
    print(f"✅ Bot logged in as {bot.user}")
    print(f"✅ Bot is ready to generate images!")
    print(f"✅ Use: !generate <prompt>")

@bot.command(name='generate', help='Generate an AI image from a prompt')
async def generate_image(ctx, *, prompt: str):
    """
    Generate an image from a text prompt.
    
    Usage: !generate sunset over mountains
    """
    
    # Show that we're processing
    async with ctx.typing():
        try:
            # Check prompt safety
            print(f"\n📝 Checking prompt: {prompt}")
            is_safe, score, reason = await moderation_service.check_content(prompt)
            
            if not is_safe:
                embed = discord.Embed(
                    title="❌ Prompt Rejected",
                    description=f"Your prompt was rejected for safety reasons.\n\n**Reason:** {reason}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            print(f"✅ Prompt is safe (score: {score:.2f})")
            
            # Generate image
            print(f"🎨 Generating image...")
            image_urls, image_base64 = await image_generation_service.generate_image(
                prompt=prompt,
                model="stable-diffusion",
                num_outputs=1,
                guidance_scale=7.5,
                num_inference_steps=50,
                return_base64=True,
            )
            
            if not image_base64 or not image_base64[0]:
                embed = discord.Embed(
                    title="❌ Generation Failed",
                    description="Failed to generate image. Please try again.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Create embed with image
            embed = discord.Embed(
                title="🎨 Generated Image",
                description=f"**Prompt:** {prompt}",
                color=discord.Color.purple()
            )
            
            # Set image from base64
            embed.set_image(url=image_base64[0])
            
            # Add footer with model info
            embed.set_footer(text="Generated with Stable Diffusion v1.5 via Fulmine-Sparks ⚡")
            
            # Send embed
            await ctx.send(embed=embed)
            print(f"✅ Image sent to Discord!")
            
        except ValueError as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Image generation failed: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            print(f"❌ Error: {str(e)}")
        except Exception as e:
            embed = discord.Embed(
                title="❌ Unexpected Error",
                description=f"An unexpected error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            print(f"❌ Unexpected error: {str(e)}")

@bot.command(name='models', help='List available image generation models')
async def list_models(ctx):
    """List available models."""
    models_info = image_generation_service.get_available_models()
    
    embed = discord.Embed(
        title="🎨 Available Models",
        description="Choose a model for image generation",
        color=discord.Color.blue()
    )
    
    for model_name, model_info in models_info.items():
        embed.add_field(
            name=f"**{model_name}**",
            value=f"{model_info['description']}\nCost: {model_info['cost']} BTC",
            inline=False
        )
    
    embed.set_footer(text="Use !generate <prompt> to generate an image")
    await ctx.send(embed=embed)

@bot.command(name='help', help='Show help information')
async def show_help(ctx):
    """Show help information."""
    embed = discord.Embed(
        title="🎨 Fulmine-Sparks Discord Bot",
        description="AI-powered image generation with Lightning payments",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="Commands",
        value="""
        `!generate <prompt>` - Generate an image from a text prompt
        `!models` - List available image generation models
        `!help` - Show this help message
        """,
        inline=False
    )
    
    embed.add_field(
        name="Example",
        value="`!generate a beautiful sunset over mountains`",
        inline=False
    )
    
    embed.add_field(
        name="Features",
        value="""
        ✅ AI image generation via Stable Diffusion
        ✅ Content moderation
        ✅ Lightning payments (coming soon)
        ✅ Base64 image encoding
        """,
        inline=False
    )
    
    embed.set_footer(text="Powered by Fulmine-Sparks ⚡")
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Missing Argument",
            description=f"Please provide a prompt.\n\nUsage: `!generate <prompt>`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="❌ Command Not Found",
            description="Use `!help` to see available commands.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred: {str(error)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

def main():
    """Run the bot."""
    # Get bot token from environment
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        print("❌ DISCORD_BOT_TOKEN not set in .env file")
        print("\nTo set up the bot:")
        print("1. Go to https://discord.com/developers/applications")
        print("2. Create a new application")
        print("3. Go to 'Bot' section and create a bot")
        print("4. Copy the token and add to .env:")
        print("   DISCORD_BOT_TOKEN=your_token_here")
        print("\n5. Go to OAuth2 > URL Generator")
        print("6. Select scopes: bot")
        print("7. Select permissions: Send Messages, Embed Links, Attach Files")
        print("8. Copy the generated URL and open in browser to invite bot to server")
        return
    
    print("=" * 60)
    print("🎨 Fulmine-Sparks Discord Bot")
    print("=" * 60)
    print("\n✅ Starting bot...")
    print("✅ Commands:")
    print("   !generate <prompt> - Generate an image")
    print("   !models - List available models")
    print("   !help - Show help")
    print("\n")
    
    # Run the bot
    bot.run(token)

if __name__ == "__main__":
    main()
