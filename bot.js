const TelegramBot = require('node-telegram-bot-api');
const { exec } = require('child_process');
const fs = require('fs');

const token = process.env.BOT_TOKEN;
const bot = new TelegramBot(token, { polling: { params: { drop_pending_updates: true } } });

// Database la'aan hadda si aan natiijo degdeg ah u helno (Tijaabo)
console.log("Bot-kii wuu shaqaynayaa... Platform walba waa diyaar! 🚀");

// 1. START COMMAND
bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id, `Hi ${msg.from.first_name}! Send me ANY link (IG, FB, YT, TikTok). 🔗\nUse /lang to select country.`);
});

// 2. LANG COMMAND (40 Waddan)
bot.onText(/\/lang/, (msg) => {
    const countries = [
        "Somalia 🇸🇴", "USA 🇺🇸", "UK 🇬🇧", "Kenya 🇰🇪", "Ethiopia 🇪🇹", "Turkey 🇹🇷", "UAE 🇦🇪", "Egypt 🇪🇬",
        "Canada 🇨🇦", "Norway 🇳🇴", "Sweden 🇸🇪", "Germany 🇩🇪", "France 🇫🇷", "India 🇮🇳", "China 🇨🇳", "Brazil 🇧🇷"
    ]; // Halkan 40-ka waa ku dari kartaa
    
    const opts = {
        reply_markup: {
            inline_keyboard: countries.reduce((acc, curr, i) => {
                if (i % 2 === 0) acc.push([{ text: curr, callback_data: `ln_${curr}` }]);
                else acc[acc.length - 1].push({ text: curr, callback_data: `ln_${curr}` });
                return acc;
            }, [])
        }
    };
    bot.sendMessage(msg.chat.id, "Dooro Wadankaaga:", opts);
});

// 3. UNIVERSAL DOWNLOADER ENGINE
bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const url = msg.text;

    if (!url || !url.startsWith('http')) return;
    if (url.startsWith('/')) return; // Iska dhaaf commands-ka

    const wait = await bot.sendMessage(chatId, "⚡ Processing... please wait.");

    const output = `downloads/${Date.now()}.mp4`;
    // yt-dlp wuxuu dagsanayaa wax kasta (Video + Audio)
    const cmd = `yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" --no-check-certificate -o "${output}" "${url}"`;

    exec(cmd, (error, stdout, stderr) => {
        if (error) {
            return bot.editMessageText("❌ Error: Link-gan lama dagsan karo!", { chat_id: chatId, message_id: wait.message_id });
        }

        bot.sendVideo(chatId, output, { caption: "Done ✅ - @Fastdowloder1bot" }).then(() => {
            bot.deleteMessage(chatId, wait.message_id);
            if (fs.existsSync(output)) fs.unlinkSync(output); // Tirtir faylka
        }).catch(err => {
            bot.sendMessage(chatId, "❌ Telegram baa diiday inuu diro Video-gan (aad buu u weyn yahay).");
        });
    });
});

bot.on('callback_query', (query) => {
    if (query.data.startsWith('ln_')) {
        bot.answerCallbackQuery(query.id, { text: `Wadankaaga waa: ${query.data.split('_')[1]}` });
        bot.sendMessage(query.message.chat.id, "✅ Mahadsanid!");
    }
});
