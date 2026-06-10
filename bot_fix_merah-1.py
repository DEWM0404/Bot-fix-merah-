"""
Bot Telegram - Fix Merah WhatsApp
Fitur:
- User kirim nomor langsung, bot langsung proses
- Bisa kirim banyak nomor sekaligus (antrian otomatis)
- 10 template email rolling/random
- Multi Gmail rotation
- Cek inbox Gmail tiap 1.5 menit
- Notif Telegram kalau WA sudah balas
- Setting Gmail langsung dari Telegram
"""

import logging
import smtplib
import imaplib
import email as email_lib
import json
import os
import random
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ─── KONFIGURASI ──────────────────────────────────────────────
BOT_TOKEN = "8813296506:AAGVaakE0fnltghT8oo15FqVmwZYXPJYabo"
ADMIN_IDS = [8235197481]  # ganti dengan Telegram ID kamu
GMAIL_FILE = "gmail_accounts.json"
CEK_INBOX_INTERVAL = 90

WA_SUPPORT_EMAILS = [
    "support@whatsapp.com",
    "support@support.whatsapp.com",
    "android_web@support.whatsapp.com",
    "iphone_web@support.whatsapp.com",
    "smb_web@support.whatsapp.com",
]

# ─── 10 TEMPLATE EMAIL APPEAL ─────────────────────────────────
TEMPLATES = [
    # Template 1
    """Hello WhatsApp Support Team,

I am writing to you because I have been experiencing a frustrating issue with my WhatsApp account for the past few days. Every time I attempt to log in and verify my number, I am presented with the message: "Login not available right now. For security reasons, we can't log you in at the moment."

I want to be completely honest with you — I have no idea why this is happening. I have been using this number for a long time and I have never done anything that would go against WhatsApp's Terms of Service. I only use the official WhatsApp application and I have never shared my account with anyone else.

I have already tried several troubleshooting steps on my own, including reinstalling the app and restarting my phone, but unfortunately none of these have resolved the issue. At this point I am not sure what else I can do on my end.

WhatsApp Number: {nomor}

I am kindly requesting your team to look into this matter and help me restore access to my account. I truly depend on WhatsApp to stay connected with my family and friends, and being locked out has been really difficult. I am more than happy to provide any additional information or go through any verification process you may require.

Thank you so much for taking the time to read this. I really hope to hear back from you soon.""",

    # Template 2
    """Dear WhatsApp Support Team,

I hope this message finds you well. I am reaching out today because I have been locked out of my WhatsApp account and I genuinely do not understand why. Whenever I try to verify my number, the app shows me this message: "Login not available right now. For security reasons, we can't log you in at the moment."

This has been going on for a few days now and it has been quite stressful. I use WhatsApp every single day to communicate with my family, close friends, and work contacts. Losing access to my account has disrupted a lot of my daily communication and I am really hoping your team can help me resolve this quickly.

I can confirm that I am the rightful owner of this number and I have always used WhatsApp responsibly. I have never used any unofficial version of the app or done anything that would breach your community guidelines.

WhatsApp Number: {nomor}

I sincerely request your team to review my account and remove the restriction. I am fully prepared to cooperate with any verification steps you may need. Thank you very much for your help and I look forward to your response.""",

    # Template 3
    """Hello WhatsApp Support,

I am currently experiencing an issue while trying to verify my WhatsApp number. During the login process, the following message appears: "Login not available right now. For security reasons, we can't log you in at the moment."

I believe this number belongs to me and has been used normally without any violation of WhatsApp's Terms of Service. I do not recall doing anything unusual with my account prior to this issue occurring. Everything was working perfectly fine until a few days ago when I suddenly found myself unable to log in.

WhatsApp Number: {nomor}

I kindly request that the WhatsApp team review this restriction so I can regain access to my account. I am willing to provide any additional information if needed to verify ownership of this number. Thank you for your time and I look forward to hearing from you.""",

    # Template 4
    """Dear WhatsApp Support Team,

I hope you are doing well. I am writing to report that I have been unable to access my WhatsApp account due to the following error: "Login not available right now. For security reasons, we can't log you in at the moment."

I have not engaged in any activity that would violate your Terms of Service. This account is extremely important to me as I use it to stay in touch with family members who live in different cities. Being suddenly cut off from them has been very difficult and I am urgently requesting your assistance.

WhatsApp Number: {nomor}

I have tried uninstalling and reinstalling the application multiple times but the same error keeps appearing. I really hope your team can look into this and help restore my access as soon as possible. Please let me know if there is any additional information you require from me.

Thank you so much for your understanding and assistance.""",

    # Template 5
    """Hello WhatsApp Team,

I am contacting you regarding a serious issue I have been facing with my WhatsApp account. For several days now, I have been completely unable to log into my account. Each time I try to verify my number the following message is displayed: "Login not available right now. For security reasons, we can't log you in at the moment."

I am genuinely confused as to why this is happening because I have always used WhatsApp strictly within the boundaries of your Terms of Service. I have never used any modified application, never engaged in spamming or bulk messaging, and have always maintained my account responsibly.

WhatsApp Number: {nomor}

I am respectfully asking your support team to investigate this issue and restore access to my account. I depend on WhatsApp for important personal and professional communication and the disruption caused by this restriction has been significant. I am happy to assist in any way and provide whatever information is needed.

Thank you for your time and I sincerely hope to have this resolved soon.""",

    # Template 6
    """Dear WhatsApp Support,

I hope this email finds you in good health. I am reaching out to request your urgent assistance with an issue affecting my WhatsApp account. When I attempt to log in and verify my number, I consistently receive the error: "Login not available right now. For security reasons, we can't log you in at the moment."

This situation has been ongoing for the past few days and I am at a complete loss as to what might have caused it. I have reviewed WhatsApp's Terms of Service thoroughly and I am confident that I have not violated any of the guidelines. I exclusively use the official WhatsApp application and my usage has always been limited to normal personal communication.

WhatsApp Number: {nomor}

I would be extremely grateful if your team could review my account and lift whatever restriction has been placed on it. I understand that your team works hard to keep the platform safe and I fully support those efforts. However, I genuinely believe that this restriction may have been applied to my account in error.

Thank you very much for taking the time to consider my request. I look forward to your response.""",

    # Template 7
    """Hello WhatsApp Support Team,

I am writing to bring to your attention an issue I have been experiencing with my WhatsApp account. Over the past few days I have been unable to complete the login process as I keep encountering the following message: "Login not available right now. For security reasons, we can't log you in at the moment."

I want to assure your team that I have always been a responsible user of WhatsApp. I have never attempted to use the platform in any way that would be considered a violation of your Terms of Service. My usage has always been limited to staying in touch with the people I care about.

WhatsApp Number: {nomor}

After trying numerous solutions on my own without any success, I am turning to your support team for help. I am kindly requesting a thorough review of my account and the removal of any restrictions that may be preventing me from logging in. I am fully available to provide any supporting information or undergo any verification process your team deems necessary.

Thank you for your patience and assistance. I genuinely appreciate the work your support team does.""",

    # Template 8
    """Dear WhatsApp Support,

I am reaching out today because I have been experiencing a very distressing issue with my WhatsApp account. For the last several days, every attempt I make to log in results in the same error message: "Login not available right now. For security reasons, we can't log you in at the moment."

I have gone over my recent activity and I can say with complete confidence that I have done nothing to violate WhatsApp's Terms of Service. I have always used the official application, never participated in any form of spam or unauthorized messaging, and have kept my account secure at all times.

WhatsApp Number: {nomor}

I am humbly requesting that your support team review my account and restore my access. WhatsApp is my primary means of communication with my loved ones and being unable to access it has been very challenging. I am committed to cooperating fully with your team and providing any information that would help resolve this matter quickly.

Thank you so much for reading my message. I truly hope to hear from you soon.""",

    # Template 9
    """Hello WhatsApp Support Team,

I hope you are well. I am writing because I have been locked out of my WhatsApp account for several days now and despite my best efforts I have been unable to resolve the issue on my own. The error message I keep seeing is: "Login not available right now. For security reasons, we can't log you in at the moment."

To the best of my knowledge I have done absolutely nothing to warrant this restriction. I am a regular everyday user of WhatsApp who uses the platform solely to communicate with family and friends. I have always downloaded and used only the official version of the application from the official app store.

WhatsApp Number: {nomor}

I am sincerely asking your team to take a closer look at my account and help me regain access. This account holds years of important conversations and memories and losing it would be truly devastating. I am prepared to do whatever is necessary to verify my identity and prove ownership of this number.

Thank you very much for your time and consideration. I look forward to a positive response.""",

    # Template 10
    """Dear WhatsApp Support Team,

I am contacting you because I have been experiencing a persistent login issue with my WhatsApp account that I have been unable to resolve on my own. Every time I try to verify my number, I receive the message: "Login not available right now. For security reasons, we can't log you in at the moment."

I have been a loyal WhatsApp user for many years and I take the platform's Terms of Service very seriously. I have never used any third party applications, never engaged in any form of mass messaging, and have always used my account for legitimate personal communication only. I am genuinely at a loss as to why this restriction has been placed on my account.

WhatsApp Number: {nomor}

I am respectfully requesting that your support team investigate this issue and restore access to my account as soon as possible. I rely on WhatsApp as my main communication tool and the impact of this restriction on my daily life has been considerable. I am fully willing to provide any additional documentation or information that your team may require to process this request.

Thank you so much for your time and I sincerely hope this matter can be resolved quickly.""",
]
# ──────────────────────────────────────────────────────────────

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

