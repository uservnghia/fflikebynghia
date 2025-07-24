import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests

# Debug: In ra giá trị của BOT_TOKEN
print(f"BOT_TOKEN from environment: {os.getenv('BOT_TOKEN')}")

# Cấu hình bot Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables!")

# Tạo application mà không dùng builder để tránh lỗi
application = Application.builder().token(BOT_TOKEN).build()

# Danh sách vùng hỗ trợ
SUPPORTED_REGIONS = ["ME", "SG", "BD", "TH", "VN", "US", "BR", "SAC", "NA"]

# Các endpoint API
PLAYER_INFO_URL = "https://info-ob49.vercel.app/api/account/"
BAN_CHECK_URL = "https://lkteam-bancheck.deno.dev/checkban"
SEARCH_NICKNAME_URL = "https://searchbynicknameapi.onrender.com/search"
LIKES_URL = "https://likes-api-lkteam-v3.onrender.com/like"
CHANGE_BIO_URL = "https://change-bio-api-lkteam.onrender.com/changebio"
CHANGE_NICKNAME_URL = "https://nickname-change-lkteam-dbww.onrender.com/change_nickname"

# Hàm xử lý lệnh
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = (
        "Chào bạn! Đây là bot Telegram sử dụng Free Fire API từ PRINCE-LKTEAM.\n"
        "Danh sách lệnh:\n"
        "/playerinfo <uid> <region> - Lấy thông tin người chơi\n"
        "/bancheck <uid> - Kiểm tra trạng thái cấm\n"
        "/searchnickname <nickname> - Tìm kiếm người chơi theo biệt danh\n"
        "/addlikes <uid> <region> <count> - Thêm lượt thích cho người chơi\n"
        "/changebio <uid> <password> <newbio> <region> - Thay đổi bio\n"
        "/changenickname <jwt> <newname> - Thay đổi biệt danh\n"
        "/help - Hiển thị hướng dẫn\n"
        f"Vùng hỗ trợ: {', '.join(SUPPORTED_REGIONS)}"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Danh sách lệnh:\n"
        "/playerinfo <uid> <region> - Lấy thông tin người chơi (VD: /playerinfo 12345678 SG)\n"
        "/bancheck <uid> - Kiểm tra trạng thái cấm (VD: /bancheck 12345678)\n"
        "/searchnickname <nickname> - Tìm kiếm người chơi theo biệt danh (VD: /searchnickname xLK-TEAM-1)\n"
        "/addlikes <uid> <region> <count> - Thêm lượt thích (VD: /addlikes 9067719977 US 100)\n"
        "/changebio <uid> <password> <newbio> <region> - Thay đổi bio (VD: /changebio 123 pass [FF0000]LK[00FF00]TEAM SG)\n"
        "/changenickname <jwt> <newname> - Thay đổi biệt danh (VD: /changenickname <jwt_token> LK-HYUN1)\n"
        f"Vùng hỗ trợ: {', '.join(SUPPORTED_REGIONS)}"
    )
    await update.message.reply_text(help_text)

async def player_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 2:
        await update.message.reply_text("Vui lòng cung cấp UID và vùng. VD: /playerinfo 12345678 SG")
        return
    uid, region = context.args
    if region.upper() not in SUPPORTED_REGIONS:
        await update.message.reply_text(f"Vùng không được hỗ trợ. Vùng hợp lệ: {', '.join(SUPPORTED_REGIONS)}")
        return
    try:
        response = requests.get(f"{PLAYER_INFO_URL}?uid={uid}®ion={region}")
        response.raise_for_status()
        data = response.json()
        basic_info = data.get("basicInfo", {})
        reply = (
            f"Thông tin người chơi:\n"
            f"UID: {basic_info.get('accountId', 'N/A')}\n"
            f"Tên: {basic_info.get('nickname', 'N/A')}\n"
            f"Vùng: {basic_info.get('region', 'N/A')}\n"
            f"Cấp độ: {basic_info.get('level', 'N/A')}\n"
            f"Bio: {data.get('socialInfo', {}).get('signature', 'N/A')}"
        )
        await update.message.reply_text(reply)
    except requests.RequestException as e:
        await update.message.reply_text(f"Lỗi khi gọi API: {str(e)}")

async def ban_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        await update.message.reply_text("Vui lòng cung cấp UID. VD: /bancheck 12345678")
        return
    uid = context.args[0]
    try:
        response = requests.get(f"{BAN_CHECK_URL}?uid={uid}")
        response.raise_for_status()
        data = response.json()
        reply = (
            f"Kiểm tra cấm:\n"
            f"UID: {data.get('uid', 'N/A')}\n"
            f"Tên: {data.get('nickname', 'N/A')}\n"
            f"Vùng: {data.get('region', 'N/A')}\n"
            f"Trạng thái: {'Cấm' if data.get('banned', False) else 'Không bị cấm'}\n"
            f"Thời gian cấm: {data.get('ban_period_months', 0)} tháng"
        )
        await update.message.reply_text(reply)
    except requests.RequestException as e:
        await update.message.reply_text(f"Lỗi khi gọi API: {str(e)}")

