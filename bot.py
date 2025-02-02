import validators
import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
)
import pandas as pd
import numpy as np
import datetime
import subprocess
import random
import re

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define conversation states
ASK_HANDLE, VERIFY_LINKS, ASK_VIRAL, VERIFY_VIRAL, MENU, TRACK_CHALLENGE, DAILY_UPDATE = range(7)
user_data = {}

# Start Command
async def start(update: Update, context: CallbackContext) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome! Please share **links** to your social media profiles (Instagram, TikTok, YouTube, etc.) or type 'skip'."
    )
    return ASK_HANDLE

# Handle social media links input
async def ask_handle(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    user_input = update.message.text.strip().lower()

    if user_input == "skip":
        # If user skips, show the content creation guide and motivational messages
        await show_content_guide_and_motivation(update, context)
        return MENU
    
    context.user_data['social_links'] = update.message.text

    # Fetch profile preview for verification
    profile_image, profile_title = fetch_content_preview(user_input)

    if profile_image:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=profile_image,
            caption=f"Here are the links you provided:\n\n{update.message.text}\n\nIs this correct? (Yes/No) or type 'skip'."
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Here are the links you provided:\n\n{update.message.text}\n\nIs this correct? (Yes/No) or type 'skip'."
        )
    return VERIFY_LINKS

# Handle verification of social media links
async def verify_links(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    response = update.message.text.strip().lower()

    if response == "yes":
        await context.bot.send_message(
            chat_id=chat_id,
            text="Great! Now, share a **link** to your most viral content, or type 'skip'."
        )
        return ASK_VIRAL
    elif response == "skip":
        await show_content_guide_and_motivation(update, context)
        return MENU
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="No problem! Please re-enter your social media links or type 'skip' to move ahead."
        )
        return ASK_HANDLE  # Restart link input process

# Handle viral content input
async def ask_viral(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    viral_link = update.message.text.strip()

    if viral_link == "skip":
        # If user skips, show the content creation guide and motivational messages
        await show_content_guide_and_motivation(update, context)
        return MENU

    if validators.url(viral_link):  # Validate URL format
        context.user_data['viral_link'] = viral_link

        # Fetch content preview
        preview_image, title = fetch_content_preview(viral_link)

        if preview_image:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=preview_image,
                caption=f"🔗 **Is this the correct content?**\n\n**Title:** {title}\n\n(Yes/No)"
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔗 **Is this the correct link?**\n{viral_link}\n\n(Yes/No)"
            )

        return VERIFY_VIRAL
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ That doesn't seem like a valid link. Please enter a **correct viral content link** or type 'skip'."
        )
        return ASK_VIRAL

# Verify the viral content link and show the menu
async def verify_viral(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    response = update.message.text.strip().lower()

    if response == "yes":
        await context.bot.send_message(chat_id=chat_id, text="🎉 **Awesome! Your details are saved. 🚀**")
        return await show_menu(update, context)
    elif response == "skip":
        await show_content_guide_and_motivation(update, context)
        return MENU
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="No worries! Please enter the **correct viral content link** or type 'skip' to skip this step."
        )
        return ASK_VIRAL  # Restart viral link input process

# Show content creation guide and motivational messages
async def show_content_guide_and_motivation(update: Update, context: CallbackContext) -> int:
    youtube_link = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Replace with your actual YouTube video URL
    
    # Send the content creation guide
    await update.message.reply_text(
        f"📚 **Content Creation Guide**\n\n"
        "1. **Define Your Niche:** Choose a niche that aligns with your passions.\n"
        "2. **Consistency is Key:** Post regularly to build engagement.\n"
        "3. **Engage with Your Audience:** Respond to comments and messages.\n"
        "4. **Quality over Quantity:** Focus on producing high-quality content.\n"
        "5. **Learn from Analytics:** Study which content works best and replicate it.\n\n"
        "For a deeper dive into content creation, check out our YouTube guide here:\n"
        f"🔗 [Watch the Content Creation Guide on YouTube]({youtube_link})\n\n"
        "Ready to start your 21-Day Challenge? 🏆"
    )
    
    # Send motivational message
    motivational_messages = [
        "🔥 Every great creator starts somewhere. Keep pushing forward!",
        "🚀 Consistency is key! Stay on track and success will follow.",
        "💡 Your content has value—share it with the world!",
        "🎯 Progress over perfection. Just keep creating!",
        "✨ The more you create, the better you become. Keep going!"
    ]
    motivation = random.choice(motivational_messages)
    await update.message.reply_text(f"🎯 **Motivation for you:** {motivation}")

    return MENU

async def show_menu(update: Update, context: CallbackContext) -> int:
    # Define the keyboard with 3 options
    keyboard = [
        ['📚 Content Creation Guide (/guide)'],  # First option
        ['🏆 Start 21-Day Challenge (/challenge)'], # Second option
        ['🤔 Maybe Later (/later)']              # Third option
    ]
    
    # Create the reply markup with the defined keyboard
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    # Send the menu options to the user
    await update.message.reply_text(
        "Choose an option below or use the corresponding command:\n\n"
        "📚 Content Creation Guide → Type `/guide`\n"
        "🏆 Start 21-Day Challenge → Type `/challenge`\n"
        "🤔 Maybe Later → Type `/later`",
        reply_markup=reply_markup
    )
    return MENU

