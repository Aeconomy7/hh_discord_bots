import math
import discord
from discord.ui import View, Button

class PageableEmbedView(View):
    def __init__(self, pages, user_id, title="Results", per_page=1):
        super().__init__(timeout=120)
        self.pages = pages
        self.user_id = user_id
        self.page = 0
        self.title = title
        self.per_page = per_page

        self.prev_button = Button(label="⬅️ Prev", style=discord.ButtonStyle.secondary)
        self.next_button = Button(label="Next ➡️", style=discord.ButtonStyle.secondary)
        self.prev_button.callback = self.prev_page
        self.next_button.callback = self.next_page
        self.add_item(self.prev_button)
        self.add_item(self.next_button)

    async def prev_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You can't control this pagination.", ephemeral=True)
            return
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You can't control this pagination.", ephemeral=True)
            return
        if self.page < len(self.pages) - 1:
            self.page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    def get_embed(self):
        embed = discord.Embed(title=self.title, description=self.pages[self.page], color=discord.Color.blue())
        embed.set_footer(text=f"Page {self.page+1}/{len(self.pages)}")
        return embed