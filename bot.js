const TelegramBot = require('node-telegram-bot-api');
const { exec } = require('child_process');
const { Pool } = require('pg'); // Pool ayaa ka fiican Client xiriirka joogtada ah
const fs = require('fs');

const token = process.env.BOT_TOKEN;
const ADMIN_ID = 6301321523; 
const bot = new TelegramBot(token, { polling: { params: { drop_pending_updates: true } } });

// Database Connection with Auto-Fix for your Error
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false },
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
});

async function initDB() {
    try {
        await pool.query(`
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                downloads INT DEFAULT 0,
                country TEXT DEFAULT 'Unknown',
                lang_fixed BOOLEAN DEFAULT FALSE
            );
        `);
        console.log("Database Operational ✅");
    } catch (err) {
        console.error("DB Initialization Error:", err.message);
    }
}
initDB();

// --- ADMIN PANEL ---
bot.onText(/\/admin/, async (msg) => {
    if (msg.from.id !== ADMIN_ID) return;
    const res = await pool.query("SELECT COUNT(*) FROM users");
    bot.sendMessage(msg.chat.id, `👑 **Admin Panel**\n\nTotal Users: ${res.rows[0].count}\n\n/broadcast [text]\n/users - All IDs\n/list - Download Leaderboard`);
});

bot.onText(/\/broadcast (.+)/, async (msg, match) => {
    if (msg.from.id !== ADMIN_ID) return;
    const users = await pool.query("SELECT user_id FROM users");
    users.rows.forEach(u => bot.sendMessage(u.user_id, match[1]).catch(() => {}));
    bot.sendMessage(msg.chat.id, "✅ Broadcast Sent.");
});

bot.onText(/\/list/, async (msg) => {
    if (msg.from.id !== ADMIN_ID) return;
    const res = await pool.query("SELECT username, downloads FROM users ORDER BY downloads DESC LIMIT 20");
    let text = "📋 **User Leaderboard:**\n\n";
    res.rows.forEach(u => { text += `👤 ${u.username || 'User'} - 📥 ${u.downloads}\n`; });
    bot.sendMessage(msg.chat.id, text);
});

// --- USER COMMANDS (ENGLISH) ---
bot.onText(/\/start/, async (msg) => {
    const user = msg.from;
    await pool.query("INSERT INTO users (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET username = $2", [user.id, user.first_name]);
    bot.sendMessage(msg.chat.id, `Hi ${user.first_name}, send any link ✨`, {
        reply_markup: { inline_keyboard: [[{ text: "Discord 🔗", url: "https://discord.gg/j6WZkksV8" }]] }
    });
});

bot.onText(/\/rank/, async (msg) => {
    const userRes = await pool.query("SELECT downloads, country FROM users WHERE user_id = $1", [msg.from.id]);
    const totalRes = await pool.query("SELECT SUM(downloads) as total FROM users");
    const topCountry = await pool.query("SELECT country, COUNT(*) as count FROM users WHERE country != 'Unknown' GROUP BY country ORDER BY count DESC LIMIT 1");
    
    const user = userRes.rows[0];
    let text = `📊 **Rank Stats**\n\n📥 Global Downloads: ${totalRes.rows[0].total || 0}\n🌍 Top Country: ${topCountry.rows[0]?.country || 'None'}\n📅 Rank Started: Feb 2026\n\n👤 **Your Stats:**\n📍 Country: ${user?.country || 'Not Set'}\n📥 Downloads: ${user?.downloads || 0}`;
    bot.sendMessage(msg.chat.id, text);
});

bot.onText(/\/lang/, async (msg) => {
    const res = await pool.query("SELECT lang_fixed FROM users WHERE user_id = $1", [msg.from.id]);
    if (res.rows[0]?.lang_fixed) return bot.sendMessage(msg.chat.id, "❌ Error: Country selection is permanent.");

    const countries = ["Somalia 🇸🇴", "USA 🇺🇸", "UK 🇬🇧", "Kenya 🇰🇪", "Turkey 🇹🇷", "UAE 🇦🇪", "Canada 🇨🇦", "Sweden 🇸🇪"];
    const keyboard = countries.map(c => [{ text: c, callback_data: `ln_${c}` }]);
    bot.sendMessage(msg.chat.id, "Select your country (One-time only):", { reply_markup: { inline_keyboard: keyboard } });
});

// --- UNIVERSAL ENGINE (SNAP, IG, FB, YT, TIKTOK, ETC.) ---
bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const url = msg.text;

    if (!url || url.startsWith('/') || !url.startsWith('http')) return;

    const wait = await bot.sendMessage(chatId, "✨");

    const output = `downloads/${Date.now()}.mp4`;
    // The Ultimate Universal Downloader Command
    const cmd = `yt-dlp -f "best" --no-check-certificate --user-agent "Mozilla/5.0" -o "${output}" "${url}"`;

    exec(cmd, async (err) => {
        if (err) return bot.editMessageText("It's Broken 💔", { chat_id: chatId, message_id: wait.message_id });

        await bot.sendVideo(chatId, output, {
            caption: "For You 🖤🥀 - @Fastdowloder1bot",
            reply_markup: { inline_keyboard: [[{ text: "Audio 🎙️", callback_data: `au_${url}` }], [{ text: "Community 🌋", url: "https://t.me/cummunutry1" }]] }
        });
        
        await pool.query("UPDATE users SET downloads = downloads + 1 WHERE user_id = $1", [chatId]);
        bot.deleteMessage(chatId, wait.message_id);
        if (fs.existsSync(output)) fs.unlinkSync(output);
    });
});

bot.on('callback_query', async (q) => {
    if (q.data.startsWith('ln_')) {
        const c = q.data.split('_')[1];
        await pool.query("UPDATE users SET country = $1, lang_fixed = TRUE WHERE user_id = $2", [c, q.from.id]);
        bot.answerCallbackQuery(q.id, { text: "Saved!" });
        bot.sendMessage(q.message.chat.id, `✅ Country set to: ${c}`);
    }
});
