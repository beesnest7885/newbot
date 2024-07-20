import nextcord
from nextcord.ext import commands
import asyncio
import json
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import textwrap



class NewsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('trusted_users.json', 'r') as file:
            self.trusted_users = {str(user_id) for user_id in json.load(file)}

        if not os.path.exists("news_records/posts"):
            os.makedirs("news_records/posts")
        if not os.path.exists("news_records"):
            os.makedirs("news_records")


    
    @commands.command(name='news')
    async def start_news_thread(self, ctx):
        """Start a news thread for content creation."""
        
        # Check if the user is trusted
        if str(ctx.author.id) not in self.trusted_users:
            await ctx.send("You're not authorized to use this command!")
            return

        # If user is trusted, then proceed to create the thread.
        thread = await ctx.channel.create_thread(name="News Thread", type=nextcord.ChannelType.public_thread)
        await ctx.send(f"News thread created! Head over to {thread.mention} to add content.")


    
    @commands.command(name='post')
    async def post_news(self, ctx):
        # Check if the user is trusted
        if str(ctx.author.id) not in self.trusted_users:
            await ctx.send("You're not authorized to use this command!")
            return

        # Check if command is invoked inside a thread
        if not isinstance(ctx.message.channel, nextcord.Thread):
            await ctx.send("This command should be executed within a news thread!")
            return

        # Prompt user for the channel
        prompt_msg = await ctx.send("Please mention or name the channel where you'd like to post the news.")

        def check_channel_message(m):
            return m.author == ctx.author and m.channel == ctx.message.channel and m != ctx.message

        try:
            msg = await self.bot.wait_for('message', check=check_channel_message, timeout=30)
            channel_name_or_mention = msg.content.strip()
            channel = nextcord.utils.get(ctx.guild.text_channels, name=channel_name_or_mention)
            if channel is None:
                # If not found by name, try converting mention to channel object
                channel = await commands.TextChannelConverter().convert(ctx, channel_name_or_mention)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to provide a channel!")
            return

        # Aggregate the content from the thread
        content = ""
        async for message in ctx.message.channel.history(oldest_first=True):
            if message.id != ctx.message.id and message != prompt_msg and message.id != msg.id:
                content += f"{message.content}\n\n"

        # Create an embed for the content
        embed = nextcord.Embed(
            title="News Update",
            description="",
            color=nextcord.Color.blue(),  # You can choose a color that fits your theme
            timestamp=datetime.utcnow()
        )

        # Check if content fits in one embed, and add it
        if len(content) <= 4096:
            embed.description = content
        else:
            # Handle the case where content is too long
            embed.description = content[:4093] + "..."  # Truncate and indicate continuation
            # Here, you may want to send additional embeds or provide a link to the full content

        # Send the embed to the specified channel
        await channel.send(embed=embed)

        # Optionally, delete the thread
        await ctx.message.channel.delete()






    @commands.command(name='postimg')
    async def post_img_news(self, ctx):
        """Post the content of a news thread onto an image and then to a specified channel."""
        # Check if the user is trusted
        if str(ctx.author.id) not in self.trusted_users:
            await ctx.send("You're not authorized to use this command!")
            return

        # Check if command is invoked inside a thread
        if not isinstance(ctx.message.channel, nextcord.Thread):
            await ctx.send("This command should be executed within a news thread!")
            return

        # Prompt user for the channel
        prompt_msg = await ctx.send("Please mention or name the channel where you'd like to post the news.")
        def check_channel_message(m):
            return m.author == ctx.author and m.channel == ctx.message.channel and m != ctx.message

        try:
            msg = await self.bot.wait_for('message', check=check_channel_message, timeout=30)
            channel_name_or_mention = msg.content.strip()
            channel = nextcord.utils.get(ctx.guild.text_channels, name=channel_name_or_mention)
            if channel is None:
                channel = await commands.TextChannelConverter().convert(ctx, channel_name_or_mention)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to provide a channel!")
            return

        # Aggregate the content from the thread
        content = ""
        async for message in ctx.message.channel.history(oldest_first=True):
            if message.id != ctx.message.id and message != prompt_msg and message.id != msg.id:
                content += f"{message.content}\n\n"

        # Define text wrapping and image creation function with dynamic font size
        # ... (other code)

        def create_news_images(content, template_path):
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            font_path = "news_records/font/open-sans/OpenSans-Regular.ttf" # Update to your actual font path

            # We start by establishing the character limit for each line and the line limit for each page
            max_chars_per_line = 65
            max_lines_per_page = 20

            # Create font object with a base size
            base_font_size = 30  # Start with a base font size

            # Now we prepare the content by separating it into messages and then wrapping each message
            messages = content.strip().split('\n\n')  # Separate content into messages

            # Wrap each message separately to maintain the gap between messages
            wrapped_lines = []
            for message in messages:
                # Wrap this message and add it to the list
                wrapped_lines.extend(textwrap.wrap(message, width=max_chars_per_line))
                wrapped_lines.append('')  # Add a space after each message for clarity

            # Now, split the wrapped lines into pages
            pages = [wrapped_lines[i:i + max_lines_per_page] for i in range(0, len(wrapped_lines), max_lines_per_page)]

            image_paths = []
            for page_num, page in enumerate(pages, start=1):
                with Image.open(template_path) as image:
                    draw = ImageDraw.Draw(image)
                    font = ImageFont.truetype(font_path, base_font_size)
                    x, y = 70, 190
                    y_increment = base_font_size + 3  # Adjust line spacing based on font size

                    for line in page:
                        draw.text((x, y), line, fill="black", font=font)
                        y += y_increment  # Increment y position for each line

                    # Save each page as an image
                    saved_image_path = f"news_records/pages/news_page_{page_num}_{current_time}.png"
                    image.save(saved_image_path)
                    image_paths.append(saved_image_path)

            return image_paths

        # ... (other code)


        # Generate and preview the images
        image_paths = create_news_images(content, "news_records/template/template_image.png")

        # Send a preview of all images
        preview_messages = []  # List to keep track of all preview messages sent
        for img_path in image_paths:
            with open(img_path, "rb") as img_file:
                preview_message = await ctx.send(file=nextcord.File(img_file, filename=os.path.basename(img_path)))
                preview_messages.append(preview_message)  # Add the message to the list


        confirm_msg = await ctx.send("Do you want to post this image to the selected channel? Reply with 'yes' to confirm.")
        def check_confirm_message(m):
            return m.author == ctx.author and m.channel == ctx.message.channel

        try:
            confirm_response = await self.bot.wait_for('message', check=check_confirm_message, timeout=30)
            if confirm_response.content.lower() != 'yes':
                await ctx.send("Image posting cancelled.")
                return
        except asyncio.TimeoutError:
            await ctx.send("Confirmation not received in time. Image posting cancelled.")
            return

        # Post the images to the specified channel
        for img_path in image_paths:
            with open(img_path, "rb") as img_file:
                await channel.send(file=nextcord.File(img_file, filename=os.path.basename(img_path)))

        # Delete the thread after posting
        await ctx.message.channel.delete()

   

def setup(client):
    client.add_cog(NewsCog(client))