TANYA_KONFIRM = range(1)
TAMBAH_EMAIL, TAMBAH_PASSWORD = range(1, 3)

gmail_index = 0
active_users = set()
notified_emails = set()
template_index = 0


# ─── UTILS ────────────────────────────────────────────────────

def load_gmail():
    if os.path.exists(GMAIL_FILE):
        with open(GMAIL_FILE, "r") as f:
            return json.load(f)
    return []


def save_gmail(accounts):
    with open(GMAIL_FILE, "w") as f:
        json.dump(accounts, f, indent=2)


def get_next_gmail():
    global gmail_index
    accounts = load_gmail()
    if not accounts:
        return None
    account = accounts[gmail_index % len(accounts)]
    gmail_index += 1
    return account


def get_next_template(nomor):
    global template_index
    tpl = TEMPLATES[template_index % len(TEMPLATES)]
    template_index += 1
    return tpl.replace("{nomor}", nomor)


def is_admin(user_id):
    return user_id in ADMIN_IDS


def test_gmail(email, app_password):
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email, app_password)
        return True, "OK"
    except smtplib.SMTPAuthenticationError:
        return False, "App Password salah atau IMAP belum aktif"
    except Exception as e:
        return False, str(e)[:60]


def parse_nomor(text):
    """Parse satu atau banyak nomor dari teks"""
    lines = text.strip().split("\n")
    nomor_list = []
    for line in lines:
        for word in line.split():
            word = word.strip().replace(" ", "")
            if word.startswith("+") and word[1:].isdigit() and len(word) > 8:
                nomor_list.append(word)
    return nomor_list


