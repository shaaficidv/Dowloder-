const TelegramBot = require('node-telegram-bot-api');
const { exec } = require('child_process');
const { Client } = require('pg');
const fs = require('fs');
const axios = require('axios');

const token = process.env.BOT_TOKEN;
const ADMIN_ID = 6301321523; // Ensure this is your ID
const bot = new TelegramBot(token, { polling: { params: { drop_pending_updates: true } } });

const client = new Client({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
});

async function initDB() {
    await client.connect();
    await client.query(`
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            downloads INT DEFAULT 0,
            country TEXT DEFAULT 'Unknown',
            lang_fixed BOOLEAN DEFAULT FALSE
        );
    `);
    console.log("Database Ready ✅");
}
initDB().catch(err => console.error(err));

// --- ADMIN PANEL ---

bot.onText(/\/admin/, async (msg) => {
    if (msg.from.id !== ADMIN_ID) return;
    const res = await client.query("SELECT COUNT(*) FROM users");
    bot.sendMessage(msg.chat.id, `👑 **Admin Panel**\n\nTotal Users: ${res.rows[0].count}\n\n/broadcast - Message to all\n/users - See all IDs\n/list - See download leaderboard`);
});

bot.onText(/\/broadcast (.+)/, async (msg, match) => {
    if (msg.from.id !== ADMIN_ID) return;
    const users = await client.query("SELECT user_id FROM users");
    let count = 0;
    for (let u of users.rows) {
        try { await bot.sendMessage(u.user_id, match[1]); count++; } catch (e) {}
    }
    bot.sendMessage(msg.chat.id, `✅ Broadcast sent to ${count} users.`);
});

bot.onText(/\/users/, async (msg) => {
    if (msg.from.id !== ADMIN_ID) return;
    const res = await client.query("SELECT user_id FROM users");
    let text = "🆔 **Bot User IDs:**\n\n";
    res.rows.forEach(u => { text += `\`${u.user_id}\`\n`; });
    bot.sendMessage(msg.chat.id, text, { parse_mode: 'Markdown' });
});

bot.onText(/\/list/, async (msg) => {
    if (msg.from.id !== ADMIN_ID) return;
    const res = await client.query("SELECT username, downloads FROM users ORDER BY downloads DESC LIMIT 50");
    let text = "📋 **User Download List:**\n\n";
    res.rows.forEach(u => { text += `👤 ${u.username} - 📥 ${u.downloads}\n`; });
    bot.sendMessage(msg.chat.id, text);
});

// --- USER COMMANDS (ENGLISH) ---

bot.onText(/\/start/, async (msg) => {
    const user = msg.from;
    await client.query("INSERT INTO users (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET username = $2", [user.id, user.first_name]);
    bot.sendMessage(msg.chat.id, `Hi ${user.first_name}, send any link 🥀`, {
        reply_markup: { inline_keyboard: [[{ text: "Discord 🔗", url: "https://discord.gg/j6WZkksV8" }]] }
    });
});

bot.onText(/\/rank/, async (msg) => {
    const userRes = await client.query("SELECT downloads, country FROM users WHERE user_id = $1", [msg.from.id]);
    const totalRes = await client.query("SELECT SUM(downloads) as total FROM users");
    const topCountry = await client.query("SELECT country, COUNT(*) as count FROM users WHERE country != 'Unknown' GROUP BY country ORDER BY count DESC LIMIT 1");
    
    const user = userRes.rows[0];
    let text = `📊 **Rank Stats**\n\n`;
    text += `📥 Total Downloads: ${totalRes.rows[0].total || 0}\n`;
    text += `🌍 Top Country: ${topCountry.rows[0]?.country || 'None'}\n`;
    text += `📅 Rank Started: Feb 2026\n`;
    text += `\n👤 **Your Stats:**\n📍 Your Country: ${user?.country || 'Unknown'}\n📥 Your Downloads: ${user?.downloads || 0}`;
    
    bot.sendMessage(msg.chat.id, text);
});

bot.onText(/\/lang/, async (msg) => {
    const res = await client.query("SELECT lang_fixed FROM users WHERE user_id = $1", [msg.from.id]);
    if (res.rows[0]?.lang_fixed) {
        return bot.sendMessage(msg.chat.id, "❌ Error: You have already selected your country. Choice is permanent!");
    }

    const countries = ["Somalia 🇸🇴", "USA 🇺🇸", "UK 🇬🇧", "Kenya 🇰🇪", "Ethiopia 🇪🇹", "Turkey 🇹🇷", "UAE 🇦🇪", "Egypt 🇪🇬", "Canada 🇨🇦", "Norway 🇳🇴", "Sweden 🇸🇪", "Germany 🇩🇪"];
    const keyboard = [];
    for (let i = 0; i < countries.length; i += 2) {
        keyboard.push([{ text: countries[i], callback_data: `ln_${countries[i]}` }, { text: countries[i+1], callback_data: `ln_${countries[i+1]}` }]);
    }
    bot.sendMessage(msg.chat.id, "Select Your Country (One-time Choice):", { reply_markup: { inline_keyboard: keyboard } });
});

// --- CORE DOWNLOADER ---

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const url = msg.text;

    if (!url || url.startsWith('/') || !url.startsWith('http')) {
        if (!url?.startsWith('/')) bot.sendMessage(chatId, "I only accept links. For help/problems contact the team 💹", { reply_markup: { inline_keyboard: [[{ text: "Team 💹", url: "https://t.me/Daddy_sadiqq" }]] } });
        return;
    }

    const wait = await bot.sendMessage(chatId, "✨");

    try {
        const output = `downloads/${Date.now()}.mp4`;
        const cmd = `yt-dlp -f "best" --no-check-certificate --user-agent "Mozilla/5.0" -o "${output}" "${url}"`;

        exec(cmd, async (err) => {
            if (err) return bot.editMessageText("It's Broken 💔", { chat_id: chatId, message_id: wait.message_id });

            await bot.sendVideo(chatId, output, {
                caption: "For You 🖤🥀 - @Fastdowloder1bot",
                reply_markup: { inline_keyboard: [[{ text: "Audio 🎙️", callback_data: `au_${url}` }], [{ text: "Community 🌋", url: "https://t.me/cummunutry1" }]] }
            });
            
            await client.query("UPDATE users SET downloads = downloads + 1 WHERE user_id = $1", [chatId]);
            bot.deleteMessage(chatId, wait.message_id);
            if (fs.existsSync(output)) fs.unlinkSync(output);
        });
    } catch (e) {
        bot.editMessageText("It's Broken 💔", { chat_id: chatId, message_id: wait.message_id });
    }
});

bot.on('callback_query', async (q) => {
    if (q.data.startsWith('ln_')) {
        const c = q.data.split('_')[1];
        await client.query("UPDATE users SET country = $1, lang_fixed = TRUE WHERE user_id = $2", [c, q.from.id]);
        bot.answerCallbackQuery(q.id, { text: "Saved permanently!" });
        bot.sendMessage(q.message.chat.id, `✅ Your country is set to: ${c}`);
    }
});