async def content_guide(update: Update, context: CallbackContext) -> int:
    # Define the YouTube link to the content creation guide
    youtube_link = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Replace with your actual YouTube video URL
    
    # Respond with the content creation guide and the YouTube link
    await update.message.reply_text(
        f"📚 **Content Creation Guide**\n\n"
        "1. **Define Your Niche:** Choose a niche that aligns with your passions.\n"
        "2. **Consistency is Key:** Post regularly to build engagement.\n"
        "3. **Engage with Your Audience:** Respond to comments and messages.\n"
        "4. **Quality over Quantity:** Focus on producing high-quality content.\n"
        "5. **Learn from Analytics:** Study which content works best and replicate it.\n\n"
        "For a deeper dive into content creation, check out our YouTube guide here:\n"
        f"🔗 [Watch the Content Creation Guide on YouTube]({youtube_link})\n\n"
        "Ready to start your 21-Day Challenge? 🏆"
    )
    return MENU
    
    # Handle declined challenge
async def declined_challenge(update: Update, context: CallbackContext) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="No problem! You can start anytime. Meanwhile, explore our content guides."
    )
    return MENU

# Handle start 21-day challenge
async def start_challenge(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    user_data[chat_id] = {'challenge_days': 0, 'progress': []}
    await update.message.reply_text("🏆 You've started the **21-day challenge!** I'll remind you daily to post content.")
    return DAILY_UPDATE

# Send daily reminders
async def daily_reminder(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    user_data[chat_id]['challenge_days'] += 1
    day = user_data[chat_id]['challenge_days']
    if day > 21:
        return await check_progress(update, context)
    motivational_messages = [
        "🔥 Every great creator starts somewhere. Keep pushing forward!",
        "🚀 Consistency is key! Stay on track and success will follow.",
        "💡 Your content has value—share it with the world!",
        "🎯 Progress over perfection. Just keep creating!",
        "✨ The more you create, the better you become. Keep going!"
    ]
    motivation = random.choice(motivational_messages)
    await update.message.reply_text(f"📢 **Day {day}:** Post your content and share the link along with views count!\n\n{motivation}")
    return DAILY_UPDATE

# Track daily content updates
async def track_daily_progress(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    user_data[chat_id]['progress'].append(update.message.text)

    await context.bot.send_message(
        chat_id=chat_id,
        text="✅ **Recorded!** See you tomorrow for the next update."
    )
    return await daily_reminder(update, context)

# Check user progress after 21 days
async def check_progress(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="🎉 **Challenge completed!** Analyzing your growth... 📊"
    )
    # Call subprocess to analyze progress here (optional step)
    analysis_result = subprocess.run(['python', 'checked_progress.py', 'analyze'], capture_output=True, text=True)
    await context.bot.send_message(chat_id=chat_id, text=f"Your progress analysis:\n{analysis_result.stdout}")
    return MENU

# Cancel command
async def cancel(update: Update, context: CallbackContext) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👋 Goodbye!"
    )
    return ConversationHandler.END

# Fetch content preview (scrapes webpage for metadata)
def fetch_content_preview(url):
    """
    This function fetches preview information (image, title) for both content links
    and social media profile links. It returns the appropriate data.
    """

    def fetch_social_media_profile_preview(url):
        """Fetch preview data for social media profiles (like Instagram, TikTok, YouTube)."""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Instagram profile preview (checking for the profile image)
            if 'instagram.com' in url:
                profile_pic = soup.find("meta", property="og:image")
                username = soup.find("meta", property="og:title")
                return profile_pic["content"] if profile_pic else None, username["content"] if username else "Instagram User"
            
            # TikTok profile preview (checking for the profile image)
            elif 'tiktok.com' in url:
                profile_pic = soup.find("meta", property="og:image")
                username = soup.find("meta", property="og:title")
                return profile_pic["content"] if profile_pic else None, username["content"] if username else "TikTok User"
            
            # YouTube profile preview (fetch channel avatar)
            elif 'youtube.com' in url:
                profile_pic = soup.find("link", rel="icon")
                return profile_pic["href"] if profile_pic else None, "YouTube Channel"
            
            return None, "Unknown Profile"
        except Exception as e:
            print(f"Error fetching social media profile preview: {e}")
            return None, "Error fetching profile"
    
    try:
        # First, check if the URL is a valid content link (such as YouTube video, etc.)
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Check for profile-specific URLs (Instagram, TikTok, YouTube, etc.)
        if 'instagram.com' in url or 'tiktok.com' in url or 'youtube.com' in url:
            return fetch_social_media_profile_preview(url)
        
        # Otherwise, treat as a content link
        title = soup.title.string if soup.title else "No title found"
        
        # Extract Open Graph (OG) image if available for content
        og_image = soup.find("meta", property="og:image")
        image_url = og_image["content"] if og_image else None
        
        return image_url, title

    except Exception as e:
        print(f"Error fetching content preview: {e}")
        return None, "No preview available"

# Main function to set up the bot
def main():
    TOKEN = "YOUR_TOKEN"  # Replace with actual bot token
    app = Application.builder().token(TOKEN).build()

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_HANDLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_handle)],
            VERIFY_LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_links)],
            ASK_VIRAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_viral)],
            VERIFY_VIRAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_viral)],
            MENU: [
                MessageHandler(filters.Regex("^🏆 Start 21-Day Challenge"), start_challenge),
                MessageHandler(filters.Regex("^📚 Content Creation Guide"), content_guide),
                MessageHandler(filters.Regex("^🤔 Maybe Later"), declined_challenge),
                CommandHandler("guide", content_guide),
                CommandHandler("challenge", start_challenge),
                CommandHandler("later", declined_challenge),
            ],
            DAILY_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, track_daily_progress)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.run_polling()

if __name__ == "__main__":
    main()
