import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import AsyncOpenAI

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if not TELEGRAM_TOKEN or not DEEPSEEK_API_KEY:
    raise ValueError("请设置环境变量 TELEGRAM_TOKEN 和 DEEPSEEK_API_KEY")

SYSTEM_PROMPT = "你是一个乐于助人的助手。"
if os.path.exists("SKILL.md"):
    with open("SKILL.md", "r", encoding="utf-8") as f:
        content = f.read()
        if "---" in content:
            SYSTEM_PROMPT = content.split("---", 1)[1].strip()
        else:
            SYSTEM_PROMPT = content
    logging.info("已加载 SKILL.md")
else:
    logging.warning("未找到 SKILL.md，使用默认提示词")

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好，我是 Serenity 风格的助手。")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    if 'history' not in context.chat_data:
        context.chat_data['history'] = [{"role": "system", "content": SYSTEM_PROMPT}]
    context.chat_data['history'].append({"role": "user", "content": user_msg})

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=context.chat_data['history'],
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        context.chat_data['history'].append({"role": "assistant", "content": reply})
        if len(context.chat_data['history']) > 20:
            context.chat_data['history'] = [context.chat_data['history'][0]] + context.chat_data['history'][-19:]
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("抱歉，出错了，请稍后再试。")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    logging.info("Bot 启动中...")
    app.run_polling()

if __name__ == "__main__":
    main()
