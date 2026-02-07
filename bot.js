const TelegramBot = require('node-telegram-bot-api');
const { exec } = require('child_process');
const { Client } = require('pg');
const axios = require('axios');
const fs = require('fs');

const token = process.env.BOT_TOKEN;
const bot = new TelegramBot(token, { polling: { params: { drop_pending_updates: true } } });

const client = new Client({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
});

// Database Initialization with Column Fix
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
        // Force add column if missing
        await client.query(`
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='downloads') THEN
                    ALTER TABLE users ADD COLUMN downloads INT DEFAULT 0;
                END IF;
            END $$;
        `);
        console.log("Database Connected & Repaired! ✅");
    } catch (err) {
        console.error('DB Error:', err.stack);
    }
}
initDB();

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const url = msg.text;

    if (!url || !url.startsWith('http')) return;

    const wait = await bot.sendMessage(chatId, "⚡ Processing TikTok Link...");

    try {
        // TikTok API for Slideshows and Videos
        const apiRes = await axios.get(`https://www.tikwm.com/api/?url=${url}`);
        const data = apiRes.data.data;

        if (data && data.images) {
            const media = data.images.slice(0, 10).map(img => ({ type: 'photo', media: img }));
            await bot.sendMediaGroup(chatId, media, { caption: "Done ✅" });
        } else if (data && data.play) {
            await bot.sendVideo(chatId, data.play, { caption: "Done ✅" });
        } else {
            // Fallback to yt-dlp
            const output = `downloads/${Date.now()}.mp4`;
            exec(`yt-dlp -f "best" -o "${output}" "${url}"`, async (err) => {
                if (err) return bot.editMessageText("❌ Error: Link-gan ma shaqaynayo.", { chat_id: chatId, message_id: wait.message_id });
                await bot.sendVideo(chatId, output, { caption: "Done ✅" });
                if (fs.existsSync(output)) fs.unlinkSync(output);
            });
        }

        // Update User Stats
        await client.query("UPDATE users SET downloads = downloads + 1 WHERE user_id = $1", [chatId]);
        bot.deleteMessage(chatId, wait.message_id);

    } catch (e) {
        bot.editMessageText("❌ Error occurred!", { chat_id: chatId, message_id: wait.message_id });
    }
});
