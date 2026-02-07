const TelegramBot = require('node-telegram-bot-api');
const { exec } = require('child_process');
const { Client } = require('pg');
const fs = require('fs');
const axios = require('axios');

const token = process.env.BOT_TOKEN;
const ADMIN_ID = 8167075879; // <-- ID-GAAGA HALKAN GELI
const bot = new TelegramBot(token, { polling: { params: { drop_pending_updates: true } } });

// Database Connection
const client = new Client({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
});

async function initDB() {
    try {
        await client.connect();
        await client.query(`
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                downloads INT DEFAULT 0,
                country TEXT DEFAULT 'Unknown'
            );
        `);
        console.log("Database Connected & Ready ✅");
    } catch (err) { console.error('DB Error:', err.stack); }
}
initDB();

// --- HELPER FUNCTIONS ---
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function playAnimation(chatId) {
    const emojis = ["🥀", "💀", "🫦", "🎯", "🎁", "🔥"];
    let msg = await bot.sendMessage(chatId, emojis[0]);
    for (let i = 1; i < emojis.length; i++) {
        await sleep(800);
        await bot.editMessageText(emojis[i], { chat_id: chatId, message_id: msg.message_id }).catch(() => {});
    }
    return msg.message_id;
}

// --- SLASH COMMANDS ---

bot.onText(/\/start/, async (msg) => {
    const user = msg.from;
    await client.query("INSERT INTO users (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET username = $2", [user.id, user.first_name]);
    bot.sendMessage(msg.chat.id, `Hi ${user.first_name} Send any Link 🥀`, {
        reply_markup: { inline_keyboard: [[{ text: "Discord 🔗", url: "https://discord.gg/j6WZkksV8" }]] }
    });
});

bot.onText(/\/help/, (msg) => {
    bot.sendMessage(msg.chat.id, `Hi ${msg.from.first_name} Read This 👇\n\n/start - Start The Bot\n/lang - Set Up Your Country\n/rank - See Rank\n/help - Help Menu`, {
        reply_markup: { inline_keyboard: [[{ text: "Discord 🔗", url: "https://discord.gg/j6WZkksV8" }]] }
    });
});

bot.onText(/\/lang/, (msg) => {
    const countries = ["Somalia 🇸🇴", "USA 🇺🇸", "UK 🇬🇧", "Kenya 🇰🇪", "Ethiopia 🇪🇹", "Turkey 🇹🇷", "UAE 🇦🇪", "Egypt 🇪🇬", "Canada 🇨🇦", "Norway 🇳🇴", "Sweden 🇸🇪", "Germany 🇩🇪", "France 🇫🇷", "India 🇮🇳", "China 🇨🇳", "Brazil 🇧🇷", "Qatar 🇶🇦", "S.Arabia 🇸🇦", "Djibouti 🇩🇯", "Italy 🇮🇹", "Spain 🇪🇸", "Russia 🇷🇺", "Japan 🇯🇵", "S.Korea 🇰🇷", "Australia 🇦🇺", "Nigeria 🇳🇬", "S.Africa 🇿🇦", "Uganda 🇺🇬", "Tanzania 🇹🇿", "Sudan 🇸🇩", "Pakistan 🇵🇰", "Mexico 🇲🇽", "Finland 🇫🇮", "Denmark 🇩🇰", "Oman 🇴🇲", "Kuwait 🇰🇼", "Yemen 🇾🇪", "Libya 🇱🇾", "Morocco 🇲🇦", "Netherlands 🇳🇱"];
    const keyboard = [];
    for (let i = 0; i < countries.length; i += 2) {
        keyboard.push([{ text: countries[i], callback_data: `ln_${countries[i]}` }, { text: countries[i+1], callback_data: `ln_${countries[i+1]}` }]);
    }
    bot.sendMessage(msg.chat.id, "Choice - Country / From:", { reply_markup: { inline_keyboard: keyboard } });
});

bot.onText(/\/rank/, async (msg) => {
    const totalRes = await client.query("SELECT SUM(downloads) as total FROM users");
    const topCountries = await client.query("SELECT country, COUNT(*) as count FROM users WHERE country != 'Unknown' GROUP BY country ORDER BY count DESC LIMIT 10");
    
    let text = `📊 **Rank Stats**\n\nTotal Uploaded Video: ${totalRes.rows[0].total || 0}\n\nTop 10 Countries:\n`;
    topCountries.rows.forEach((row, i) => { text += `${i+1}. ${row.country} (${row.count} users)\n`; });
    text += `\nXiliga la bilaabay Rankiga: Feb 2026`;
    
    bot.sendMessage(msg.chat.id, text, { reply_markup: { inline_keyboard: [[{ text: "Discord 🔗", url: "https://discord.gg/j6WZkksV8" }]] } });
});

