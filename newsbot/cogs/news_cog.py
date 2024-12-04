import nextcord
from nextcord.ext import commands
from nextcord.ui import View, Button, Modal, TextInput, Select
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
import asyncio


class NewsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trusted_users = ["your user id here"]  # Replace with actual trusted user IDs

    @commands.command(name='news')
    async def news(self, ctx):
        """Start the news posting process."""
        if str(ctx.author.id) not in self.trusted_users:
            await ctx.send("You're not authorized to use this command!")
            return

        view = NewsTypeView(self.bot)
        await ctx.send("What kind of post would you like to make?", view=view)


class NewsTypeView(View):
    def __init__(self, bot):
        super().__init__(timeout=3600)  # 1 hour timeout
        self.bot = bot
        self.add_item(TextPostButton(bot))
        self.add_item(NewsSheetButton(bot))


class TextPostButton(Button):
    def __init__(self, bot):
        super().__init__(label="Text", style=nextcord.ButtonStyle.primary)
        self.bot = bot

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.send_modal(TextPostModal(self.bot))


class NewsSheetButton(Button):
    def __init__(self, bot):
        super().__init__(label="News Sheet", style=nextcord.ButtonStyle.primary)
        self.bot = bot

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.send_modal(NewsSheetModal(self.bot))


class TextPostModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Create Text Post")
        self.bot = bot
        self.add_item(TextInput(label="Title", style=nextcord.TextInputStyle.short))
        self.add_item(TextInput(label="Content", style=nextcord.TextInputStyle.paragraph))

    async def callback(self, interaction: nextcord.Interaction):
        title = self.children[0].value
        content = self.children[1].value

        # Request image upload or allow skipping
        await interaction.response.send_message("Please upload image files for the post or click 'None' to skip.", ephemeral=True)
        view = ImageUploadView(self.bot, interaction, title, content)
        await interaction.followup.send("Upload your image files here or click 'None' to skip:", view=view, ephemeral=True)


class NewsSheetModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Create News Sheet")
        self.bot = bot
        self.add_item(TextInput(label="Title", style=nextcord.TextInputStyle.short))
        self.add_item(TextInput(label="Content", style=nextcord.TextInputStyle.paragraph))

    async def callback(self, interaction: nextcord.Interaction):
        title = self.children[0].value
        content = self.children[1].value

        view = CategorySelectView(interaction, title, content, None, is_news_sheet=True)
        await interaction.response.send_message("Select a category:", view=view, ephemeral=True)


