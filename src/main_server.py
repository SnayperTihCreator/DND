import asyncio
import logging

from ServerTools.core.server import Server
import typer
from log import setup_logging

setup_logging("SERVER")

app = typer.Typer()

logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("qasync").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


async def runner(server: Server):
    server.start_services()
    
    logger.info(f"🚀 Сервер запущен!")
    logger.info(f"🔑 Master Token: {server.master_token}")
    logger.info(f"🌐 Ожидание подключений...")
    
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        server.stop_services()
        logger.info("\n🛑 Сервер остановлен")


@app.command()
def main(master_token: str):
    server = Server(master_token)
    
    try:
        asyncio.run(runner(server))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    app(help_option_names=["--help", "-h"])
