"""
象棋作弊系统 - 完整可视化 GUI 版本
带象棋图标，点击移动棋子
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, Tuple, Dict

from engine_controller import XiangqiEngine
from board import XiangqiBoard


class ChessPiece:
    """象棋棋子类"""

    # 棋子中文名称
    RED_PIECES = {
        'r': '車', 'n': '馬', 'b': '相', 'a': '仕', 'k': '帥',
        'c': '炮', 'p': '兵'
    }

    BLACK_PIECES = {
        'r': '车', 'n': '马', 'b': '象', 'a': '士', 'k': '将',
        'c': '炮', 'p': '卒'
    }

    @staticmethod
    def get_name(piece_type: str, is_red: bool) -> str:
        """获取棋子名称"""
        if is_red:
            return ChessPiece.RED_PIECES.get(piece_type, '')
        else:
            return ChessPiece.BLACK_PIECES.get(piece_type, '')


class VisualXiangqiGUI:
    """可视化象棋 GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("象棋作弊系统 - 可视化版本")
        self.root.geometry("1100x750")
        self.root.resizable(False, False)

        # 棋盘参数
        self.margin = 50
        self.cell_size = 60
        self.piece_radius = 25

        # 棋盘状态 (file, rank) -> (piece_type, is_red)
        self.board_state: Dict[Tuple[int, int], Tuple[str, bool]] = {}
        self._init_board_state()

        # 游戏状态
        self.engine: Optional[XiangqiEngine] = None
        self.move_history = XiangqiBoard()
        self.my_is_red = True       # 我方是否执红（先手）
        self.ai_thinking = False    # 引擎是否正在计算（防止重入）
        self.engine_running = False
        self.game_started = False   # 是否已开始对局
        self.manual_input_mode = False  # 是否正在手动输入我方走法

        # 选择状态
        self.selected_piece: Optional[Tuple[int, int]] = None
        self.last_move: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None

        # 棋盘是否翻转显示（False: 红方在下；True: 红方在上）
        self.flipped = False

        # 创建 UI
        self._create_ui()

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _init_board_state(self):
        """初始化棋盘状态（标准开局）"""
        # 黑方（上方，rank 9-7）
        # 车马象士将士象马车
        black_back = [
            ((0, 9), ('r', False)), ((1, 9), ('n', False)), ((2, 9), ('b', False)),
            ((3, 9), ('a', False)), ((4, 9), ('k', False)), ((5, 9), ('a', False)),
            ((6, 9), ('b', False)), ((7, 9), ('n', False)), ((8, 9), ('r', False))
        ]

        # 炮
        black_cannons = [((1, 7), ('c', False)), ((7, 7), ('c', False))]

        # 卒
        black_pawns = [
            ((0, 6), ('p', False)), ((2, 6), ('p', False)), ((4, 6), ('p', False)),
            ((6, 6), ('p', False)), ((8, 6), ('p', False))
        ]

        # 红方（下方，rank 0-2）
        # 车马相仕帅仕相马车
        red_back = [
            ((0, 0), ('r', True)), ((1, 0), ('n', True)), ((2, 0), ('b', True)),
            ((3, 0), ('a', True)), ((4, 0), ('k', True)), ((5, 0), ('a', True)),
            ((6, 0), ('b', True)), ((7, 0), ('n', True)), ((8, 0), ('r', True))
        ]

        # 炮
        red_cannons = [((1, 2), ('c', True)), ((7, 2), ('c', True))]

        # 兵
        red_pawns = [
            ((0, 3), ('p', True)), ((2, 3), ('p', True)), ((4, 3), ('p', True)),
            ((6, 3), ('p', True)), ((8, 3), ('p', True))
        ]

        # 合并所有棋子
        all_pieces = (black_back + black_cannons + black_pawns +
                      red_back + red_cannons + red_pawns)

        for pos, piece_info in all_pieces:
            self.board_state[pos] = piece_info

    def _create_ui(self):
        """创建用户界面"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 左侧：棋盘
        self._create_board_canvas(main_frame)

        # 右侧：控制面板
        self._create_control_panel(main_frame)

    def _create_board_canvas(self, parent):
        """创建棋盘画布"""
        board_frame = ttk.LabelFrame(parent, text="象棋棋盘", padding="10")
        board_frame.grid(row=0, column=0, padx=(0, 10), sticky=(tk.N, tk.S))

        # 画布
        canvas_width = self.margin * 2 + self.cell_size * 8
        canvas_height = self.margin * 2 + self.cell_size * 9

        self.canvas = tk.Canvas(
            board_frame,
            width=canvas_width,
            height=canvas_height,
            bg="#F5DEB3",  # 小麦色
            highlightthickness=2,
            highlightbackground="#8B4513"
        )
        self.canvas.pack()

        # 绑定点击事件
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # 绘制棋盘和棋子
        self._draw_board()
        self._draw_all_pieces()

    def _draw_board(self):
        """绘制棋盘线"""
        # 横线
        for i in range(10):
            y = self.margin + i * self.cell_size
            self.canvas.create_line(
                self.margin, y,
                self.margin + 8 * self.cell_size, y,
                width=2, fill="#654321"
            )

        # 竖线（分为上下两部分，中间是楚河汉界）
        for i in range(9):
            x = self.margin + i * self.cell_size
            # 上半部分
            self.canvas.create_line(
                x, self.margin,
                x, self.margin + 4 * self.cell_size,
                width=2, fill="#654321"
            )
            # 下半部分
            self.canvas.create_line(
                x, self.margin + 5 * self.cell_size,
                x, self.margin + 9 * self.cell_size,
                width=2, fill="#654321"
            )

        # 九宫格斜线（黑方）
        self.canvas.create_line(
            self.margin + 3 * self.cell_size, self.margin,
            self.margin + 5 * self.cell_size, self.margin + 2 * self.cell_size,
            width=2, fill="#654321"
        )
        self.canvas.create_line(
            self.margin + 5 * self.cell_size, self.margin,
            self.margin + 3 * self.cell_size, self.margin + 2 * self.cell_size,
            width=2, fill="#654321"
        )

        # 九宫格斜线（红方）
        self.canvas.create_line(
            self.margin + 3 * self.cell_size, self.margin + 7 * self.cell_size,
            self.margin + 5 * self.cell_size, self.margin + 9 * self.cell_size,
            width=2, fill="#654321"
        )
        self.canvas.create_line(
            self.margin + 5 * self.cell_size, self.margin + 7 * self.cell_size,
            self.margin + 3 * self.cell_size, self.margin + 9 * self.cell_size,
            width=2, fill="#654321"
        )

        # 楚河汉界文字
        self.canvas.create_text(
            self.margin + 2 * self.cell_size, self.margin + 4.5 * self.cell_size,
            text="楚 河", font=("KaiTi", 20, "bold"), fill="#8B4513"
        )
        self.canvas.create_text(
            self.margin + 6 * self.cell_size, self.margin + 4.5 * self.cell_size,
            text="汉 界", font=("KaiTi", 20, "bold"), fill="#8B4513"
        )

    def _draw_all_pieces(self):
        """绘制所有棋子"""
        self.canvas.delete("piece")
        self.canvas.delete("highlight")

        # 绘制上一步走法的高亮
        if self.last_move:
            from_pos, to_pos = self.last_move
            self._draw_move_highlight(from_pos, to_pos)

        # 绘制选中棋子的高亮
        if self.selected_piece:
            self._draw_selection_highlight(self.selected_piece)

        # 绘制所有棋子
        for (file, rank), (piece_type, is_red) in self.board_state.items():
            self._draw_piece(file, rank, piece_type, is_red)

    def _board_to_screen(self, file: int, rank: int) -> Tuple[int, int]:
        """将棋盘坐标 (file, rank) 转换为画布像素坐标，考虑翻转状态"""
        if self.flipped:
            col = 8 - file
            row = rank
        else:
            col = file
            row = 9 - rank
        x = self.margin + col * self.cell_size
        y = self.margin + row * self.cell_size
        return x, y

    def _screen_to_board(self, px: int, py: int) -> Tuple[int, int]:
        """将画布像素坐标转换为棋盘坐标 (file, rank)，考虑翻转状态"""
        col = round((px - self.margin) / self.cell_size)
        row = round((py - self.margin) / self.cell_size)
        if self.flipped:
            file = 8 - col
            rank = row
        else:
            file = col
            rank = 9 - row
        return file, rank

    def _draw_piece(self, file: int, rank: int, piece_type: str, is_red: bool):
        """绘制单个棋子"""
        x, y = self._board_to_screen(file, rank)

        # 棋子圆圈
        fill_color = "#FFE4B5" if is_red else "#708090"
        outline_color = "#8B0000" if is_red else "#000000"

        self.canvas.create_oval(
            x - self.piece_radius, y - self.piece_radius,
            x + self.piece_radius, y + self.piece_radius,
            fill=fill_color,
            outline=outline_color,
            width=3,
            tags="piece"
        )

        # 棋子文字
        text_color = "#8B0000" if is_red else "#FFFFFF"
        piece_name = ChessPiece.get_name(piece_type, is_red)

        self.canvas.create_text(
            x, y,
            text=piece_name,
            font=("KaiTi", 18, "bold"),
            fill=text_color,
            tags="piece"
        )

    def _draw_selection_highlight(self, pos: Tuple[int, int]):
        """绘制选中高亮"""
        file, rank = pos
        x, y = self._board_to_screen(file, rank)

        self.canvas.create_oval(
            x - self.piece_radius - 5, y - self.piece_radius - 5,
            x + self.piece_radius + 5, y + self.piece_radius + 5,
            outline="#00FF00",
            width=3,
            tags="highlight"
        )

    def _draw_move_highlight(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        """绘制走法高亮"""
        for pos in [from_pos, to_pos]:
            file, rank = pos
            x, y = self._board_to_screen(file, rank)

            self.canvas.create_oval(
                x - self.piece_radius - 3, y - self.piece_radius - 3,
                x + self.piece_radius + 3, y + self.piece_radius + 3,
                outline="#0066FF",
                width=4,
                tags="highlight"
            )

    def _move_count(self) -> int:
        """已走步数"""
        return self.move_history.get_move_count()

    def _side_to_move_is_red(self) -> bool:
        """当前轮到红方走（象棋红先，偶数步为红方）"""
        return self._move_count() % 2 == 0

    def _is_my_turn(self) -> bool:
        """当前是否轮到我方"""
        return self._side_to_move_is_red() == self.my_is_red

    def _advance_turn(self):
        """根据当前局面决定下一步由谁行棋"""
        if not self.engine_running:
            return

        if self._is_my_turn():
            # 我方回合：AI 替我方计算并落子
            self._ai_play_my_move()
        else:
            # 对方回合：等待我手动输入对方走法
            opp_is_red = not self.my_is_red
            side = "红方" if opp_is_red else "黑方"
            self.add_history(f"请点击棋盘输入对方（{side}）的走法")
            self.update_suggest_text(f"等待输入对方（{side}）走法...\n\n点击对方棋子，再点击目标位置。")

        # 每次状态切换都刷新「手动输入」按钮
        self._refresh_manual_btn()

    def _on_canvas_click(self, event):
        """处理画布点击事件"""
        if not self.engine_running or not self.game_started:
            return

        if self.manual_input_mode:
            # 手动输入模式：选择我方棋子并落子
            self._handle_click_for_side(event, side_is_red=self.my_is_red, is_manual=True)
            return

        # 正常模式：只有轮到对方、且 AI 未在思考时，才允许点击输入
        if self._is_my_turn() or self.ai_thinking:
            return

        opp_is_red = not self.my_is_red
        self._handle_click_for_side(event, side_is_red=opp_is_red, is_manual=False)

    def _handle_click_for_side(self, event, side_is_red: bool, is_manual: bool):
        """处理一次点击：选择/落子指定颜色方的棋子"""
        # 转换点击坐标到棋盘位置
        file, rank = self._screen_to_board(event.x, event.y)

        # 检查是否在棋盘范围内
        if not (0 <= file <= 8 and 0 <= rank <= 9):
            return

        pos = (file, rank)

        if self.selected_piece is None:
            # 第一次点击：选择指定方的棋子
            if pos in self.board_state and self.board_state[pos][1] == side_is_red:
                self.selected_piece = pos
                self._draw_all_pieces()
        else:
            # 第二次点击
            if pos == self.selected_piece:
                # 点击同一个棋子：取消选择
                self.selected_piece = None
                self._draw_all_pieces()
            elif pos in self.board_state and self.board_state[pos][1] == side_is_red:
                # 点击另一个己方棋子：切换选中，避免吃自己的子
                self.selected_piece = pos
                self._draw_all_pieces()
            else:
                # 目标为空格或对方棋子：先校验走法是否合法
                legal, reason = self._is_legal_move(self.selected_piece, pos)
                if not legal:
                    self.update_suggest_text(f"⚠ 非法走法：{reason}\n\n请重新选择目标位置。")
                    return  # 保持选中，等待重新点击
                self._commit_move(self.selected_piece, pos, is_manual=is_manual)

    def _in_palace(self, x: int, y: int, is_red: bool) -> bool:
        """坐标是否在己方九宫内"""
        if x < 3 or x > 5:
            return False
        return (0 <= y <= 2) if is_red else (7 <= y <= 9)

    def _count_between(self, fx: int, fy: int, tx: int, ty: int) -> int:
        """统计两点之间（不含端点）直线上的棋子数；非水平/垂直返回 -1"""
        count = 0
        if fx == tx:
            step = 1 if ty > fy else -1
            for y in range(fy + step, ty, step):
                if (fx, y) in self.board_state:
                    count += 1
        elif fy == ty:
            step = 1 if tx > fx else -1
            for x in range(fx + step, tx, step):
                if (x, fy) in self.board_state:
                    count += 1
        else:
            return -1
        return count

    def _kings_face_each_other(self, board: dict) -> bool:
        """两个将/帅是否在同一直线上直接照面（飞将）"""
        red_king = black_king = None
        for (x, y), (pt, red) in board.items():
            if pt == 'k':
                if red:
                    red_king = (x, y)
                else:
                    black_king = (x, y)
        if not red_king or not black_king:
            return False
        if red_king[0] != black_king[0]:
            return False
        fx = red_king[0]
        lo, hi = sorted((red_king[1], black_king[1]))
        for y in range(lo + 1, hi):
            if (fx, y) in board:
                return False
        return True

    def _is_legal_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> Tuple[bool, str]:
        """校验走法是否符合该棋子的行棋规则。返回 (是否合法, 原因)"""
        if from_pos not in self.board_state:
            return False, "起点没有棋子"

        piece_type, is_red = self.board_state[from_pos]

        # 兜底：不能吃己方棋子
        if to_pos in self.board_state and self.board_state[to_pos][1] == is_red:
            return False, "不能吃自己的棋子"

        fx, fy = from_pos
        tx, ty = to_pos
        dx, dy = tx - fx, ty - fy

        if dx == 0 and dy == 0:
            return False, "起点和终点相同"

        ok, reason = True, ""

        if piece_type == 'r':  # 车
            if dx != 0 and dy != 0:
                ok, reason = False, "车只能走直线"
            elif self._count_between(fx, fy, tx, ty) != 0:
                ok, reason = False, "车的路径被阻挡"

        elif piece_type == 'c':  # 炮
            if dx != 0 and dy != 0:
                ok, reason = False, "炮只能走直线"
            else:
                between = self._count_between(fx, fy, tx, ty)
                is_capture = to_pos in self.board_state
                if is_capture and between != 1:
                    ok, reason = False, "炮吃子必须隔一个棋子"
                elif not is_capture and between != 0:
                    ok, reason = False, "炮移动路径被阻挡"

        elif piece_type == 'n':  # 马
            if not ((abs(dx) == 1 and abs(dy) == 2) or (abs(dx) == 2 and abs(dy) == 1)):
                ok, reason = False, "马走日字"
            else:
                leg = (fx + dx // 2, fy) if abs(dx) == 2 else (fx, fy + dy // 2)
                if leg in self.board_state:
                    ok, reason = False, "蹩马腿"

        elif piece_type == 'b':  # 相/象
            if abs(dx) != 2 or abs(dy) != 2:
                ok, reason = False, "相/象走田字"
            elif (fx + dx // 2, fy + dy // 2) in self.board_state:
                ok, reason = False, "塞象眼"
            elif is_red and ty > 4:
                ok, reason = False, "相/象不能过河"
            elif (not is_red) and ty < 5:
                ok, reason = False, "相/象不能过河"

        elif piece_type == 'a':  # 仕/士
            if abs(dx) != 1 or abs(dy) != 1:
                ok, reason = False, "仕/士只能走斜线一格"
            elif not self._in_palace(tx, ty, is_red):
                ok, reason = False, "仕/士不能走出九宫"

        elif piece_type == 'k':  # 帅/将
            if abs(dx) + abs(dy) != 1:
                ok, reason = False, "帅/将只能上下左右走一格"
            elif not self._in_palace(tx, ty, is_red):
                ok, reason = False, "帅/将不能走出九宫"

        elif piece_type == 'p':  # 兵/卒
            forward = 1 if is_red else -1
            crossed = (fy >= 5) if is_red else (fy <= 4)
            if dx == 0 and dy == forward:
                pass  # 前进一格
            elif crossed and dy == 0 and abs(dx) == 1:
                pass  # 过河后可左右平移一格
            else:
                ok, reason = False, "兵/卒只能前进，过河后才能平移"

        else:
            ok, reason = False, "未知棋子"

        if not ok:
            return False, reason

        # 模拟走子后检查「飞将」（将帅照面）
        new_board = dict(self.board_state)
        del new_board[from_pos]
        new_board[to_pos] = (piece_type, is_red)
        if self._kings_face_each_other(new_board):
            return False, "将帅不能照面（飞将）"

        return True, ""

    def _commit_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], is_manual: bool):
        """提交一步走法（来自点击）"""
        # 转换为 ICCS 格式
        move_str = self._pos_to_iccs(from_pos, to_pos)

        # 执行移动
        self._execute_move(from_pos, to_pos, move_str)
        self.selected_piece = None

        # 添加到历史
        self.move_history.add_move(move_str)
        if is_manual:
            self.add_history(f"[我方·手动] {move_str}")
            self.manual_input_mode = False
        else:
            self.add_history(f"[对方] {move_str}")

        # 推进回合
        self._advance_turn()

    def _execute_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], move_str: str):
        """执行移动（更新棋盘状态）"""
        # 移动棋子
        if from_pos in self.board_state:
            piece = self.board_state[from_pos]
            del self.board_state[from_pos]
            self.board_state[to_pos] = piece

            # 记录最后一步走法
            self.last_move = (from_pos, to_pos)

            # 重新绘制
            self._draw_all_pieces()

    def _pos_to_iccs(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> str:
        """将棋盘位置转换为 ICCS 格式"""
        files = "abcdefghi"
        from_file, from_rank = from_pos
        to_file, to_rank = to_pos

        return f"{files[from_file]}{from_rank}{files[to_file]}{to_rank}"

    def _iccs_to_pos(self, move: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """将 ICCS 格式转换为棋盘位置"""
        files = "abcdefghi"
        from_file = files.index(move[0])
        from_rank = int(move[1])
        to_file = files.index(move[2])
        to_rank = int(move[3])

        return ((from_file, from_rank), (to_file, to_rank))

    def _rebuild_board_from_history(self):
        """根据走法历史重建棋盘状态（用于回退，可还原被吃的棋子）"""
        # 重置到开局
        self.board_state.clear()
        self._init_board_state()

        # 依次重放所有走法
        moves = self.move_history.get_moves_history()
        last = None
        for move in moves:
            from_pos, to_pos = self._iccs_to_pos(move)
            if from_pos in self.board_state:
                piece = self.board_state[from_pos]
                del self.board_state[from_pos]
                self.board_state[to_pos] = piece  # 目标位置若有子则被吃
                last = (from_pos, to_pos)

        # 更新最后一步高亮
        self.last_move = last

    def _undo_move(self):
        """回退一步（无论当前轮到我方还是对方）"""
        if not self.engine_running or not self.game_started or self.ai_thinking:
            return

        if self._move_count() == 0:
            self.update_suggest_text("已经是开局，无法继续回退。")
            return

        # 撤销最后一步走法
        self.move_history.undo_last_move()

        # 取消当前选择，重建棋盘
        self.selected_piece = None
        self._rebuild_board_from_history()
        self._draw_all_pieces()

        # 同步引擎局面
        self.engine.set_position(self.move_history.get_moves_history())

        # 提示当前轮到谁，但不自动让 AI 落子
        self.add_history(f"↩ 已回退一步（当前共 {self._move_count()} 步）")

        if self._is_my_turn():
            self.update_suggest_text(
                "已回退到我方回合。\n\n点击「重算我方走法」让 AI 给出建议。"
            )
        else:
            opp_is_red = not self.my_is_red
            side = "红方" if opp_is_red else "黑方"
            self.update_suggest_text(
                f"已回退到对方回合。\n\n请点击棋盘输入对方（{side}）的走法。"
            )

        # 更新「手动输入」按钮可用性
        self._refresh_manual_btn()

    def _enter_manual_input(self):
        """回退 AI 刚下的我方走法，进入手动输入模式"""
        if not self.engine_running or not self.game_started or self.ai_thinking:
            return
        if self.manual_input_mode:
            return
        # 只在「对方回合」且「有历史」时才可用：说明上一步是我方（AI）走的
        if self._is_my_turn() or self._move_count() == 0:
            self.update_suggest_text("当前不能手动输入（需要 AI 先给出我方走法）。")
            return

        # 撤销最后一步（AI 给出的我方走法）
        self.move_history.undo_last_move()
        self.selected_piece = None
        self._rebuild_board_from_history()
        self._draw_all_pieces()

        # 同步引擎局面
        self.engine.set_position(self.move_history.get_moves_history())

        # 进入手动输入模式
        self.manual_input_mode = True
        side = "红方" if self.my_is_red else "黑方"
        self.add_history("✎ 已撤销 AI 走法，等待手动输入我方走法")
        self.update_suggest_text(
            f"手动输入模式：\n\n点击我方（{side}）棋子，\n再点击目标位置完成落子。"
        )

        self._refresh_manual_btn()

    def _refresh_manual_btn(self):
        """根据当前局面更新「手动输入」按钮可用性"""
        if not self.game_started or self.ai_thinking or self.manual_input_mode:
            self.manual_btn.config(state=tk.DISABLED)
            return
        # 对方回合 + 有历史 ⇒ 上一步是我方走的，可撤销改手动
        if not self._is_my_turn() and self._move_count() > 0:
            self.manual_btn.config(state=tk.NORMAL)
        else:
            self.manual_btn.config(state=tk.DISABLED)

    def _create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))

        # 标题
        title_label = ttk.Label(
            control_frame,
            text="象棋作弊系统",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        # 状态显示
        status_frame = ttk.LabelFrame(control_frame, text="系统状态", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.status_label = ttk.Label(
            status_frame,
            text="● 未启动",
            foreground="red",
            font=("Microsoft YaHei", 11)
        )
        self.status_label.pack()

        # 先手选择
        side_frame = ttk.LabelFrame(control_frame, text="先手选择", padding="10")
        side_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.side_var = tk.StringVar(value="my")
        ttk.Radiobutton(
            side_frame,
            text="我方先手（红方）",
            variable=self.side_var,
            value="my"
        ).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(
            side_frame,
            text="对方先手（红方）",
            variable=self.side_var,
            value="opponent"
        ).pack(anchor=tk.W, pady=2)

        # AI 建议显示
        suggest_frame = ttk.LabelFrame(control_frame, text="AI 建议", padding="10")
        suggest_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.suggest_text = tk.Text(
            suggest_frame,
            height=5,
            width=35,
            font=("Consolas", 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.suggest_text.pack(fill=tk.BOTH, expand=True)

        # 历史记录
        history_frame = ttk.LabelFrame(control_frame, text="历史走法", padding="10")
        history_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # 滚动条
        scrollbar = ttk.Scrollbar(history_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_text = tk.Text(
            history_frame,
            height=15,
            width=35,
            font=("Consolas", 9),
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            state=tk.DISABLED
        )
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_text.yview)

        # 按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(10, 0))

        self.begin_btn = ttk.Button(
            button_frame,
            text="开始对局",
            command=self._begin_game,
            width=15
        )
        self.begin_btn.grid(row=0, column=0, padx=5, pady=5)

        self.hint_btn = ttk.Button(
            button_frame,
            text="重算我方走法",
            command=self._show_hint,
            state=tk.DISABLED,
            width=15
        )
        self.hint_btn.grid(row=0, column=1, padx=5, pady=5)

        self.flip_btn = ttk.Button(
            button_frame,
            text="对调棋盘",
            command=self._flip_board,
            width=15
        )
        self.flip_btn.grid(row=1, column=0, padx=5, pady=5)

        self.undo_btn = ttk.Button(
            button_frame,
            text="回退一步",
            command=self._undo_move,
            state=tk.DISABLED,
            width=15
        )
        self.undo_btn.grid(row=1, column=1, padx=5, pady=5)

        self.manual_btn = ttk.Button(
            button_frame,
            text="手动输入我方",
            command=self._enter_manual_input,
            state=tk.DISABLED,
            width=15
        )
        self.manual_btn.grid(row=2, column=0, padx=5, pady=5)

        self.reset_btn = ttk.Button(
            button_frame,
            text="重置对局",
            command=self._reset_game,
            state=tk.DISABLED,
            width=15
        )
        self.reset_btn.grid(row=2, column=1, padx=5, pady=5)

        # 配置权重
        control_frame.rowconfigure(4, weight=1)

    def _flip_board(self):
        """对调棋盘上下方向并重绘"""
        self.flipped = not self.flipped
        self._draw_all_pieces()

    def _begin_game(self):
        """开始对局：启动引擎并按所选先手开始辅助（一键完成）"""
        if self.game_started:
            return

        # 锁定先手方（先手 = 红方）
        self.my_is_red = (self.side_var.get() == "my")

        # 引擎已经在跑（例如重置后再开局），直接进入开局流程
        if self.engine_running:
            self.engine.new_game()
            self._on_game_started()
            return

        # 首次开局：启动引擎
        self.begin_btn.config(state=tk.DISABLED)
        self.update_status("正在启动引擎...", "orange")

        def start_thread():
            try:
                self.engine = XiangqiEngine()
                if not self.engine.start():
                    self.root.after(0, lambda: messagebox.showerror(
                        "错误", "引擎启动失败！\n请确认 engine/pikafish.exe 存在。"
                    ))
                    self.root.after(0, lambda: self.begin_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.update_status("未启动", "red"))
                    return

                self.engine.new_game()
                self.engine_running = True
                self.root.after(0, self._on_game_started)

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"启动失败: {e}"))
                self.root.after(0, lambda: self.begin_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.update_status("启动失败", "red"))

        threading.Thread(target=start_thread, daemon=True).start()

    def _on_game_started(self):
        """引擎启动成功，正式开始对局"""
        self.game_started = True
        self.begin_btn.config(state=tk.DISABLED)
        self.hint_btn.config(state=tk.NORMAL)
        self.flip_btn.config(state=tk.NORMAL)
        self.reset_btn.config(state=tk.NORMAL)
        self.undo_btn.config(state=tk.NORMAL)

        self.update_status("对局进行中", "green")

        if self.my_is_red:
            self.add_history("对局开始：我方先手（红方），AI 正在计算开局...")
        else:
            self.add_history("对局开始：对方先手（红方），请输入对方第一步")

        # 根据当前局面推进回合
        self._advance_turn()

    def _ai_play_my_move(self):
        """AI 替我方计算并落子"""
        if not self.engine_running or self.ai_thinking:
            return

        self.ai_thinking = True
        self.update_suggest_text("AI 正在为我方计算最佳走法...")

        def analyze_thread():
            try:
                self.engine.set_position(self.move_history.get_moves_history())
                best_move, score = self.engine.get_best_move(depth=20, time_ms=3000)

                if best_move:
                    score_text = self._format_score(score)
                    self.root.after(0, lambda: self._apply_my_move(best_move, score_text))
                else:
                    self.root.after(0, lambda: self.update_suggest_text("未能获取建议"))
                    self.ai_thinking = False
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"分析失败: {e}"))
                self.ai_thinking = False

        threading.Thread(target=analyze_thread, daemon=True).start()

    def _apply_my_move(self, move: str, score_text: str):
        """落子：AI 给出的我方走法（在主线程执行）"""
        from_pos, to_pos = self._iccs_to_pos(move)

        # 执行移动
        self._execute_move(from_pos, to_pos, move)

        # 添加到历史
        self.move_history.add_move(move)
        self.add_history(f"[我方·AI建议] {move} ({score_text})")

        suggest_msg = (
            f"我方应走: {move}\n"
            f"评分: {score_text}\n"
            f"从 {move[:2]} 到 {move[2:]}\n\n"
            f"请在实际对局中走这一步，\n然后输入对方的应招。"
        )
        self.update_suggest_text(suggest_msg)

        self.ai_thinking = False

        # 推进到对方回合（等待手动输入）
        self._advance_turn()

    def _show_hint(self):
        """重新显示我方应走的提示（仅在我方回合可用）"""
        if not self.engine_running or not self.game_started or self.ai_thinking:
            return
        if not self._is_my_turn():
            self.update_suggest_text("当前是对方回合，请先输入对方的走法。")
            return

        # 我方回合：重新计算并落子
        self._ai_play_my_move()

    def _reset_game(self):
        """重置对局"""
        result = messagebox.askyesno("确认", "确定要重置对局吗？")
        if not result:
            return

        # 重置状态
        self.board_state.clear()
        self._init_board_state()
        self.move_history.reset()
        self.selected_piece = None
        self.last_move = None
        self.ai_thinking = False
        self.manual_input_mode = False

        # 清空显示
        self.update_suggest_text("")
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        self.history_text.config(state=tk.DISABLED)

        # 重新绘制
        self._draw_all_pieces()

        # 回到「未开始对局」状态，等待用户选先手并点「开始对局」
        self.game_started = False
        if self.engine_running:
            self.engine.new_game()

        # 按钮回到初始状态
        self.begin_btn.config(state=tk.NORMAL)
        self.hint_btn.config(state=tk.DISABLED)
        self.undo_btn.config(state=tk.DISABLED)
        self.manual_btn.config(state=tk.DISABLED)
        self.reset_btn.config(state=tk.DISABLED)

        self.update_status("已重置，请选择先手后点「开始对局」", "blue")
        self.add_history("对局已重置。请重新选择先手方，然后点击「开始对局」。")

    def update_status(self, text: str, color: str):
        """更新状态"""
        self.status_label.config(text=f"● {text}", foreground=color)

    def update_suggest_text(self, text: str):
        """更新建议文本"""
        self.suggest_text.config(state=tk.NORMAL)
        self.suggest_text.delete(1.0, tk.END)
        self.suggest_text.insert(tk.END, text)
        self.suggest_text.config(state=tk.DISABLED)

    def add_history(self, text: str):
        """添加历史记录"""
        self.history_text.config(state=tk.NORMAL)
        self.history_text.insert(tk.END, text + "\n")
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)

    def _format_score(self, score: int) -> str:
        """格式化评分"""
        value = score / 100
        if value > 0:
            return f"+{value:.2f}"
        else:
            return f"{value:.2f}"

    def _on_closing(self):
        """关闭窗口"""
        if self.engine and self.engine_running:
            self.engine.stop()
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = VisualXiangqiGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
