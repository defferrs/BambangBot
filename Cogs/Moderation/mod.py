import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.commands import Option  #Importing the packages
import datetime
import json


class Moderation(commands.Cog):
    def __init__(self, bot):#to Initialise
        self.bot = bot


    @slash_command(description="Hapus sejumlah pesan di channel ini")
    @commands.has_permissions(manage_messages = True)
    async def clear(self, ctx, amount: Option(int, "Jumlah pesan yang akan dihapus")):    
        await ctx.channel.purge(limit = amount)
        await ctx.respond(f"✅ Berhasil menghapus {amount} pesan dari channel ini.")
    
    
    @slash_command(description="Keluarkan member dari server")
    @commands.has_permissions(kick_members = True)
    async def kick(self, ctx, member: Option(discord.Member, "Member yang akan dikeluarkan")):
    
        await member.kick(reason=None)
        await ctx.respond(f"✅ {member.mention} telah dikeluarkan dari server.")
    
    
    @slash_command(description="Banned member dari server secara permanen")
    @commands.has_permissions(ban_members = True)
    async def ban(self, ctx, member: Option(discord.Member, "Member yang akan di-ban")):
    
        await member.ban(reason=None, delete_message_days=0)
        await ctx.respond(f"🔨 {member.mention} telah di-ban dari server secara permanen.")    


    @commands.command(description="Batalkan ban member dengan ID")
    @commands.has_permissions(ban_members = True)
    async def unban(self, ctx, *, member_id: int):
        
        user = await self.bot.fetch_user(member_id)
        await ctx.guild.unban(user, reason=None)
        await ctx.send(f"✅ {user.mention} telah di-unban dari server.")
    
    @slash_command(description="Bisu member di server (memerlukan role 'Muted')")
    @commands.has_permissions(manage_roles = True)
    async def mute(self, ctx, member: Option(discord.Member, "Member yang akan dibisu")):
        muted_role = ctx.guild.get_role(1234567890)#get the muted role with ID - UPDATE THIS WITH YOUR ACTUAL ROLE ID
        
        if not muted_role:
            await ctx.respond("🚫 Role 'Muted' tidak ditemukan! Silakan periksa ID role.")
            return
    
        await member.add_roles(muted_role)
    
        await ctx.respond(f"🔇 {member.mention} telah dibisu di server.")


    @slash_command(description="Batalkan bisu member di server")
    @commands.has_permissions(manage_roles = True)
    async def unmute(self, ctx, member: Option(discord.Member, "Member yang akan dibatalkan bisuannya")):
        muted_role = ctx.guild.get_role(1234567890)#get the muted role with ID - UPDATE THIS WITH YOUR ACTUAL ROLE ID
        
        if not muted_role:
            await ctx.respond("🚫 Role 'Muted' tidak ditemukan! Silakan periksa ID role.")
            return
    
        await member.remove_roles(muted_role)
    
        await ctx.respond(f"🔊 {member.mention} telah dibatalkan bisuannya.")                                                   
                                                 

    # membercount command moved to memberjoin.py to avoid duplicates
	
    @slash_command(description="Berikan timeout kepada member untuk waktu tertentu")
    async def timeout(self, ctx, member: Option(discord.Member, "Member yang akan di-timeout"), minutes: Option(int, "Durasi timeout dalam menit")):
        """Apply a timeout to a member"""

        duration = datetime.timedelta(minutes=minutes)
        await member.timeout_for(duration)
        await ctx.respond(f"⏰ {member.mention} telah di-timeout selama {minutes} menit.")	


#Warn command section(it is still in the same class)-----------------------------------------------------

    @slash_command(description="Lihat jumlah peringatan member")    
    async def warnings(self, ctx, member: Option(discord.Member, "Member yang akan dilihat peringatannya")):
        await self.open_account(member)

        users = await self.get_user_data()

        warns = users[str(member.id)]["warns"]

        await ctx.respond(f"⚠️ {member.mention} memiliki {warns} peringatan.")

    @slash_command(description="Berikan peringatan kepada member")    
    @commands.has_permissions(kick_members = True)
    async def warn(self, ctx, member: Option(discord.Member, "Member yang akan diberi peringatan")):
        await self.open_account(member)

        users = await self.get_user_data()

        warns = await self.add_warn(member)

        await ctx.respond(f"⚠️ {member.mention} telah diberi peringatan. Total peringatan: {warns}.")
	
	
    async def open_account(self, user):
        with open ("./Cogs/Moderation/reports.json","r")as f:
            users = json.load(f)
        if str (user.id) in users:
            return False
        else:
            users[str(user.id)] = {}
            users[str(user.id)]["warns"] = 0
        
        with open("./Cogs/Moderation/reports.json","w")as f:
            json.dump(users, f)
	
	
    async def get_user_data(self):
        with open ("./Cogs/Moderation/reports.json","r")as f:
            users = json.load(f)
        return users


    async def add_warn(self, user, change = 1, mode = "warns"):
        users = await self.get_user_data()
    
        users[str(user.id)][mode] += change
    
        with open("./Cogs/Moderation/reports.json","w")as f:
            json.dump(users, f)
        
        warns = users[str(user.id)][mode]
    
        return warns	


# ----------------------------------------------------------------

# Note that you have to copy and paste all this code into yours or if you are more advanced feel free to do whatever you want. Enjoy~!
# This code is not specifically for 1 server your bot can execute this code on any server 

# Reaction role functionality removed - contains undefined references




def setup(bot):
    bot.add_cog(Moderation(bot))