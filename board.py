"""
象棋棋盘表示和走法验证
"""


class XiangqiBoard:
    """象棋棋盘类"""

    # ICCS 坐标系统 (列a-i, 行0-9)
    FILES = "abcdefghi"
    RANKS = "0123456789"

    def __init__(self):
        """初始化空棋盘"""
        self.moves_history = []  # 走法历史

    def add_move(self, move: str) -> bool:
        """
        添加一步棋

        Args:
            move: ICCS 格式走法，如 'h2e2'

        Returns:
            是否成功添加
        """
        if self._validate_move_format(move):
            self.moves_history.append(move)
            return True
        return False

    def _validate_move_format(self, move: str) -> bool:
        """
        验证走法格式

        Args:
            move: 走法字符串

        Returns:
            格式是否正确
        """
        if len(move) != 4:
            return False

        from_file, from_rank, to_file, to_rank = move

        if from_file not in self.FILES or to_file not in self.FILES:
            return False
        if from_rank not in self.RANKS or to_rank not in self.RANKS:
            return False

        return True

    def get_moves_history(self) -> list[str]:
        """获取走法历史"""
        return self.moves_history.copy()

    def undo_last_move(self):
        """悔棋"""
        if self.moves_history:
            self.moves_history.pop()

    def reset(self):
        """重置棋盘"""
        self.moves_history = []

    def get_move_count(self) -> int:
        """获取走法数量"""
        return len(self.moves_history)