// --- ADMIN COMMANDS ---

bot.onText(/\/admin/, async (msg) => {
    if (msg.from.id !== ADMIN_ID) return;
    const res = await client.query("SELECT COUNT(*) FROM users");
    bot.sendMessage(msg.chat.id, `👑 **Admin Panel**\n\nTotal Users: ${res.rows[0].count}\n/broadcast [text] - Send message to all\n/users - Show last 50 IDs`);
});

bot.onText(/\/broadcast (.+)/, async (msg, match) => {
    if (msg.from.id !== ADMIN_ID) return;
    const res = await client.query("SELECT user_id FROM users");
    res.rows.forEach(u => bot.sendMessage(u.user_id, match[1]).catch(() => {}));
    bot.sendMessage(msg.chat.id, "✅ Broadcast Sent!");
});

// --- MAIN DOWNLOADER ---

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const url = msg.text;

    if (!url || url.startsWith('/')) return;
    if (!url.startsWith('http')) {
        return bot.sendMessage(chatId, "A accepted Only Link Any Help /Problem Content team 💹", {
            reply_markup: { inline_keyboard: [[{ text: "team 💹", url: "https://t.me/Daddy_sadiqq" }]] }
        });
    }

    const animId = await playAnimation(chatId);

    try {
        // TikTok Check (Images & Video)
        const apiRes = await axios.get(`https://www.tikwm.com/api/?url=${url}`);
        const data = apiRes.data.data;

        if (data && data.images) {
            const media = data.images.slice(0, 10).map(img => ({ type: 'photo', media: img }));
            await bot.sendMediaGroup(chatId, media, { caption: "For You 🖤🥀 - @Fastdowloder1bot" });
            if (data.music) await bot.sendAudio(chatId, data.music, { caption: "Music 🎵" });
            bot.deleteMessage(chatId, animId);
        } else {
            const output = `downloads/${Date.now()}.mp4`;
            exec(`yt-dlp -f "best" -o "${output}" "${url}"`, async (err) => {
                if (err) return bot.editMessageText("Ist Brok 💔", { chat_id: chatId, message_id: animId });
                
                await bot.sendVideo(chatId, output, {
                    caption: "For You 🖤🥀 - @Fastdowloder1bot",
                    reply_markup: { inline_keyboard: [[{ text: "Audio 🎙️", callback_data: `au_${url}` }], [{ text: "Community 🌋", url: "https://t.me/cummunutry1" }]] }
                });
                bot.deleteMessage(chatId, animId);
                if (fs.existsSync(output)) fs.unlinkSync(output);
            });
        }
        await client.query("UPDATE users SET downloads = downloads + 1 WHERE user_id = $1", [chatId]);
    } catch (e) { bot.editMessageText("Ist Brok 💔", { chat_id: chatId, message_id: animId }); }
});

// --- CALLBACKS ---

bot.on('callback_query', async (query) => {
    const chatId = query.message.chat.id;
    const data = query.data;

    if (data.startsWith('ln_')) {
        const country = data.split('_')[1];
        await client.query("UPDATE users SET country = $1 WHERE user_id = $2", [country, query.from.id]);
        bot.answerCallbackQuery(query.id, { text: "Saved ✅" });
        bot.sendMessage(chatId, `Wadankaaga: ${country} ✅`);
    } else if (data.startsWith('au_')) {
        const url = data.split('_')[1];
        const wait = await bot.sendMessage(chatId, "🎙️ Extracting Audio...");
        const out = `downloads/${Date.now()}.mp3`;
        exec(`yt-dlp -x --audio-format mp3 -o "${out}" "${url}"`, async (err) => {
            if (err) return bot.sendMessage(chatId, "Ist Brok 💔");
            await bot.sendAudio(chatId, out, { caption: "For You 🖤🥀 - @Fastdowloder1bot" });
            bot.deleteMessage(chatId, wait.message_id);
            if (fs.existsSync(out)) fs.unlinkSync(out);
        });
    }
});
