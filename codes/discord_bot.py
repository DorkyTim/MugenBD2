import os
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import asyncio
from discord.ext import commands
import discord
from dotenv import load_dotenv
load_dotenv()

class DiscordBotThread(QThread):
    log_signal = pyqtSignal(str)
    reroll_signal = pyqtSignal(str)

    def __init__(self, target_user_id = None):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # intents setting
        intents = discord.Intents.default()
        intents.message_content = True

        # Bot Init
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.target_token = os.getenv("DISCORD_BOT_TOKEN")
        assert self.target_token is not None, "DISCORD_BOT_TOKEN must be set in the .env file"
        self.target_channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
        assert self.target_channel_id is not None, "DISCORD_CHANNEL_ID must be set in the .env file"
        self.target_user_id = target_user_id

        self.channel = None

        # Bot event handler
        @self.bot.event
        async def on_ready():
            self.channel = self.bot.get_channel(self.target_channel_id)
            if self.channel:
                self.log_signal.emit(f"Connected to #{self.channel.name} of {self.channel.guild.name}")
            else:
                self.log_signal.emit(f"Channel {self.target_channel_id} not found")

        @self.bot.event
        async def on_error(event_method, *args, **kwargs):
            self.log_signal.emit(f"Error in {event_method}")

        @self.bot.command()
        async def stop(ctx):
            if target_user_id == ctx.author.id:
                await ctx.send("Stop Reroll")
                self.reroll_signal.emit("stop")

        @self.bot.command()
        async def reroll(ctx):
            if target_user_id == ctx.author.id:
                await ctx.send("Continue Reroll")
                self.reroll_signal.emit("reroll")

    def run(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.bot.start(self.target_token))
        except Exception as e:
            self.log_signal.emit(f"Failed to connect: {str(e)}")
            self.loop.stop()

    def stop(self):
        async def close_bot():
            await self.bot.close()
        asyncio.run_coroutine_threadsafe(close_bot(), self.loop)
        self.loop.call_soon_threadsafe(self.loop.stop)
        
    def set_ur_names(self, ur_names):
        self.last_ur_names = ur_names
        self.send_message()

    @pyqtSlot(list)
    def send_message_with_names(self, ur_names):
        async def send():
            try:
                image_path = './res/result.jpg'
                if not os.path.exists(image_path):
                    self.log_signal.emit(f"Image files {image_path} does not exist.")
                    return

                if self.channel:
                    with open(image_path, 'rb') as image_file:
                        ur_names_text = ", ".join(ur_names) if ur_names else "(None)"
                        await self.channel.send(
                            f"<@{self.target_user_id}> Costumes: {ur_names_text}\nDo you want to continue?\n(Response: !reroll / !stop)",
                            file=discord.File(image_file, 'result.jpg')
                        )
                    self.log_signal.emit("Sent a message to the channel.")
                else:
                    self.log_signal.emit(f"Channel with ID {self.channel} not found.")
            except Exception as e:
                print("send error")
                self.log_signal.emit(f"Failed to send message: {str(e)}")

        asyncio.ensure_future(send())
        print("done")