# ─── KIRIM APPEAL ─────────────────────────────────────────────

async def kirim_appeal_satu_nomor(nomor):
    """Kirim appeal untuk satu nomor ke semua email WA"""
    hasil = []
    accounts = load_gmail()
    if not accounts:
        return [{"email": "-", "pengirim": "-", "status": "❌ Belum ada Gmail"}]

    body = get_next_template(nomor)
    subject = f"WhatsApp Account Login Issue - {nomor}"

    for i, wa_email in enumerate(WA_SUPPORT_EMAILS):
        gmail = accounts[i % len(accounts)]
        try:
            msg = MIMEMultipart()
            msg["From"] = gmail["email"]
            msg["To"] = wa_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(gmail["email"], gmail["app_password"])
                server.sendmail(gmail["email"], wa_email, msg.as_string())
            hasil.append({"email": wa_email, "pengirim": gmail["email"], "status": "✅"})
        except Exception as e:
            hasil.append({"email": wa_email, "pengirim": gmail["email"], "status": "❌"})
    return hasil


def cek_inbox_gmail(account):
    balasan = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(account["email"], account["app_password"])
        mail.select("inbox")
        _, data = mail.search(None, 'FROM "whatsapp.com" UNSEEN')
        if data[0]:
            for num in data[0].split():
                _, msg_data = mail.fetch(num, "(RFC822)")
                msg = email_lib.message_from_bytes(msg_data[0][1])
                subject = msg.get("Subject", "")
                sender = msg.get("From", "")
                date = msg.get("Date", "")
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                mail.store(num, "+FLAGS", "\\Seen")
                email_id = f"{sender}{date}{subject}"
                if email_id not in notified_emails:
                    notified_emails.add(email_id)
                    balasan.append({
                        "dari": sender, "subjek": subject,
                        "tanggal": date, "isi": body[:500],
                        "inbox": account["email"]
                    })
        mail.logout()
    except Exception as e:
        logging.error(f"Error cek inbox {account['email']}: {e}")
    return balasan


