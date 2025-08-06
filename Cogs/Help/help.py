

import discord
from discord.ext import commands
from discord.commands import slash_command

class CategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="🛡️ Moderasi",
                description="Perintah moderasi server",
                emoji="🛡️",
                value="moderation"
            ),
            discord.SelectOption(
                label="🎵 Musik",
                description="Perintah pemutar musik",
                emoji="🎵",
                value="music"
            ),
            discord.SelectOption(
                label="👤 Manajemen Role",
                description="Perintah role dan reaction role",
                emoji="👤",
                value="role"
            ),
            discord.SelectOption(
                label="🔍 Pencarian",
                description="Perintah pencarian Google",
                emoji="🔍",
                value="search"
            ),
            discord.SelectOption(
                label="⚙️ Pengaturan Server",
                description="Perintah konfigurasi server",
                emoji="⚙️",
                value="server"
            )
        ]
        super().__init__(placeholder="🎯 Pilih kategori untuk dijelajahi...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        
        if category == "moderation":
            embed = self.create_moderation_embed()
        elif category == "music":
            embed = self.create_music_embed()
        elif category == "role":
            embed = self.create_role_embed()
        elif category == "search":
            embed = self.create_search_embed()
        elif category == "server":
            embed = self.create_server_embed()
        
        view = CategoryView()
        await interaction.response.edit_message(embed=embed, view=view)

    def create_moderation_embed(self):
        embed = discord.Embed(
            title="🛡️ Perintah Moderasi",
            description="Alat moderasi yang kuat untuk menjaga server Anda tetap aman dan terorganisir",
            color=0xFF4B4B
        )
        
        commands_data = [
            ("🧹 /bersihkan", "Hapus pesan secara massal", "jumlah (1-100)"),
            ("👢 /tendang", "Keluarkan anggota dari server", "anggota, alasan (opsional)"),
            ("🔨 /ban", "Ban anggota secara permanen", "anggota, alasan (opsional)"),
            ("🔓 /batalban", "Batal ban anggota berdasarkan ID", "id_anggota"),
            ("🔇 /bisu", "Bisu anggota di server", "anggota, alasan (opsional)"),
            ("🔊 /batalbus", "Batal bisu anggota", "anggota"),
            ("⏰ /timeout", "Timeout anggota", "anggota, menit (1-40320)"),
            ("⚠️ /peringatkan", "Berikan peringatan kepada anggota", "anggota, alasan"),
            ("📋 /peringatan", "Lihat peringatan anggota", "anggota (opsional)"),
            ("🔒 /kunci", "Kunci channel", "channel (opsional)"),
            ("🔓 /bukakunci", "Buka kunci channel", "channel (opsional)"),
            ("🧹 /bersihkanbot", "Hapus pesan bot", "jumlah (opsional)"),
            ("📝 /slowmode", "Atur slowmode channel", "detik (0-21600)"),
            ("🏷️ /nick", "Ubah nickname anggota", "anggota, nickname_baru"),
            ("📊 /moderasi", "Panel kontrol moderasi interaktif", "anggota")
        ]
        
        for emoji_cmd, desc, params in commands_data:
            embed.add_field(
                name=emoji_cmd,
                value=f"**Fungsi:** {desc}\n**Parameter:** {params}",
                inline=True
            )
        
        embed.set_footer(text="🛡️ Memerlukan izin yang sesuai • Dioptimalkan untuk mobile")
        return embed

    def create_music_embed(self):
        embed = discord.Embed(
            title="🎵 Perintah Musik",
            description="Streaming musik berkualitas tinggi dari YouTube dengan manajemen antrian",
            color=0x1DB954
        )
        
        commands_data = [
            ("▶️ /putar", "Putar musik dari YouTube", "kueri (nama lagu atau URL)"),
            ("⏹️ /berhenti", "Hentikan musik dan hapus antrian", "Tidak ada"),
            ("⏭️ /lewati", "Lewati ke lagu berikutnya", "Tidak ada"),
            ("⏸️ /jeda", "Jeda lagu saat ini", "Tidak ada"),
            ("▶️ /lanjut", "Lanjutkan lagu yang dijeda", "Tidak ada"),
            ("📝 /antrian", "Tampilkan antrian musik", "Tidak ada"),
            ("🔀 /acak", "Acak urutan antrian", "Tidak ada"),
            ("🗑️ /hapus", "Hapus lagu dari antrian", "posisi (1-∞)"),
            ("🔊 /volume", "Atur volume musik", "level (1-100)"),
            ("🔁 /ulangi", "Ulangi lagu/antrian", "mode (lagu/antrian/mati)"),
            ("ℹ️ /sedangputar", "Info lagu yang sedang diputar", "Tidak ada"),
            ("💾 /simpan", "Simpan lagu ke playlist pribadi", "Tidak ada")
        ]
        
        for emoji_cmd, desc, params in commands_data:
            embed.add_field(
                name=emoji_cmd,
                value=f"**Fungsi:** {desc}\n**Parameter:** {params}",
                inline=True
            )
        
        embed.set_footer(text="🎵 Bergabunglah dengan voice channel terlebih dahulu • Audio berkualitas tinggi")
        return embed

    def create_role_embed(self):
        embed = discord.Embed(
            title="👤 Manajemen Role",
            description="Manajemen role canggih dengan reaction role dan otomatisasi",
            color=0x9B59B6
        )
        
        commands_data = [
            ("➕ /tambahrole", "Tambah role ke anggota", "anggota, role"),
            ("➖ /hapusrole", "Hapus role dari anggota", "anggota, role"),
            ("🎭 /tambah_reaction_role", "Buat reaction role", "role, channel, emoji"),
            ("🗑️ /hapus_reaction_role", "Hapus reaction role", "role"),
            ("📋 /daftar_reaction_role", "Daftar semua reaction role", "Tidak ada"),
            ("👤 /rolemanager", "Panel manajemen role interaktif", "anggota"),
            ("🔄 /sinkronrole", "Sinkronisasi role server", "Tidak ada"),
            ("📊 /inforole", "Informasi detail role", "role"),
            ("🎨 /warnrole", "Ubah warna role", "role, warna_hex"),
            ("👥 /anggotarole", "Daftar anggota dengan role", "role")
        ]
        
        for emoji_cmd, desc, params in commands_data:
            embed.add_field(
                name=emoji_cmd,
                value=f"**Fungsi:** {desc}\n**Parameter:** {params}",
                inline=True
            )
        
        embed.set_footer(text="👤 Bot harus memiliki izin Kelola Role")
        return embed

    def create_search_embed(self):
        embed = discord.Embed(
            title="🔍 Perintah Pencarian",
            description="Hasil pencarian Google instan dengan format yang cerdas",
            color=0xF39C12
        )
        
        embed.add_field(
            name="🔍 /cari",
            value="**Fungsi:** Cari Google untuk informasi\n**Parameter:** kueri (istilah pencarian)\n**Hasil:** 5 hasil teratas dengan deskripsi",
            inline=False
        )
        
        embed.add_field(
            name="✨ Fitur",
            value="• Penyaringan hasil yang cerdas\n• Format ramah mobile\n• Hasil instan\n• Pencarian aman diaktifkan",
            inline=True
        )
        
        embed.set_footer(text="🔍 Didukung oleh Google Search API")
        return embed

    def create_server_embed(self):
        embed = discord.Embed(
            title="⚙️ Pengaturan Server",
            description="Alat manajemen dan konfigurasi server yang komprehensif",
            color=0xE67E22
        )
        
        commands_data = [
            ("👥 /jumlah_anggota", "Tampilkan jumlah anggota server", "Tidak ada"),
            ("👋 /atur_selamatjalan", "Konfigurasi pesan selamat jalan", "aktif, channel, pesan"),
            ("🔄 /sinkron_perintah", "Sinkronisasi slash command", "Tidak ada (Khusus Admin)"),
            ("📊 /info_server", "Informasi detail server", "Tidak ada"),
            ("⚙️ /pengaturan", "Panel pengaturan server", "Tidak ada"),
            ("📢 /pengumuman", "Buat pengumuman server", "pesan, channel"),
            ("🔔 /notifikasi", "Atur sistem notifikasi", "tipe, channel"),
            ("📈 /statistik", "Statistik server lengkap", "Tidak ada"),
            ("🎯 /automod", "Pengaturan auto moderasi", "aktif/nonaktif"),
            ("💬 /atur_welcome", "Pengaturan pesan welcome", "Tidak ada")
        ]
        
        for emoji_cmd, desc, params in commands_data:
            embed.add_field(
                name=emoji_cmd,
                value=f"**Fungsi:** {desc}\n**Parameter:** {params}",
                inline=True
            )
        
        embed.add_field(
            name="🤖 Fitur Otomatis",
            value="• DM welcome untuk anggota baru\n• Log join/leave\n• Pengaturan otomatis per server\n• Notifikasi mobile",
            inline=False
        )
        
        embed.set_footer(text="⚙️ Pengaturan disimpan otomatis per server")
        return embed

class CategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(CategorySelect())

    @discord.ui.button(label="🏠 Menu Utama", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def main_menu(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 Bot Discord All-in-One",
            description="**Solusi manajemen server lengkap Anda**\n\n✨ Pilih kategori di bawah ini untuk menjelajahi perintah yang tersedia",
            color=0x00D4FF
        )
        
        embed.add_field(
            name="🌟 Fitur",
            value="```\n🛡️ Moderasi Canggih\n🎵 Musik Berkualitas Tinggi\n👤 Manajemen Role Cerdas\n🔍 Pencarian Instan\n⚙️ Otomatisasi Server```",
            inline=True
        )
        
        embed.add_field(
            name="📱 Dioptimalkan untuk Mobile",
            value="```\n✅ Tombol ramah sentuh\n✅ Layout responsif\n✅ Interaksi cepat\n✅ Performa lancar```",
            inline=True
        )
        
        embed.set_footer(text="🚀 Didukung oleh AI canggih • Dioptimalkan untuk mobile")
        
        view = CategoryView()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="📊 Statistik Bot", style=discord.ButtonStyle.success, emoji="📊")
    async def bot_stats(self, button: discord.ui.Button, interaction: discord.Interaction):
        bot = interaction.client
        
        embed = discord.Embed(
            title="📊 Statistik Bot",
            description="Metrik performa real-time",
            color=0x00FF88
        )
        
        embed.add_field(name="🏠 Server", value=f"```{len(bot.guilds)}```", inline=True)
        embed.add_field(name="👥 Pengguna", value=f"```{len(bot.users)}```", inline=True)
        embed.add_field(name="🔗 Latency", value=f"```{round(bot.latency * 1000)}ms```", inline=True)
        embed.add_field(name="⚡ Perintah", value="```50+ Perintah```", inline=True)
        embed.add_field(name="🎵 Kualitas Musik", value="```320kbps```", inline=True)
        embed.add_field(name="📱 Siap Mobile", value="```100%```", inline=True)
        
        embed.set_footer(text="📊 Diperbarui secara real-time")
        
        view = CategoryView()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🆘 Bantuan", style=discord.ButtonStyle.danger, emoji="🆘")
    async def support(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🆘 Butuh Bantuan?",
            description="Dapatkan dukungan dan pelajari lebih lanjut tentang bot",
            color=0xFF3366
        )
        
        embed.add_field(
            name="📝 Tips Cepat",
            value="• Gunakan `/bantuan` untuk kategori perintah\n• Periksa izin jika perintah gagal\n• Bergabung dengan voice channel untuk musik\n• Laporkan bug via DM ke pemilik bot",
            inline=False
        )
        
        embed.add_field(
            name="⚡ Status",
            value="🟢 **Online**\n🔄 Update otomatis\n📱 Dioptimalkan untuk mobile",
            inline=True
        )
        
        embed.set_footer(text="🆘 Dukungan tersedia 24/7")
        
        view = CategoryView()
        await interaction.response.edit_message(embed=embed, view=view)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="bantuan", description="🎯 Menu bantuan interaktif dengan kategori dan tombol")
    async def help(self, ctx):
        """Sistem bantuan interaktif modern dengan kategori dan tombol"""
        
        embed = discord.Embed(
            title="🤖 Bot Discord All-in-One",
            description="**Solusi manajemen server lengkap Anda**\n\n✨ Pilih kategori di bawah ini untuk menjelajahi perintah yang tersedia",
            color=0x00D4FF
        )
        
        embed.add_field(
            name="🌟 Fitur",
            value="```\n🛡️ Moderasi Canggih\n🎵 Musik Berkualitas Tinggi\n👤 Manajemen Role Cerdas\n🔍 Pencarian Instan\n⚙️ Otomatisasi Server```",
            inline=True
        )
        
        embed.add_field(
            name="📱 Dioptimalkan untuk Mobile",
            value="```\n✅ Tombol ramah sentuh\n✅ Layout responsif\n✅ Interaksi cepat\n✅ Performa lancar```",
            inline=True
        )
        
        embed.set_footer(text="🚀 Didukung oleh AI canggih • Dioptimalkan untuk mobile")
        
        view = CategoryView()
        await ctx.respond(embed=embed, view=view)

def setup(bot):
    bot.add_cog(Help(bot))
    print("Enhanced Help cog dimuat dengan UI interaktif")

