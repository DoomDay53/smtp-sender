FTS Email Bot
A Telegram bot for mass reporting of prohibited content via SMTP using multiple Gmail accounts.

Description
FTS Email Bot is a tool for automated email reporting through Gmail’s SMTP server. The bot is integrated with Telegram, uses SQLite for managing subscriptions and statistics, and provides a user-friendly interface with buttons and complaint templates.

Key Features:

Mass sending of complaints using a pool of SMTP accounts
User subscription management
Statistics on successful and failed sends
Support for complaint templates
Logging of all operations
Multithreading with locks for database operations
Requirements
Python 3.8+
Libraries:

telebot
sqlite3 (built into Python)
smtplib (built into Python)
Install dependencies:

pip install pyTelegramBotAPI
Installation
Clone the repository:
it clone https://github.com/username/fts-email-bot.git
cd fts-email-bot
Configure the settings in the code:

Specify BOT_TOKEN (your Telegram bot token from @BotFather)
Add ADMINS (list of admin IDs)
Specify TARGET_EMAIL (email address for receiving complaints)
Configure SMTP_ACCOUNTS (dictionary with Gmail emails and app passwords)
Run the bot:

python main.py
Usage
Commands
/start - Start the bot and display the main menu
/givesub USER_ID - Grant a subscription to a user (admins only)
/revokesub USER_ID - Revoke a user’s subscription (admins only)
/stats - Show sending statistics (admins only)
Functionality
Sending a Complaint:

Click "🚨 Send Complaint"
Enter the complaint text or select a template
The bot will send the complaint through all available SMTP accounts
Complaint Templates:

Click "📋 Complaint Templates" to select pre-made text
Statistics:

Admins can view overall statistics and the top 10 SMTP accounts
Project Structure
bot.py - Main file with the bot’s code
subscriptions.db - SQLite database (created automatically)
smtp_bot.log - Log file
Database
subscriptions table: Stores user subscriptions
email_stats table: Statistics for SMTP accounts
SMTP Configuration
To work with Gmail, you need to:

Enable two-factor authentication
Generate an app password in Google Account settings
Add the email and app password to SMTP_ACCOUNTS
Logging
All operations are logged in smtp_bot.log with timestamps, log levels, and messages.

Security
Use only verified SMTP accounts
Store the bot token and passwords securely
Do not publish sensitive data publicly

Contact
For questions or suggestions, write to t.me/IntelBreak on Telegram.