async def search_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 1:
        await update.message.reply_text("Vui lòng cung cấp biệt danh. VD: /searchnickname xLK-TEAM-1")
        return
    nickname = " ".join(context.args)
    try:
        response = requests.get(f"{SEARCH_NICKNAME_URL}?name={nickname}")
        response.raise_for_status()
        data = response.json()
        results = data.get("result", [])
        if not results:
            await update.message.reply_text("Không tìm thấy người chơi nào.")
            return
        reply = "Kết quả tìm kiếm:\n"
        for player in results[:5]:
            reply += (
                f"Tên: {player.get('nickname', 'N/A')}\n"
                f"UID: {player.get('account_id', 'N/A')}\n"
                f"Vùng: {player.get('region', 'N/A')}\n"
                f"Cấp độ: {player.get('level', 'N/A')}\n\n"
            )
        await update.message.reply_text(reply)
    except requests.RequestException as e:
        await update.message.reply_text(f"Lỗi khi gọi API: {str(e)}")

async def add_likes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 3:
        await update.message.reply_text("Vui lòng cung cấp UID, vùng và số lượt thích. VD: /addlikes 9067719977 US 100")
        return
    uid, region, count = context.args
    if region.upper() not in SUPPORTED_REGIONS:
        await update.message.reply_text(f"Vùng không được hỗ trợ. Vùng hợp lệ: {', '.join(SUPPORTED_REGIONS)}")
        return
    try:
        count = int(count)
        if count <= 0:
            raise ValueError("Số lượt thích phải lớn hơn 0")
        response = requests.get(f"{LIKES_URL}?uid={uid}®ion={region}&count={count}")
        response.raise_for_status()
        data = response.json()
        reply = (
            f"Kết quả thêm lượt thích:\n"
            f"Tên: {data.get('name', 'N/A')}\n"
            f"UID: {data.get('uid', 'N/A')}\n"
            f"Vùng: {data.get('region', 'N/A')}\n"
            f"Lượt thích trước: {data.get('likes_before', 'N/A')}\n"
            f"Lượt thích sau: {data.get('likes_after', 'N/A')}\n"
            f"Lượt thích đã thêm: {data.get('likes_added', 'N/A')}\n"
            f"Lượt thích thất bại: {data.get('failed_likes', 'N/A')}"
        )
        await update.message.reply_text(reply)
    except ValueError as e:
        await update.message.reply_text(f"Lỗi: {str(e)}")
    except requests.RequestException as e:
        await update.message.reply_text(f"Lỗi khi gọi API: {str(e)}")

async def change_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 4:
        await update.message.reply_text("Vui lòng cung cấp UID, mật khẩu, bio mới và vùng. VD: /changebio 123 pass [FF0000]LK[00FF00]TEAM SG")
        return
    uid, password = context.args[0], context.args[1]
    newbio = " ".join(context.args[2:-1])
    region = context.args[-1]
    if region.upper() not in SUPPORTED_REGIONS:
        await update.message.reply_text(f"Vùng không được hỗ trợ. Vùng hợp lệ: {', '.join(SUPPORTED_REGIONS)}")
        return
    try:
        response = requests.get(f"{CHANGE_BIO_URL}?uid={uid}&password={password}&newbio={newbio}®ion={region}")
        response.raise_for_status()
        data = response.json()
        reply = f"Kết quả thay đổi bio:\nTrạng thái: {data.get('status', 'N/A')}\nThông báo: {data.get('message', 'N/A')}"
        await update.message.reply_text(reply)
    except requests.RequestException as e:
        await update.message.reply_text(f"Lỗi khi gọi API: {str(e)}")

async def change_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("Vui lòng cung cấp JWT token và biệt danh mới. VD: /changenickname <jwt_token> LK-HYUN1")
        return
    jwt_token = context.args[0]
    newname = " ".join(context.args[1:])
    try:
        response = requests.get(f"{CHANGE_NICKNAME_URL}?jwt={jwt_token}&newname={newname}")
        response.raise_for_status()
        data = response.json()
        reply = (
            f"Kết quả thay đổi biệt danh:\n"
            f"UID: {data.get('account_id', 'N/A')}\n"
            f"Tên cũ: {data.get('old_name', 'N/A')}\n"
            f"Tên mới: {data.get('new_name', 'N/A')}\n"
            f"Vùng: {data.get('region', 'N/A')}\n"
            f"Trạng thái: {data.get('status_code', 'N/A')}"
        )
        await update.message.reply_text(reply)
    except requests.RequestException as e:
        await update.message.reply_text(f"Lỗi khi gọi API: {str(e)}")

# Hàm chạy bot
async def run_bot():
    # Thêm handler cho bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("playerinfo", player_info))
    application.add_handler(CommandHandler("bancheck", ban_check))
    application.add_handler(CommandHandler("searchnickname", search_nickname))
    application.add_handler(CommandHandler("addlikes", add_likes))
    application.add_handler(CommandHandler("changebio", change_bio))
    application.add_handler(CommandHandler("changenickname", change_nickname))

    # Chạy bot polling với cấu hình thủ công
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.run_polling()

if __name__ == "__main__":
    # Chạy bot trong event loop
    asyncio.run(run_bot())
