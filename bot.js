const TelegramBot = require('node-telegram-bot-api');
const { exec } = require('child_process');
const { Client } = require('pg');
const fs = require('fs');
const axios = require('axios');

const token = process.env.BOT_TOKEN;
const bot = new TelegramBot(token, { polling: { params: { drop_pending_updates: true } } });

// Database Connection
const client = new Client({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
});
client.connect().catch(err => console.error('Database connection error', err.stack));

// Initialize DB
client.query(`
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        username TEXT,
        downloads INT DEFAULT 0,
        country TEXT DEFAULT 'Unknown'
    );
`);

console.log("Bot-kii Universal-ka ahaa waa kacay! 🚀");

// --- COMMANDS ---

bot.onText(/\/start/, async (msg) => {
    const user = msg.from;
    await client.query("INSERT INTO users (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING", [user.id, user.first_name]);
    bot.sendMessage(msg.chat.id, `Ku soo dhawaaw ${user.first_name}! 🤖\n\nI soo sii Link kasta (Video ama Sawirro).\n\nCommands:\n/lang - Dooro wadanka\n/rank - Fiiri darajadaada\n/help - Caawinaad`);
});

bot.onText(/\/lang/, (msg) => {
    const countries = ["Somalia 🇸🇴", "USA 🇺🇸", "UK 🇬🇧", "Kenya 🇰🇪", "Ethiopia 🇪🇹", "Turkey 🇹🇷", "UAE 🇦🇪", "Egypt 🇪🇬", "Canada 🇨🇦", "Norway 🇳🇴", "Sweden 🇸🇪", "Germany 🇩🇪", "France 🇫🇷", "India 🇮🇳", "China 🇨🇳", "Brazil 🇧🇷"];
    const keyboard = [];
    for (let i = 0; i < countries.length; i += 2) {
        keyboard.push([{ text: countries[i], callback_data: `ln_${countries[i]}` }, { text: countries[i+1], callback_data: `ln_${countries[i+1]}` }]);
    }
    bot.sendMessage(msg.chat.id, "Dooro Wadankaaga:", { reply_markup: { inline_keyboard: keyboard } });
});

bot.onText(/\/rank/, async (msg) => {
    const res = await client.query("SELECT downloads, country FROM users WHERE user_id = $1", [msg.from.id]);
    const user = res.rows[0];
    bot.sendMessage(msg.chat.id, `📊 **Xogtaada:**\n\n📥 Downloads: ${user ? user.downloads : 0}\n📍 Wadanka: ${user ? user.country : 'Unknown'}`);
});

// --- DOWNLOADER CORE ---

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const url = msg.text;

    if (!url || !url.startsWith('http') || url.startsWith('/')) return;

    const wait = await bot.sendMessage(chatId, "⚡ Processing... please wait.");

    try {
        // 1. TIKTOK IMAGES CHECK
        if (url.includes("tiktok.com")) {
            const apiRes = await axios.get(`https://www.tikwm.com/api/?url=${url}`);
            const data = apiRes.data.data;
            if (data && data.images) {
                const media = data.images.slice(0, 10).map(img => ({ type: 'photo', media: img }));
                await bot.sendMediaGroup(chatId, media, { caption: "TikTok Slideshow ✅ - @Fastdowloder1bot" });
                await client.query("UPDATE users SET downloads = downloads + 1 WHERE user_id = $1", [chatId]);
                return bot.deleteMessage(chatId, wait.message_id);
            }
        }

        // 2. UNIVERSAL VIDEO (yt-dlp)
        const output = `downloads/${Date.now()}.mp4`;
        const cmd = `yt-dlp -f "best" --no-check-certificate -o "${output}" "${url}"`;

        exec(cmd, async (error) => {
            if (error) return bot.editMessageText("❌ Link Error!", { chat_id: chatId, message_id: wait.message_id });

            await bot.sendVideo(chatId, output, {
                caption: "Done ✅ - @Fastdowloder1bot",
                reply_markup: { inline_keyboard: [[{ text: "Audio 🎙️", callback_data: `au_${url}` }]] }
            });

            await client.query("UPDATE users SET downloads = downloads + 1 WHERE user_id = $1", [chatId]);
            bot.deleteMessage(chatId, wait.message_id);
            if (fs.existsSync(output)) fs.unlinkSync(output);
        });
    } catch (e) {
        bot.editMessageText("❌ Error processing link.", { chat_id: chatId, message_id: wait.message_id });
    }
});

// --- CALLBACK HANDLER (Audio & Lang) ---

bot.on('callback_query', async (query) => {
    const chatId = query.message.chat.id;
    const url = query.data.split('_')[1];

    if (query.data.startsWith('au_')) {
        const audioWait = await bot.sendMessage(chatId, "🎙️ Extracting audio...");
        const output = `downloads/${Date.now()}.mp3`;
        const cmd = `yt-dlp -x --audio-format mp3 -o "${output}" "${url}"`;

        exec(cmd, async (error) => {
            if (error) return bot.sendMessage(chatId, "❌ Audio error.");
            await bot.sendAudio(chatId, output);
            bot.deleteMessage(chatId, audioWait.message_id);
            if (fs.existsSync(output)) fs.unlinkSync(output);
        });
    } else if (query.data.startsWith('ln_')) {
        const country = query.data.split('_')[1];
        await client.query("UPDATE users SET country = $1 WHERE user_id = $2", [country, query.from.id]);
        bot.answerCallbackQuery(query.id, { text: `Wadankaaga: ${country}` });
        bot.sendMessage(chatId, `✅ Wadankaaga waxaa loo qoray: ${country}`);
    }
});
