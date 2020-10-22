import os
import sys
from dotenv import load_dotenv

import discord
from discord.ext import commands

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DATABASE_URL = os.getenv('DATABASE_URL')

client = discord.Client()


engine = create_engine(DATABASE_URL)
Base = automap_base()
Base.prepare(engine, reflect=True)

User = Base.classes.user
Task = Base.classes.task

session = Session(engine)

def list_and(l):
    txt = ", ".join(l[:-1])
    if len(l) > 1:
        txt += f" and {l[-1]}"
    if len(l) == 1:
        txt += f"{l[0]}"
    return txt

def list_or(l):
    txt = ", ".join(l[:-1])
    if len(l) > 1:
        txt += f" or {l[-1]}"
    if len(l) == 1:
        txt += f"{l[0]}"
    return txt


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

        async def display_tasks(tasks):
            for task in tasks:
                task_message = f"> {task.content}\n"
                if len(task.user_collection) == 0:
                    task_message += "Not assigned (add ☝️ to take it)"
                else:
                    mentions = [u.mention for u in task.user_collection]
                    task_message += f"Assigned to {list_and(mentions)}"
                await message.channel.send(f"{task_message}")

        if message.content.startswith("!todo"):
            if (len(message.content[6:]) == 0
                or message.content[6:10] == "help"):
                await message.channel.send("TaskDispatcher at your service !")
                await message.channel.send("- Add a 📝 reaction to a message to start adding task")
                await message.channel.send("- `!todo all` to list all tasks")
                await message.channel.send("- `!todo @someone` to list tasks assigned to someone")
            elif message.content[6:9] == "all":
                tasks = session.query(Task).filter(
                                            Task.status == "TODO"
                                          ).all()
                await message.channel.send(f"{len(tasks)} are awaiting to be done")
                await display_tasks(tasks)
            elif len(message.mentions) > 0:
                tasks = session.query(Task).filter(
                                            Task.status == "TODO"
                                          ).filter(
                                            Task.user_collection.any(User.mention.in_(
                                                [m. mention for m in message.mentions]
                                                )
                                            )
                                          ).all()
                tasked_mentions = list_or([u.mention for u in message.mentions])
                await message.channel.send(f"{len(tasks)} are awaiting to be done by {tasked_mentions}")
                display_tasks(tasks)


    async def on_reaction_add(self, reaction, user):
        print(f'{str(reaction)} on message {reaction.message.content}')

        message = reaction.message
        channel = message.channel

        if(str(reaction) == "📝"):
            seen_message = f'> {message.content}\nOk, {user.mention}, I will add that to the general todolist'
            await channel.send(seen_message)

            task = Task(content=message.content, status="TODO")
            session.add(task)
            session.commit()

            def ask_attribute(m):
                return m.channel == channel and m.author == user

            await channel.send('Should I attribute the task to someone ?')
            try:
                msg = await self.wait_for('message', check=ask_attribute)
            except asyncio.TimeoutError:
                await channel.send('Ok, I let it go')
            else:
                if msg.content.lower().startswith("no"):
                    await channel.send(f'Ok, but my guess is nobody will do it !')
                elif len(msg.mentions) == 0:
                    await channel.send(f'You did not mention anyone...')
                else:
                    tasked_mentions = list_and([u.mention for u in msg.mentions])
                    
                    def create_or_get_user(user):
                        try:
                            u = session.query(User).filter(
                                                        User.discord_id == user.id
                                                   ).one()
                            u.name = user.name
                        except:
                            u = User(discord_id=user.id, mention=user.mention, name=user.name)
                        session.add(u)
                        session.commit()
                        return u

                    task.user_collection = [create_or_get_user(u) for u in  msg.mentions]
                    session.add(task)
                    session.commit()

                    await channel.send(f'Ok, it\'s been attributed to {tasked_mentions}')
        elif(str(reaction) == "☝️"):
            await channel.send(f'Not implemented yet')


bot = TaskDispatcherBot()
bot.run(TOKEN)
