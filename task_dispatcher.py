import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()

class TaskDispatcherBot(discord.Client):
    async def on_ready(self):
        
        print(f'{self.user} has connected to Discord!')

        for guild in self.guilds:
            print(guild.name)
            if guild.name == GUILD:
                break

            print(
                f'{client.user} is connected to the following guild:\n'
                f'{guild.name}(id: {guild.id})'
            )

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith("!todo"):
            await message.channel.send("TaskDispatcher at your service !")

    async def on_reaction_add(self, reaction, user):
        print(f'{str(reaction)} on message {reaction.message.content}' )
        
        message = reaction.message
        channel = message.channel

        if(str(reaction) == "📝"):
            seen_message = f'Ok, {user.name}, I will add that to the general todolist'
            await channel.send(seen_message)

            def ask_attribute(m):
                return m.channel == channel and m.author == user

            await channel.send('Should I attribute the task to someone ?')
            try:
                msg = await self.wait_for('message', check=ask_attribute)
            except asyncio.TimeoutError:
                await channel.send('Ok, I let it go')
            else:
                if msg.content == "no":
                    await channel.send(f'Ok, but my guess is nobody will do it !')
                elif len(msg.mentions) == 0:
                    await channel.send(f'You did not mention anyone...')
                else:
                    tasked_names = ", ".join([m.name for m in msg.mentions])
                    await channel.send(f'Ok, it\'s been attributed to {tasked_names}')
            

bot = TaskDispatcherBot()
bot.run(TOKEN)