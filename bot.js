const TelegramBot = require('node-telegram-bot-api');
const { exec } = require('child_process');
const { Pool } = require('pg');
const fs = require('fs');

const token = process.env.BOT_TOKEN;
const ADMIN_ID = 6301321523; 
// drop_pending_updates: true wuxuu xallinayaa error-ka Conflict ee sawirkaaga ku jira
const bot = new TelegramBot(token, { polling: { params: { drop_pending_updates: true } } });

const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
});

async function initDB() {
    try {
        // Halkan waxaan ku daray "IF NOT EXISTS" si columns-ku u dhismaan haddii ay maqan yihiin
        await pool.query(`
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                downloads INT DEFAULT 0,
                country TEXT DEFAULT 'Unknown',
                lang_fixed BOOLEAN DEFAULT FALSE
            );
        `);
        // Hubinta columns-ka haddii ay hore u jireen laakiin ay downloads/lang_fixed ka maqan yihiin
        await pool.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS downloads INT DEFAULT 0;`).catch(()=>{});
        await pool.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS lang_fixed BOOLEAN DEFAULT FALSE;`).catch(()=>{});
        console.log("Database & Columns Ready ✅");
    } catch (err) { console.error("DB Error:", err.message); }
}
initDB();

// --- COMMANDS ---
bot.onText(/\/start/, async (msg) => {
    const user = msg.from;
    await pool.query("INSERT INTO users (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET username = $2", [user.id, user.first_name]);
    bot.sendMessage(msg.chat.id, `Hi ${user.first_name}, send any link (Snap, IG, YT, TikTok) ✨`);
});

bot.onText(/\/lang/, async (msg) => {
    const res = await pool.query("SELECT lang_fixed FROM users WHERE user_id = $1", [msg.from.id]);
    if (res.rows[0]?.lang_fixed) return bot.sendMessage(msg.chat.id, "❌ Error: Country selection is permanent.");
    const countries = ["Somalia 🇸🇴", "USA 🇺🇸", "UK 🇬🇧", "Kenya 🇰🇪", "Turkey 🇹🇷", "UAE 🇦🇪"];
    const keyboard = countries.map(c => [{ text: c, callback_data: `ln_${c}` }]);
    bot.sendMessage(msg.chat.id, "Select country (One-time only):", { reply_markup: { inline_keyboard: keyboard } });
});

bot.onText(/\/rank/, async (msg) => {
    const userRes = await pool.query("SELECT downloads, country FROM users WHERE user_id = $1", [msg.from.id]);
    const totalRes = await pool.query("SELECT SUM(downloads) as total FROM users");
    const topCountry = await pool.query("SELECT country, COUNT(*) as count FROM users WHERE country != 'Unknown' GROUP BY country ORDER BY count DESC LIMIT 1");
    let text = `📊 **Stats**\nGlobal Downloads: ${totalRes.rows[0].total || 0}\nTop Country: ${topCountry.rows[0]?.country || 'None'}\n\n👤 **You:**\nCountry: ${userRes.rows[0]?.country || 'Not Set'}\nDownloads: ${userRes.rows[0]?.downloads || 0}`;
    bot.sendMessage(msg.chat.id, text);
});

// --- ADMIN ---
bot.onText(/\/admin/, async (msg) => {
    if (msg.from.id !== ADMIN_ID) return;
    const res = await pool.query("SELECT COUNT(*) FROM users");
    bot.sendMessage(msg.chat.id, `👑 **Admin Panel**\nTotal Users: ${res.rows[0].count}\n/broadcast [text]\n/list - Leaderboard`);
});

// --- UNIVERSAL DOWNLOADER (FOR SNAPCHAT, IG, FB, ETC.) ---
bot.on('message', async (msg) => {
    if (!msg.text || msg.text.startsWith('/') || !msg.text.startsWith('http')) return;
    const wait = await bot.sendMessage(msg.chat.id, "✨");
    const output = `downloads/${Date.now()}.mp4`;
    // yt-dlp is the key to downloading everything (Snapchat included)
    exec(`yt-dlp -f "best" --no-check-certificate -o "${output}" "${msg.text}"`, async (err) => {
        if (err) return bot.editMessageText("It's Broken 💔 (Link not supported or server busy)", { chat_id: msg.chat.id, message_id: wait.message_id });
        await bot.sendVideo(msg.chat.id, output, { caption: "For You 🖤🥀 - @Fastdowloder1bot" });
        await pool.query("UPDATE users SET downloads = downloads + 1 WHERE user_id = $1", [msg.chat.id]);
        bot.deleteMessage(msg.chat.id, wait.message_id);
        if (fs.existsSync(output)) fs.unlinkSync(output);
    });
});

bot.on('callback_query', async (q) => {
    if (q.data.startsWith('ln_')) {
        const c = q.data.split('_')[1];
        await pool.query("UPDATE users SET country = $1, lang_fixed = TRUE WHERE user_id = $2", [c, q.from.id]);
        bot.sendMessage(q.message.chat.id, `✅ Country set to: ${c}`);
    }
});
