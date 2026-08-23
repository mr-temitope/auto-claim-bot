   @echo off
   title Auto-Claim Bot
   echo Starting Auto-Claim Bot...
   
   REM Change directory to your project folder
   cd /d "C:\Users\HomePC\Documents\auto-claim-bot"
   
   REM Run the bot using your specific Python installation
   "C:\Users\HomePC\AppData\Local\Programs\Python\Python312\python.exe" -m bot.main
   
   echo Bot stopped.
   pause