# ─── /start ───────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_users.add(update.effective_user.id)
    uid = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("🔴 Fix Merah WA", callback_data="fixmerah")],
        [InlineKeyboardButton("ℹ️ Info Bot", callback_data="info")],
    ]
    if is_admin(uid):
        keyboard.append([InlineKeyboardButton("⚙️ Setting Gmail", callback_data="setting_gmail")])
    await update.message.reply_text(
        "👋 *Bot Fix Merah WhatsApp*\n\n"
        "Kirim appeal ke WhatsApp Support otomatis.\n"
        f"Dikirim ke *{len(WA_SUPPORT_EMAILS)} email* sekaligus.\n\n"
        "Pilih menu:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ─── FIX MERAH ────────────────────────────────────────────────

async def fixmerah_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        send = query.edit_message_text
    else:
        send = update.message.reply_text

    accounts = load_gmail()
    if not accounts:
        await send("⚠️ *Belum ada Gmail terdaftar!*\n\nAdmin harus tambah Gmail dulu via /setting", parse_mode="Markdown")
        return ConversationHandler.END

    await send(
        "📱 *Fix Merah WA*\n\n"
        "Kirim nomor WA yang mau di-appeal.\n"
        "Bisa satu atau banyak nomor sekaligus.\n\n"
        "Format:\n"
        "`+6281234567890`\n"
        "`+6282345678901`\n"
        "`+6283456789012`\n\n"
        "Ketik /batal untuk membatalkan.",
        parse_mode="Markdown",
    )
    return TANYA_KONFIRM


async def tanya_konfirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nomor_list = parse_nomor(update.message.text)

    if not nomor_list:
        await update.message.reply_text(
            "⚠️ Nomor tidak valid.\nGunakan format: `+6281234567890`",
            parse_mode="Markdown",
        )
        return TANYA_KONFIRM

    context.user_data["nomor_list"] = nomor_list
    accounts = load_gmail()

    text = f"📋 *Konfirmasi Appeal*\n\n"
    text += f"📱 Jumlah nomor: *{len(nomor_list)}*\n"
    for n in nomor_list:
        text += f"• `{n}`\n"
    text += f"\n📧 Kirim ke *{len(WA_SUPPORT_EMAILS)} email* per nomor\n"
    text += f"📨 Gmail rotation: *{len(accounts)} akun*\n"
    text += f"📝 Template: *rolling otomatis*\n\n"
    text += "Lanjutkan?"

    keyboard = [[
        InlineKeyboardButton("✅ Kirim Sekarang", callback_data="konfirm_ya"),
        InlineKeyboardButton("❌ Batal", callback_data="konfirm_batal"),
    ]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    return TANYA_KONFIRM


async def proses_kirim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nomor_list = context.user_data.get("nomor_list", [])

    await query.edit_message_text(
        f"⏳ Memproses *{len(nomor_list)} nomor*...\n\nMohon tunggu.",
        parse_mode="Markdown",
    )

    total_sukses = 0
    total_gagal = 0
    report = f"📊 *Hasil Appeal*\n\n"

    for nomor in nomor_list:
        hasil = await kirim_appeal_satu_nomor(nomor)
        sukses = sum(1 for h in hasil if "✅" in h["status"])
        gagal = len(hasil) - sukses
        total_sukses += sukses
        total_gagal += gagal
        status = "✅" if gagal == 0 else "⚠️" if sukses > 0 else "❌"
        report += f"{status} `{nomor}` — {sukses}/{len(WA_SUPPORT_EMAILS)} terkirim\n"
        await asyncio.sleep(2)  # jeda antar nomor

    report += f"\n📈 Total sukses: *{total_sukses}* | Gagal: *{total_gagal}*"
    report += f"\n⏳ Tunggu balasan WA *1-3 hari kerja*"
    report += f"\n🔔 Notif otomatis kalau WA sudah balas"

    await query.edit_message_text(report, parse_mode="Markdown")
    return ConversationHandler.END


# ─── SETTING GMAIL ────────────────────────────────────────────

async def setting_gmail_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        send = query.edit_message_text
    else:
        send = update.message.reply_text

    accounts = load_gmail()
    keyboard = [
        [InlineKeyboardButton("➕ Tambah Gmail", callback_data="gmail_tambah")],
        [InlineKeyboardButton("📋 Lihat Daftar", callback_data="gmail_list")],
        [InlineKeyboardButton("🗑 Hapus Gmail", callback_data="gmail_hapus")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_start")],
    ]
    await send(
        f"⚙️ *Setting Gmail*\n\nGmail terdaftar: *{len(accounts)} akun*\n\nPilih aksi:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def gmail_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    accounts = load_gmail()
    if not accounts:
        text = "📋 *Daftar Gmail*\n\nBelum ada Gmail terdaftar."
    else:
        text = "📋 *Daftar Gmail:*\n\n"
        for i, acc in enumerate(accounts, 1):
            text += f"{i}. `{acc['email']}`\n"
    await query.edit_message_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="setting_gmail")]]),
    )


