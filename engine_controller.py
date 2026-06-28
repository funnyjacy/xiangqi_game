"""
象棋引擎 UCI 协议通信模块
"""
import subprocess
import os
import sys
from typing import Optional, Tuple


def get_resource_dir() -> str:
    """
    获取资源根目录。

    - 开发运行时：返回本文件所在目录。
    - PyInstaller 打包后：返回可执行文件所在目录（引擎文件随 exe 一起分发）。
    """
    if getattr(sys, "frozen", False):
        # 已被 PyInstaller 打包。打包进来的数据文件位于 sys._MEIPASS：
        # - onedir 模式下指向 exe 同级的 _internal 目录
        # - onefile 模式下指向运行时解压的临时目录
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    # 普通脚本运行，使用本文件所在目录
    return os.path.dirname(os.path.abspath(__file__))


class XiangqiEngine:
    """象棋引擎类，负责与 Pikafish 引擎通信"""

    def __init__(self, engine_path: Optional[str] = None):
        """
        初始化引擎

        Args:
            engine_path: 引擎可执行文件路径。默认根据运行环境自动定位
                         resource_dir/engine/pikafish.exe。
        """
        if engine_path is None:
            engine_path = os.path.join(get_resource_dir(), "engine", "pikafish.exe")
        self.engine_path = engine_path
        self.process: Optional[subprocess.Popen] = None
        self.initialized = False

    def start(self) -> bool:
        """启动引擎进程"""
        # 转换为绝对路径
        abs_path = os.path.abspath(self.engine_path)

        if not os.path.exists(abs_path):
            print(f"错误: 引擎文件不存在 - {abs_path}")
            print("请下载 Pikafish 引擎并放置在 engine/ 目录下")
            return False

        try:
            self.process = subprocess.Popen(
                abs_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                # 引擎需要在自身目录下运行才能找到 pikafish.nnue 权重文件
                cwd=os.path.dirname(abs_path),
                # 打包后无控制台时，避免弹出黑色命令行窗口
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            # 发送 UCI 初始化命令
            self._send_command("uci")
            # 等待 uciok 响应
            while True:
                line = self._read_line()
                if line == "uciok":
                    break
            self.initialized = True
            return True
        except Exception as e:
            print(f"引擎启动失败: {e}")
            return False

    def _send_command(self, command: str):
        """发送命令到引擎"""
        if self.process and self.process.stdin:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()

    def _read_line(self) -> str:
        """从引擎读取一行输出"""
        if self.process and self.process.stdout:
            return self.process.stdout.readline().strip()
        return ""

    def new_game(self):
        """开始新游戏"""
        self._send_command("ucinewgame")
        self._send_command("isready")
        while self._read_line() != "readyok":
            pass

    def set_position(self, moves: list[str]):
        """
        设置当前局面

        Args:
            moves: 走法列表，使用 ICCS 格式 (如 ['h2e2', 'h9g7'])
        """
        if not moves:
            command = "position startpos"
        else:
            moves_str = " ".join(moves)
            command = f"position startpos moves {moves_str}"
        self._send_command(command)

    def get_best_move(self, depth: int = 20, time_ms: int = 3000) -> Tuple[str, int]:
        """
        获取最佳走法

        Args:
            depth: 搜索深度
            time_ms: 思考时间（毫秒）

        Returns:
            (最佳走法, 评分) 元组
        """
        self._send_command(f"go depth {depth} movetime {time_ms}")

        best_move = ""
        score = 0

        while True:
            line = self._read_line()
            if not line:
                continue

            # 解析评分信息
            if line.startswith("info") and "score cp" in line:
                parts = line.split()
                try:
                    cp_index = parts.index("cp")
                    score = int(parts[cp_index + 1])
                except (ValueError, IndexError):
                    pass

            # 获取最佳走法
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2:
                    best_move = parts[1]
                break

        return best_move, score

    def stop(self):
        """停止引擎"""
        if self.process:
            self._send_command("quit")
            self.process.wait(timeout=3)
            self.process = None
            self.initialized = False
