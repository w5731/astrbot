import argparse
import asyncio
import mimetypes
import os
import sys
from pathlib import Path

from astrbot.core import LogBroker, LogManager, db_helper, logger
from astrbot.core.config.default import VERSION
from astrbot.core.initial_loader import InitialLoader
from astrbot.core.utils.astrbot_path import get_astrbot_data_path, get_astrbot_path
from astrbot.core.utils.io import download_dashboard, get_dashboard_version

# 将父目录添加到 sys.path
sys.path.append(Path(__file__).parent.as_posix())

logo_tmpl = r"""
     ___           _______.___________..______      .______     ______   .___________.
    /   \         /       |           ||   _  \     |   _  \   /  __  \  |           |
   /  ^  \       |   (----`---|  |----`|  |_)  |    |  |_)  | |  |  |  | `---|  |----`
  /  /_\  \       \   \       |  |     |      /     |   _  <  |  |  |  |     |  |
 /  _____  \  .----)   |      |  |     |  |\  \----.|  |_)  | |  `--'  |     |  |
/__/     \__\ |_______/       |__|     | _| `._____||______/   \______/      |__|

"""


def check_env():
    if not (sys.version_info.major == 3 and sys.version_info.minor >= 10):
        logger.error("请使用 Python3.10+ 运行本项目。")
        exit()

    os.makedirs("data/config", exist_ok=True)
    os.makedirs("data/plugins", exist_ok=True)
    os.makedirs("data/temp", exist_ok=True)

    # 针对问题 #181 的临时解决方案
    mimetypes.add_type("text/javascript", ".js")
    mimetypes.add_type("text/javascript", ".mjs")
    mimetypes.add_type("application/json", ".json")


async def check_dashboard_files(webui_dir: str | None = None):
    """Resolve WebUI dir: 1) --webui-dir 2) built-in dashboard/dist 3) data/dist 4) download to data."""
    if webui_dir and os.path.exists(webui_dir):
        logger.info(f"使用指定的 WebUI 目录: {webui_dir}")
        return webui_dir
    if webui_dir:
        logger.warning(f"指定的 WebUI 目录 {webui_dir} 不存在，将使用默认逻辑。")

    # Prefer built-in frontend (project root / dashboard/dist) so local/Docker use repo frontend
    builtin_dist = os.path.join(get_astrbot_path(), "dashboard", "dist")
    if os.path.exists(builtin_dist):
        v = await get_dashboard_version(builtin_dist)
        if v is not None and v != f"v{VERSION}":
            logger.warning(
                f"检测到 WebUI 版本 ({v}) 与当前 AstrBot 版本 (v{VERSION}) 不符。",
            )
        logger.info("使用项目内置 WebUI: dashboard/dist")
        return builtin_dist

    data_dist_path = os.path.join(get_astrbot_data_path(), "dist")
    if os.path.exists(data_dist_path):
        v = await get_dashboard_version(data_dist_path)
        if v is not None and v != f"v{VERSION}":
            logger.warning(
                f"检测到 WebUI 版本 ({v}) 与当前 AstrBot 版本 (v{VERSION}) 不符。",
            )
        logger.info("使用 data/dist 中的 WebUI。")
        return data_dist_path

    logger.info(
        "未找到 WebUI，开始下载... 如失败请前往 https://github.com/AstrBotDevs/AstrBot/releases/latest 下载 dist.zip 解压至 data 目录。",
    )
    try:
        await download_dashboard(version=f"v{VERSION}", latest=False)
    except Exception as e:
        logger.critical(f"下载管理面板文件失败: {e}。")
        return None
    logger.info("管理面板下载完成。")
    return data_dist_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AstrBot")
    parser.add_argument(
        "--webui-dir",
        type=str,
        help="指定 WebUI 静态文件目录路径",
        default=None,
    )
    args = parser.parse_args()

    check_env()

    # 启动日志代理
    log_broker = LogBroker()
    LogManager.set_queue_handler(logger, log_broker)

    # 检查仪表板文件
    webui_dir = asyncio.run(check_dashboard_files(args.webui_dir))

    db = db_helper

    # 打印 logo
    logger.info(logo_tmpl)

    core_lifecycle = InitialLoader(db, log_broker)
    core_lifecycle.webui_dir = webui_dir
    asyncio.run(core_lifecycle.start())
