import os
from telegram import Update, InputFile
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from fpdf import FPDF

BOT_TOKEN = os.getenv("BOT_TOKEN")

user_data = {}

os.makedirs("data/drawings", exist_ok=True)
os.makedirs("data/pdfs", exist_ok=True)

# Animated welcome GIF
WELCOME_GIF = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExajFxZjJ0aGRvaGhlcjd1bzdvbDA3cW85NnJ0czVjNXYzdnZ4b3Y3NyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/t5z9rba4LdqU8/giphy.gif"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_animation(animation=WELCOME_GIF)
    await update.message.reply_text(
        "👋 *Welcome to NoteX Bot!*\n\n"
        "📚 Your smart note-taking assistant.\n\n"
        "*Commands:*\n"
        "📝 `/note <text>` – Save a note\n"
        "✅ `/todo <task>` – Add a to-do\n"
        "📋 `/viewnotes` – View notes\n"
        "📌 `/viewtodo` – View to-do list\n"
        "🎨 *Send a sketch/drawing* – Save as note\n"
        "📄 `/pdf` – Export notes/drawings to PDF\n\n"
        "✨ Enjoy productivity with fun!",
        parse_mode=ParseMode.MARKDOWN
    )

async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text("❌ Please write your note: `/note Do homework`", parse_mode=ParseMode.MARKDOWN)
        return
    user_data.setdefault(user_id, {"notes": [], "todos": [], "drawings": []})
    user_data[user_id]["notes"].append(text)
    await update.message.reply_text("✅ *Note saved!*", parse_mode=ParseMode.MARKDOWN)

async def view_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    notes = user_data.get(user_id, {}).get("notes", [])
    if not notes:
        await update.message.reply_text("📝 No notes found.")
        return
    msg = "\n".join([f"*{i+1}.* {note}" for i, note in enumerate(notes)])
    await update.message.reply_text("📚 *Your Notes:*\n\n" + msg, parse_mode=ParseMode.MARKDOWN)

async def save_todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    task = ' '.join(context.args)
    if not task:
        await update.message.reply_text("❌ Please add a task: `/todo Buy milk`", parse_mode=ParseMode.MARKDOWN)
        return
    user_data.setdefault(user_id, {"notes": [], "todos": [], "drawings": []})
    user_data[user_id]["todos"].append({"task": task, "done": False})
    await update.message.reply_text("✅ *Task added!*", parse_mode=ParseMode.MARKDOWN)

async def view_todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    todos = user_data.get(user_id, {}).get("todos", [])
    if not todos:
        await update.message.reply_text("📋 Your to-do list is empty.")
        return
    msg = "\n".join([f"[{'✅' if t['done'] else '❌'}] *{i+1}.* {t['task']}" for i, t in enumerate(todos)])
    await update.message.reply_text("🧾 *Your To-Do List:*\n" + msg, parse_mode=ParseMode.MARKDOWN)

async def save_drawing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    file = await update.message.photo[-1].get_file()
    filename = f"data/drawings/{user_id}_{len(user_data.get(user_id, {}).get('drawings', []))}.jpg"
    await file.download_to_drive(filename)
    user_data.setdefault(user_id, {"notes": [], "todos": [], "drawings": []})
    user_data[user_id]["drawings"].append(filename)
    await update.message.reply_text("🎨 *Drawing saved!*", parse_mode=ParseMode.MARKDOWN)

async def export_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = user_data.get(user_id)
    if not data:
        await update.message.reply_text("❌ You have no notes to export.")
        return

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    if data["notes"]:
        pdf.cell(200, 10, "Your Notes", ln=True, align='C')
        for note in data["notes"]:
            pdf.multi_cell(0, 10, note)
        pdf.ln()

    if data["todos"]:
        pdf.cell(200, 10, "To-Do List", ln=True, align='C')
        for todo in data["todos"]:
            status = "DONE" if todo["done"] else "PENDING"
            pdf.multi_cell(0, 10, f"[{status}] {todo['task']}")
        pdf.ln()

    for img_path in data["drawings"]:
        pdf.add_page()
        try:
            pdf.image(img_path, x=10, y=20, w=180)
        except:
            continue

    output_file = f"data/pdfs/{user_id}_notes.pdf"
    pdf.output(output_file)
    await update.message.reply_document(document=InputFile(output_file))

# Main bot setup
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("note", save_note))
app.add_handler(CommandHandler("viewnotes", view_notes))
app.add_handler(CommandHandler("todo", save_todo))
app.add_handler(CommandHandler("viewtodo", view_todo))
app.add_handler(CommandHandler("pdf", export_pdf))
app.add_handler(MessageHandler(filters.PHOTO, save_drawing))

print("🤖 Bot is running...")
app.run_polling()