async def gmail_tambah_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "➕ *Tambah Gmail*\n\nKirim alamat Gmail:\n_Contoh: emailkamu@gmail.com_\n\nKetik /batal untuk membatalkan.",
        parse_mode="Markdown",
    )
    return TAMBAH_EMAIL


async def gmail_tambah_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip().lower()
    if "@gmail.com" not in email:
        await update.message.reply_text("⚠️ Harus Gmail. Contoh: `emailkamu@gmail.com`", parse_mode="Markdown")
        return TAMBAH_EMAIL
    accounts = load_gmail()
    if any(a["email"] == email for a in accounts):
        await update.message.reply_text(f"⚠️ `{email}` sudah terdaftar.", parse_mode="Markdown")
        return TAMBAH_EMAIL
    context.user_data["new_gmail"] = email
    await update.message.reply_text(
        f"✅ Gmail: `{email}`\n\n"
        "Sekarang kirim *App Password* (16 digit)\n\n"
        "Cara buat:\n"
        "1. myaccount.google.com\n"
        "2. Security → 2-Step Verification (aktifkan)\n"
        "3. App Passwords → Generate → copy\n\n"
        "Format: `xxxx xxxx xxxx xxxx`",
        parse_mode="Markdown",
    )
    return TAMBAH_PASSWORD