class ImageUploadView(View):
    def __init__(self, bot, interaction, title, content):
        super().__init__(timeout=3600)  # 1 hour timeout
        self.bot = bot
        self.interaction = interaction
        self.title = title
        self.content = content
        self.image_urls = []  # List to store uploaded image URLs

    @nextcord.ui.button(label="Upload Image(s)", style=nextcord.ButtonStyle.primary)
    async def upload_images(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # Prompt the user to upload images
        await interaction.response.send_message(
            "Please upload one or more image files in this channel. Type `done` when finished.", ephemeral=True
        )

        def check(m):
            return (
                m.author == interaction.user
                and m.channel == interaction.channel
                and (m.attachments or m.content.lower() == "done")
            )

        while True:
            try:
                message = await self.bot.wait_for("message", timeout=300, check=check)  # 5-minute timeout

                # Stop collecting images if the user types 'done'
                if message.content.lower() == "done":
                    if not self.image_urls:
                        await interaction.followup.send("No images uploaded. Please restart the process if needed.", ephemeral=True)
                        return
                    break

                # Check and add valid image attachments
                for attachment in message.attachments:
                    if attachment.content_type and "image" in attachment.content_type:
                        self.image_urls.append(attachment.url)
                    else:
                        await interaction.followup.send(
                            f"File `{attachment.filename}` is not a valid image. Skipping it.", ephemeral=True
                        )

            except asyncio.TimeoutError:
                await interaction.followup.send("You didn't upload images in time. Please restart the process.", ephemeral=True)
                return

        # Proceed to category selection after collecting images
        view = CategorySelectView(self.interaction, self.title, self.content, self.image_urls)
        await interaction.followup.send("Images uploaded! Select a category:", view=view, ephemeral=True)

    @nextcord.ui.button(label="None", style=nextcord.ButtonStyle.secondary)
    async def skip_images(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # Skip image upload and proceed to category selection
        view = CategorySelectView(self.interaction, self.title, self.content, None)
        await interaction.response.send_message("No images selected. Select a category:", view=view, ephemeral=True)


class CategorySelectView(View):
    def __init__(self, interaction, title, content, image_urls=None, is_news_sheet=False):
        super().__init__(timeout=3600)  # 1 hour timeout
        self.interaction = interaction
        self.title = title
        self.content = content
        self.image_urls = image_urls
        self.is_news_sheet = is_news_sheet
        self.category_id = None

        self.add_item(CategorySelect(interaction))
        self.add_item(CancelButton())


class CategorySelect(Select):
    def __init__(self, interaction):
        self.interaction = interaction
        categories = interaction.guild.categories
        options = [nextcord.SelectOption(label=category.name, value=str(category.id)) for category in categories]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        self.view.category_id = int(self.values[0])
        view = ChannelSelectView(self.view.interaction, self.view.title, self.view.content, self.view.image_urls, self.view.is_news_sheet, self.view.category_id)
        await interaction.response.edit_message(content="Select a channel:", view=view)


class ChannelSelectView(View):
    def __init__(self, interaction, title, content, image_urls=None, is_news_sheet=False, category_id=None):
        super().__init__(timeout=3600)  # 1 hour timeout
        self.interaction = interaction
        self.title = title
        self.content = content
        self.image_urls = image_urls
        self.is_news_sheet = is_news_sheet
        self.category_id = category_id
        self.channel_id = None

        self.update_select_menu()

    def update_select_menu(self):
        self.clear_items()
        self.add_item(ChannelSelect(self.interaction, self.category_id))
        self.add_item(CancelButton())
        self.add_item(OkButton())

    def create_news_sheet(self, title, content):
        # Load the newspaper template
        template_path = "/Users/Desktop/bots/news_records/template/template_image.png"  # Replace with your template path
        image = Image.open(template_path)
        draw = ImageDraw.Draw(image)

        # Load fonts
        font_title = ImageFont.truetype("/Users/Desktop/bots/news_records/font/open-sans/OpenSans-BoldItalic.ttf", 24)  # Replace with your font path
        base_font_size = 20

        # Image dimensions
        image_width, image_height = image.size

        # Adjust the title positioning below the header
        header_offset = 180  # Adjust this value based on the header height in the template
        title_bbox = font_title.getbbox(title)  # Get bounding box of the title
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (image_width - title_width) // 2
        draw.text((title_x, header_offset), title, font=font_title, fill="black")  # Draw the title

        # Calculate dynamic font size based on content length
        max_chars = 4000
        content_length = len(content)
        if content_length > max_chars:
            font_size = max(5, int(base_font_size * (max_chars / content_length)))
        else:
            font_size = base_font_size

        font_content = ImageFont.truetype("/Users/Desktop/bots/news_records/font/open-sans/OpenSans-Regular.ttf", font_size) #Your font path here

        # Format content as a single block
        margin = 50
        content_y_start = header_offset + 50  # Start content below the title
        line_spacing = 5

        # Split content into paragraphs based on double newlines
        paragraphs = content.split("\n\n")
        current_y = content_y_start

        for paragraph in paragraphs:
            wrapped_text = textwrap.fill(paragraph, width=110)  # Adjust width to fit the wider page
            for line in wrapped_text.split("\n"):
                line_bbox = font_content.getbbox(line)  # Get bounding box of each line
                line_height = line_bbox[3] - line_bbox[1]
                if current_y + line_height > image_height - 50:  # Stop if out of space
                    break
                draw.text((margin, current_y), line, font=font_content, fill="black")
                current_y += line_height + line_spacing
            current_y += line_spacing * 2  # Add spacing after each paragraph

        # Save the image
        output_path = f"news_records/posts/{title.replace(' ', '_')}.png"
        image.save(output_path)
        return output_path


class ChannelSelect(Select):
    def __init__(self, interaction, category_id):
        self.interaction = interaction
        category = nextcord.utils.get(interaction.guild.categories, id=category_id)
        channels = category.text_channels
        options = [nextcord.SelectOption(label=channel.name, value=str(channel.id)) for channel in channels]
        super().__init__(placeholder="Select a channel...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        self.view.channel_id = int(self.values[0])
        await interaction.response.send_message(f"Selected channel: <#{self.view.channel_id}>", ephemeral=True)


class CancelButton(Button):
    def __init__(self):
        super().__init__(label="Cancel", style=nextcord.ButtonStyle.danger)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.send_message("News posting cancelled.", ephemeral=True)
        self.view.stop()


class OkButton(Button):
    def __init__(self):
        super().__init__(label="OK", style=nextcord.ButtonStyle.success)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)  # Defer the interaction to avoid timeout
        channel = self.view.interaction.guild.get_channel(self.view.channel_id)
        if self.view.is_news_sheet:
            image_path = self.view.create_news_sheet(self.view.title, self.view.content)
            try:
                await channel.send(file=nextcord.File(image_path))
            except Exception as e:
                await interaction.followup.send(f"Failed to send image: {e}", ephemeral=True)
                return
            finally:
                if os.path.exists(image_path):
                    os.remove(image_path)
        else:
            embed = nextcord.Embed(title=self.view.title, description=self.view.content, color=0x00ff00)
            await channel.send(embed=embed)  # Send the main post content first

            if self.view.image_urls:
                for image_url in self.view.image_urls:
                    try:
                        image_embed = nextcord.Embed()
                        image_embed.set_image(url=image_url)
                        await channel.send(embed=image_embed)
                    except Exception as e:
                        await interaction.followup.send(f"Failed to attach image: {e}", ephemeral=True)
                        continue

        await interaction.followup.send("News posted successfully!", ephemeral=True)
        self.view.stop()



def setup(bot):
    bot.add_cog(NewsCog(bot))
