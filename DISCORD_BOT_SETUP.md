# 🤖 Discord Bot Setup Guide

This guide will help you set up the Fulmine-Sparks Discord bot to test image generation.

## Step 1: Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give it a name: `Fulmine-Sparks`
4. Click "Create"

## Step 2: Create Bot User

1. In your application, go to "Bot" section (left sidebar)
2. Click "Add Bot"
3. Under "TOKEN", click "Copy" to copy your bot token
4. **Keep this token secret!** Never share it publicly

## Step 3: Add Token to .env

Add this line to your `.env` file:

```
DISCORD_BOT_TOKEN=your_token_here
```

Replace `your_token_here` with the token you copied.

## Step 4: Set Bot Permissions

1. Go to "OAuth2" > "URL Generator" (left sidebar)
2. Under "SCOPES", select:
   - ✅ `bot`
3. Under "PERMISSIONS", select:
   - ✅ `Send Messages`
   - ✅ `Embed Links`
   - ✅ `Attach Files`
4. Copy the generated URL at the bottom

## Step 5: Invite Bot to Your Server

1. Open the URL you copied in your browser
2. Select your Discord server from the dropdown
3. Click "Authorize"
4. Complete the CAPTCHA
5. Bot will appear in your server! ✅

## Step 6: Run the Bot

```bash
cd /workspace/Fulmine-Spark
python discord_bot.py
```

You should see:
```
============================================================
🎨 Fulmine-Sparks Discord Bot
============================================================

✅ Starting bot...
✅ Commands:
   !generate <prompt> - Generate an image
   !models - List available models
   !help - Show help
```

## Step 7: Test the Bot

In your Discord server, try:

```
!help
```

You should see the help message. Then try:

```
!generate a beautiful sunset over mountains
```

The bot will:
1. Check the prompt for safety
2. Generate the image
3. Send it to Discord with the prompt

## 🎯 Available Commands

### Generate Image
```
!generate <prompt>
```

Examples:
```
!generate a cute cat playing with a ball
!generate a futuristic city skyline at night
!generate a serene forest with a waterfall
```

### List Models
```
!models
```

Shows available image generation models and their costs.

### Help
```
!help
```

Shows help information and available commands.

## 🔧 Troubleshooting

### Bot doesn't respond
- Make sure bot is running: `python discord_bot.py`
- Check that `DISCORD_BOT_TOKEN` is set in `.env`
- Make sure bot has permission to send messages in the channel

### "DISCORD_BOT_TOKEN not set"
- Add `DISCORD_BOT_TOKEN=your_token` to `.env`
- Restart the bot

### Image generation fails
- Check that `REPLICATE_API_TOKEN` is set in `.env`
- Make sure you have credit on Replicate account
- Check that prompt passes content moderation

### Bot crashes
- Check the error message in terminal
- Make sure all dependencies are installed: `pip install -r requirements.txt`

## 📊 What's Happening

When you use `!generate`:

1. **Bot receives command** - Discord sends command to bot
2. **Prompt checked** - Content moderation checks if prompt is safe
3. **Image generated** - Replicate API generates image
4. **Image encoded** - Image is downloaded and encoded to base64
5. **Embed created** - Discord embed is created with base64 image
6. **Image displayed** - Bot sends embed to Discord
7. **User sees image** - Image appears in Discord instantly ✨

## 🚀 Production Deployment

When ready for production:

1. **Deploy bot to server** - Use a service like Heroku, Railway, or self-hosted
2. **Set up Lightning payments** - Integrate BTCPay Server
3. **Add payment verification** - Check payment before generating image
4. **Monitor usage** - Track API costs and revenue
5. **Scale** - Add more models, features, etc.

## 💡 Next Steps

1. ✅ Set up Discord bot (this guide)
2. ✅ Test image generation
3. ⬜ Add Lightning payment integration
4. ⬜ Deploy to production
5. ⬜ Invite users to your server

## 📚 Resources

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [Replicate API Docs](https://replicate.com/docs)
- [Fulmine-Sparks GitHub](https://github.com/Fulmine-Labs/Fulmine-Sparks)

---

**🎉 Your Discord bot is ready to generate images!**