async def gmail_tambah_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    app_pass = update.message.text.strip()
    email = context.user_data.get("new_gmail")
    await update.message.reply_text("⏳ Testing koneksi Gmail...")
    ok, msg = test_gmail(email, app_pass)
    if not ok:
        await update.message.reply_text(
            f"❌ *Gagal!*\n\nError: `{msg}`\n\nCek App Password atau aktifkan IMAP di Gmail.",
            parse_mode="Markdown",
        )
        return TAMBAH_PASSWORD
    accounts = load_gmail()
    accounts.append({"email": email, "app_password": app_pass})
    save_gmail(accounts)
    await update.message.reply_text(
        f"✅ *Gmail berhasil ditambahkan!*\n\n`{email}`\nTotal: *{len(accounts)} akun*\n\nKetik /setting untuk kembali.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def gmail_hapus_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    accounts = load_gmail()
    if not accounts:
        await query.edit_message_text(
            "❌ Belum ada Gmail.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="setting_gmail")]]),
        )
        return
    keyboard = [[InlineKeyboardButton(f"🗑 {acc['email']}", callback_data=f"hapus_{i}")] for i, acc in enumerate(accounts)]
    keyboard.append([InlineKeyboardButton("🔙 Batal", callback_data="setting_gmail")])
    await query.edit_message_text(
        "🗑 *Hapus Gmail*\n\nPilih yang mau dihapus:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def gmail_hapus_konfirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[1])
    accounts = load_gmail()
    if idx >= len(accounts):
        await query.edit_message_text("❌ Gmail tidak ditemukan.")
        return
    hapus = accounts.pop(idx)
    save_gmail(accounts)
    await query.edit_message_text(
        f"✅ *Dihapus!*\n\n`{hapus['email']}`\nSisa: *{len(accounts)} akun*\n\nKetik /setting untuk kembali.",
        parse_mode="Markdown",
    )


# ─── BUTTON HANDLER ───────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if query.data == "info":
        accounts = load_gmail()
        await query.edit_message_text(
            "ℹ️ *Info Bot Fix Merah*\n\n"
            f"📧 Kirim ke *{len(WA_SUPPORT_EMAILS)} email* WA\n"
            f"📨 Gmail terdaftar: *{len(accounts)} akun*\n"
            f"📝 Template: *{len(TEMPLATES)} variasi rolling*\n"
            f"🔍 Cek balasan tiap *{CEK_INBOX_INTERVAL//60} menit*\n\n"
            "Ketik /fixmerah untuk mulai.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="back_start")]]),
        )
    elif query.data == "setting_gmail":
        if not is_admin(uid):
            await query.answer("❌ Bukan admin!", show_alert=True)
            return
        await setting_gmail_menu(update, context)
    elif query.data == "gmail_list":
        await gmail_list(update, context)
    elif query.data == "gmail_hapus":
        await gmail_hapus_start(update, context)
    elif query.data.startswith("hapus_"):
        await gmail_hapus_konfirm(update, context)
    elif query.data == "konfirm_batal":
        await query.edit_message_text("❌ Dibatalkan. Ketik /fixmerah untuk mulai ulang.")
        return ConversationHandler.END
    elif query.data == "back_start":
        keyboard = [
            [InlineKeyboardButton("🔴 Fix Merah WA", callback_data="fixmerah")],
            [InlineKeyboardButton("ℹ️ Info Bot", callback_data="info")],
        ]
        if is_admin(uid):
            keyboard.append([InlineKeyboardButton("⚙️ Setting Gmail", callback_data="setting_gmail")])
        await query.edit_message_text(
            "👋 *Bot Fix Merah WhatsApp*\n\nPilih menu:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan. Ketik /start untuk mulai lagi.")
    return ConversationHandler.END


async def setting_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Kamu bukan admin.")
        return
    await setting_gmail_menu(update, context)


# ─── JOB CEK INBOX ────────────────────────────────────────────

async def job_cek_inbox(context: ContextTypes.DEFAULT_TYPE):
    for account in load_gmail():
        balasan = cek_inbox_gmail(account)
        for b in balasan:
            pesan = (
                f"📬 *WhatsApp Support Membalas!*\n\n"
                f"📧 Inbox: `{b['inbox']}`\n"
                f"📨 Dari: {b['dari']}\n"
                f"📅 {b['tanggal']}\n"
                f"📋 Subjek: {b['subjek']}\n\n"
                f"💬 Isi:\n_{b['isi']}_"
            )
            target_ids = ADMIN_IDS if ADMIN_IDS else list(active_users)
            for uid in target_ids:
                try:
                    await context.bot.send_message(chat_id=uid, text=pesan, parse_mode="Markdown")
                except Exception as e:
                    logging.error(f"Gagal notif ke {uid}: {e}")


# ─── MAIN ─────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    fix_conv = ConversationHandler(
        entry_points=[
            CommandHandler("fixmerah", fixmerah_start),
            CallbackQueryHandler(fixmerah_start, pattern="^fixmerah$"),
        ],
        states={
            TANYA_KONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tanya_konfirm),
                CallbackQueryHandler(proses_kirim, pattern="^konfirm_ya$"),
                CallbackQueryHandler(button_handler, pattern="^konfirm_batal$"),
            ],
        },
        fallbacks=[CommandHandler("batal", cancel)],
    )

    tambah_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(gmail_tambah_start, pattern="^gmail_tambah$")],
        states={
            TAMBAH_EMAIL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, gmail_tambah_email)],
            TAMBAH_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, gmail_tambah_password)],
        },
        fallbacks=[CommandHandler("batal", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setting", setting_cmd))
    app.add_handler(fix_conv)
    app.add_handler(tambah_conv)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.job_queue.run_repeating(job_cek_inbox, interval=CEK_INBOX_INTERVAL, first=30)

    print("✅ Bot Fix Merah berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
