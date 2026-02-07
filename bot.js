const TelegramBot = require('node-telegram-bot-api');
const { exec } = require('child_process');
const { Client } = require('pg');
const fs = require('fs');
const axios = require('axios');

const token = process.env.BOT_TOKEN;
const bot = new TelegramBot(token, { polling: { params: { drop_pending_updates: true } } });

const client = new Client({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
});

async function initDB() {
    try {
        await client.connect();
        // Abuur table-ka haddii uusan jirin
        await client.query(`
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                downloads INT DEFAULT 0,
                country TEXT DEFAULT 'Unknown'
            );
        `);
        // Hubi in column-ka 'downloads' uu jiro, haddii kale ku dar
        await client.query(`
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='downloads') THEN
                    ALTER TABLE users ADD COLUMN downloads INT DEFAULT 0;
                END IF;
            END $$;
        `);
        console.log("Database-kii waa diyaar! ✅");
    } catch (err) {
        console.error('Database Error:', err.stack);
    }
}

initDB();

// --- COMMANDS ---
bot.onText(/\/start/, async (msg) => {
    await client.query("INSERT INTO users (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING", [msg.from.id, msg.from.first_name]);
    bot.sendMessage(msg.chat.id, `Ku soo dhawaaw ${msg.from.first_name}! 🤖\nI soo sii Link kasta (IG, TikTok, FB, YT).\n\n/lang - Wadanka\n/rank - Darajadaada`);
});

bot.onText(/\/lang/, (msg) => {
    const countries = ["Somalia 🇸🇴", "USA 🇺🇸", "UK 🇬🇧", "Kenya 🇰🇪", "Ethiopia 🇪🇹", "Turkey 🇹🇷", "UAE 🇦🇪", "Egypt 🇪🇬"];
    const keyboard = countries.map(c => [{ text: c, callback_data: `ln_${c}` }]);
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

    const wait = await bot.sendMessage(chatId, "⚡ Processing...");

    try {
        // TIKTOK IMAGES
        if (url.includes("tiktok.com")) {
            const apiRes = await axios.get(`https://www.tikwm.com/api/?url=${url}`);
            const data = apiRes.data.data;
            if (data && data.images) {
                const media = data.images.slice(0, 10).map(img => ({ type: 'photo', media: img }));
                await bot.sendMediaGroup(chatId, media, { caption: "TikTok Slideshow ✅" });
                await client.query("UPDATE users SET downloads = downloads + 1 WHERE user_id = $1", [chatId]);
                return bot.deleteMessage(chatId, wait.message_id);
            }
        }

        // UNIVERSAL VIDEO
        const output = `downloads/${Date.now()}.mp4`;
        const cmd = `yt-dlp -f "best" --no-check-certificate -o "${output}" "${url}"`;

        exec(cmd, async (error) => {
            if (error) return bot.editMessageText("❌ Link Error!", { chat_id: chatId, message_id: wait.message_id });
            await bot.sendVideo(chatId, output, { caption: "Done ✅ - @Fastdowloder1bot" });
            await client.query("UPDATE users SET downloads = downloads + 1 WHERE user_id = $1", [chatId]);
            bot.deleteMessage(chatId, wait.message_id);
            if (fs.existsSync(output)) fs.unlinkSync(output);
        });
    } catch (e) {
        bot.editMessageText("❌ Error!", { chat_id: chatId, message_id: wait.message_id });
    }
});

bot.on('callback_query', async (query) => {
    if (query.data.startsWith('ln_')) {
        const country = query.data.split('_')[1];
        await client.query("UPDATE users SET country = $1 WHERE user_id = $2", [country, query.from.id]);
        bot.answerCallbackQuery(query.id, { text: `Wadankaaga: ${country}` });
    }
});
