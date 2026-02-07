const TelegramBot = require('node-telegram-bot-api');
const { exec } = require('child_process');
const os = require('os');

// Token-kaaga halkan geli
const token = process.env.BOT_TOKEN;
const bot = new TelegramBot(token, { polling: { params: { drop_pending_updates: true } } });

console.log("Bot-kii waa kacay... Platform kasta waa diyaar!");

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const url = msg.text;

    if (!url.startsWith('http')) return;

    const wait = await bot.sendMessage(chatId, "⚡ Natiijada sug... dhowr ilbiriqsi.");

    // Universal Command (Bash/yt-dlp) - Wuxuu dagsanayaa IG, FB, YT, TikTok
    const output = `downloads/${Date.now()}.mp4`;
    const cmd = `yt-dlp -f "best" --headers "User-Agent:Mozilla/5.0" -o "${output}" "${url}"`;

    exec(cmd, (error, stdout, stderr) => {
        if (error) {
            bot.editMessageText("❌ Link-gan ma shaqaynayo!", { chat_id: chatId, message_id: wait.message_id });
            return;
        }

        bot.sendVideo(chatId, output, { caption: "Done ✅ - @Fastdowloder1bot" }).then(() => {
            bot.deleteMessage(chatId, wait.message_id);
            // Bash command si loo tirtiro faylka markuu dhameeyo
            exec(`rm ${output}`);
        });
    });
});

// /lang and /rank commands halkan ku dar...
