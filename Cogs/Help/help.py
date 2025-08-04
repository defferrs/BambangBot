
import discord
from discord.ext import commands
from discord.commands import slash_command

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Tampilkan bantuan untuk semua command bot")
    async def help(self, ctx):
        """Menampilkan bantuan lengkap untuk semua command bot"""
        
        # Main help embed
        main_embed = discord.Embed(
            title="🤖 Bantuan Bot Discord",
            description="Pilih kategori di bawah untuk melihat command yang tersedia:",
            color=discord.Color.blue()
        )
        
        main_embed.add_field(
            name="📋 Kategori Command",
            value=(
                "🛡️ **Moderation** - Command moderasi server\n"
                "🎵 **Music** - Command pemutar musik\n"
                "👤 **Role** - Command manajemen role\n"
                "🔍 **Search** - Command pencarian Google\n"
                "⚙️ **Server** - Command pengaturan server"
            ),
            inline=False
        )
        
        main_embed.set_footer(text="Gunakan /help_moderation, /help_music, /help_role, /help_search, atau /help_server untuk detail")
        
        await ctx.respond(embed=main_embed)

    @slash_command(description="Bantuan command moderasi")
    async def help_moderation(self, ctx):
        """Bantuan untuk command moderasi"""
        embed = discord.Embed(
            title="🛡️ Command Moderasi",
            description="Command untuk moderasi dan manajemen server",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="/clear",
            value="**Fungsi:** Hapus sejumlah pesan di channel\n**Parameter:** amount (jumlah pesan)\n**Permission:** Manage Messages",
            inline=False
        )
        
        embed.add_field(
            name="/kick",
            value="**Fungsi:** Keluarkan member dari server\n**Parameter:** member (member yang akan dikeluarkan)\n**Permission:** Kick Members",
            inline=False
        )
        
        embed.add_field(
            name="/ban",
            value="**Fungsi:** Ban member dari server secara permanen\n**Parameter:** member (member yang akan di-ban)\n**Permission:** Ban Members",
            inline=False
        )
        
        embed.add_field(
            name="/unban",
            value="**Fungsi:** Batalkan ban member dengan ID\n**Parameter:** member_id (ID member yang akan di-unban)\n**Permission:** Ban Members",
            inline=False
        )
        
        embed.add_field(
            name="/mute",
            value="**Fungsi:** Bisu member di server (memerlukan role 'Muted')\n**Parameter:** member (member yang akan dibisu)\n**Permission:** Manage Roles",
            inline=False
        )
        
        embed.add_field(
            name="/unmute",
            value="**Fungsi:** Batalkan bisu member di server\n**Parameter:** member (member yang akan dibatalkan bisuannya)\n**Permission:** Manage Roles",
            inline=False
        )
        
        embed.add_field(
            name="/timeout",
            value="**Fungsi:** Berikan timeout kepada member\n**Parameter:** member, minutes (durasi dalam menit)\n**Permission:** Moderate Members",
            inline=False
        )
        
        embed.add_field(
            name="/warn",
            value="**Fungsi:** Berikan peringatan kepada member\n**Parameter:** member (member yang akan diberi peringatan)\n**Permission:** Kick Members",
            inline=False
        )
        
        embed.add_field(
            name="/warnings",
            value="**Fungsi:** Lihat jumlah peringatan member\n**Parameter:** member (member yang akan dilihat peringatannya)\n**Permission:** Semua",
            inline=False
        )
        
        embed.set_footer(text="⚠️ Pastikan bot memiliki permission yang diperlukan untuk setiap command")
        
        await ctx.respond(embed=embed)

    @slash_command(description="Bantuan command musik")
    async def help_music(self, ctx):
        """Bantuan untuk command musik"""
        embed = discord.Embed(
            title="🎵 Command Musik",
            description="Command untuk memutar musik dari YouTube",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="/play",
            value="**Fungsi:** Putar musik dari YouTube atau URL\n**Parameter:** query (nama lagu atau URL YouTube)\n**Requirement:** Harus berada di voice channel",
            inline=False
        )
        
        embed.add_field(
            name="/stop",
            value="**Fungsi:** Hentikan musik dan keluar dari voice channel\n**Parameter:** Tidak ada\n**Effect:** Menghapus seluruh antrian",
            inline=False
        )
        
        embed.add_field(
            name="/skip",
            value="**Fungsi:** Lewati lagu yang sedang diputar\n**Parameter:** Tidak ada\n**Effect:** Lanjut ke lagu berikutnya dalam antrian",
            inline=False
        )
        
        embed.add_field(
            name="/pause",
            value="**Fungsi:** Jeda lagu yang sedang diputar\n**Parameter:** Tidak ada\n**Note:** Gunakan /resume untuk melanjutkan",
            inline=False
        )
        
        embed.add_field(
            name="/resume",
            value="**Fungsi:** Lanjutkan lagu yang dijeda\n**Parameter:** Tidak ada\n**Note:** Hanya bekerja jika ada lagu yang dijeda",
            inline=False
        )
        
        embed.add_field(
            name="/queue",
            value="**Fungsi:** Tampilkan daftar antrian musik\n**Parameter:** Tidak ada\n**Info:** Menampilkan semua lagu dalam antrian",
            inline=False
        )
        
        embed.add_field(
            name="/shuffle",
            value="**Fungsi:** Acak urutan antrian musik\n**Parameter:** Tidak ada\n**Effect:** Mengacak urutan lagu dalam antrian",
            inline=False
        )
        
        embed.add_field(
            name="/remove",
            value="**Fungsi:** Hapus lagu dari antrian berdasarkan posisi\n**Parameter:** position (posisi lagu dalam antrian)\n**Note:** Posisi dimulai dari 1",
            inline=False
        )
        
        embed.set_footer(text="🎵 Bot harus berada di voice channel yang sama dengan user")
        
        await ctx.respond(embed=embed)

    @slash_command(description="Bantuan command role")
    async def help_role(self, ctx):
        """Bantuan untuk command role"""
        embed = discord.Embed(
            title="👤 Command Role",
            description="Command untuk manajemen role dan reaction role",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="/addrole",
            value="**Fungsi:** Tambahkan role kepada member\n**Parameter:** member, role\n**Permission:** Manage Roles\n**Note:** Mengirim DM konfirmasi ke member",
            inline=False
        )
        
        embed.add_field(
            name="/removerole",
            value="**Fungsi:** Hapus role dari member\n**Parameter:** member, role\n**Permission:** Manage Roles\n**Note:** Mengirim DM konfirmasi ke member",
            inline=False
        )
        
        embed.add_field(
            name="/add_reaction_role",
            value="**Fungsi:** Tambahkan reaction role ke pesan terbaru di channel\n**Parameter:** role, channel, emoji\n**Permission:** Manage Roles\n**Note:** Otomatis menambah reaction ke pesan",
            inline=False
        )
        
        embed.add_field(
            name="/remove_reaction_role",
            value="**Fungsi:** Hapus reaction role dari role tertentu\n**Parameter:** role\n**Permission:** Manage Roles\n**Effect:** Menghapus sistem reaction role untuk role tersebut",
            inline=False
        )
        
        embed.add_field(
            name="/list_reaction_roles",
            value="**Fungsi:** Tampilkan daftar reaction role yang ada\n**Parameter:** Tidak ada\n**Permission:** Manage Roles\n**Info:** Menampilkan semua reaction role aktif",
            inline=False
        )
        
        embed.set_footer(text="👤 Bot harus memiliki permission Manage Roles dan berada di atas role yang dikelola")
        
        await ctx.respond(embed=embed)

    @slash_command(description="Bantuan command pencarian")
    async def help_search(self, ctx):
        """Bantuan untuk command pencarian"""
        embed = discord.Embed(
            title="🔍 Command Pencarian",
            description="Command untuk mencari informasi di Google",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="/search",
            value="**Fungsi:** Cari informasi di Google\n**Parameter:** query (kata kunci pencarian)\n**Output:** 5 hasil pencarian teratas\n**Format:** Embedded message dengan link hasil",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Informasi Tambahan",
            value=(
                "• Pencarian menggunakan Google Search API\n"
                "• Hasil ditampilkan dalam format embed\n"
                "• Maksimal 5 hasil per pencarian\n"
                "• Delay 2 detik antar request untuk menghindari rate limit"
            ),
            inline=False
        )
        
        embed.set_footer(text="🔍 Gunakan kata kunci yang spesifik untuk hasil terbaik")
        
        await ctx.respond(embed=embed)

    @slash_command(description="Bantuan command pengaturan server")
    async def help_server(self, ctx):
        """Bantuan untuk command pengaturan server"""
        embed = discord.Embed(
            title="⚙️ Command Pengaturan Server",
            description="Command untuk mengatur welcome message dan member count",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="/member_count",
            value="**Fungsi:** Tampilkan jumlah member server\n**Parameter:** Tidak ada\n**Info:** Menampilkan total member saat ini\n**Permission:** Semua",
            inline=False
        )
        
        embed.add_field(
            name="/setup_goodbye",
            value="**Fungsi:** Konfigurasi pesan goodbye untuk member yang keluar\n**Parameter:** enabled, channel (opsional), goodbye_message (opsional)\n**Permission:** Manage Guild\n**Note:** Menggunakan {member} sebagai placeholder",
            inline=False
        )
        
        embed.add_field(
            name="/sync_commands",
            value="**Fungsi:** Sinkronisasi slash commands secara manual\n**Parameter:** Tidak ada\n**Permission:** Administrator\n**Usage:** Gunakan jika command tidak muncul",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Auto Features",
            value=(
                "• **Welcome DM:** Bot otomatis mengirim DM welcome ke member baru\n"
                "• **Member Join Log:** Bot mencatat member baru di console\n"
                "• **Auto Settings:** Pengaturan otomatis dibuat untuk setiap server"
            ),
            inline=False
        )
        
        embed.set_footer(text="⚙️ Pengaturan disimpan otomatis dan berlaku per server")
        
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Help(bot))
    print("Help cog loaded")
