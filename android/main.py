# SPDX-License-Identifier: GPL-3.0-only
"""Gabby's Tetris for Android, built with Kivy."""

from __future__ import annotations

import random
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle


__version__ = "1.0.0"

BOARD_WIDTH = 10
BOARD_HEIGHT = 20

BACKGROUND = "#10131f"
PANEL = "#171b2b"
GRID = "#252b3d"
TEXT = "#f4f6ff"
MUTED = "#8992ad"
ACCENT = "#8b7cff"
GREEN = "#61dc91"

PIECES: dict[str, tuple[str, tuple[tuple[int, ...], ...]]] = {
    "I": ("#50d8e8", ((0, 0, 0, 0), (1, 1, 1, 1), (0, 0, 0, 0), (0, 0, 0, 0))),
    "O": ("#ffd45a", ((0, 1, 1, 0), (0, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
    "T": ("#b879ff", ((0, 1, 0, 0), (1, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
    "S": ("#61dc91", ((0, 1, 1, 0), (1, 1, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
    "Z": ("#ff6b79", ((1, 1, 0, 0), (0, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
    "J": ("#6b9bff", ((1, 0, 0, 0), (1, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
    "L": ("#ffa05d", ((0, 0, 1, 0), (1, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
}


class MobileAudio:
    """Loads the game's bundled WAV music and effects when audio is available."""

    def __init__(self) -> None:
        self.enabled = True
        self.music = None
        self.effects = {}
        audio_dir = Path(__file__).parent
        try:
            self.music = SoundLoader.load(str(audio_dir / "music.wav"))
            if self.music:
                self.music.loop = True
                self.music.volume = 0.24
            for name in ("rotate", "drop", "lock", "clear"):
                sound = SoundLoader.load(str(audio_dir / f"{name}.wav"))
                if sound:
                    sound.volume = 0.45
                    self.effects[name] = sound
        except Exception:
            # Audio is optional; gameplay remains available if a device has no mixer.
            self.music = None
            self.effects = {}

    def start_music(self) -> None:
        if self.enabled and self.music:
            self.music.play()

    def toggle(self) -> None:
        self.enabled = not self.enabled
        if not self.music:
            return
        if self.enabled:
            self.music.play()
        else:
            self.music.stop()

    def play(self, name: str) -> None:
        sound = self.effects.get(name)
        if self.enabled and sound:
            sound.stop()
            sound.play()

    def pause_music(self, paused: bool) -> None:
        if not self.music:
            return
        if paused:
            self.music.stop()
        elif self.enabled:
            self.music.play()

    def close(self) -> None:
        if self.music:
            self.music.stop()
        for sound in self.effects.values():
            sound.stop()


class GameModel:
    """Tetris rules shared by the mobile view and its touch controls."""

    def __init__(self, on_change, audio: MobileAudio) -> None:
        self.on_change = on_change
        self.audio = audio
        self._tick_event = None
        self.reset(start_game=False, notify=False)

    @staticmethod
    def random_kind() -> str:
        return random.choice(tuple(PIECES))

    @staticmethod
    def rotate(matrix, clockwise: bool):
        if clockwise:
            return tuple(tuple(row) for row in zip(*matrix[::-1]))
        return tuple(tuple(row) for row in zip(*matrix))[::-1]

    def reset(self, start_game: bool = True, notify: bool = True) -> None:
        if self._tick_event is not None:
            self._tick_event.cancel()
            self._tick_event = None
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.started = start_game
        self.paused = False
        self.game_over = False
        self.next_kind = self.random_kind()
        self.spawn_piece()
        if self.started:
            self.audio.pause_music(False)
        if self.started:
            self.schedule_tick()
        if notify:
            self.on_change()

    def start(self) -> None:
        if self.started:
            return
        self.started = True
        self.audio.start_music()
        self.schedule_tick()
        self.on_change()

    def spawn_piece(self) -> None:
        self.kind = self.next_kind
        self.color, self.matrix = PIECES[self.kind]
        self.next_kind = self.random_kind()
        self.piece_x = 3
        self.piece_y = -1
        if self.collides(self.piece_x, self.piece_y, self.matrix):
            self.game_over = True

    def collides(self, x: int, y: int, matrix) -> bool:
        for row, values in enumerate(matrix):
            for col, filled in enumerate(values):
                if not filled:
                    continue
                board_x = x + col
                board_y = y + row
                if board_x < 0 or board_x >= BOARD_WIDTH or board_y >= BOARD_HEIGHT:
                    return True
                if board_y >= 0 and self.board[board_y][board_x] is not None:
                    return True
        return False

    def move(self, dx: int, dy: int) -> None:
        if not self.started or self.paused or self.game_over:
            return
        if not self.collides(self.piece_x + dx, self.piece_y + dy, self.matrix):
            self.piece_x += dx
            self.piece_y += dy
            if dy > 0:
                self.score += 1
            self.on_change()
        elif dy > 0:
            self.lock_piece()

    def hard_drop(self) -> None:
        if not self.started or self.paused or self.game_over:
            return
        distance = 0
        while not self.collides(self.piece_x, self.piece_y + 1, self.matrix):
            self.piece_y += 1
            distance += 1
        self.score += distance * 2
        self.audio.play("drop")
        self.lock_piece(play_sound=False)

    def rotate_piece(self, clockwise: bool) -> None:
        if not self.started or self.paused or self.game_over:
            return
        rotated = self.rotate(self.matrix, clockwise)
        for kick in (0, -1, 1, -2, 2):
            if not self.collides(self.piece_x + kick, self.piece_y, rotated):
                self.matrix = rotated
                self.piece_x += kick
                self.audio.play("rotate")
                self.on_change()
                return

    def clear_lines(self) -> int:
        remaining = [row for row in self.board if any(cell is None for cell in row)]
        cleared = BOARD_HEIGHT - len(remaining)
        self.board = [[None] * BOARD_WIDTH for _ in range(cleared)] + remaining
        return cleared

    def lock_piece(self, play_sound: bool = True) -> None:
        for row, values in enumerate(self.matrix):
            for col, filled in enumerate(values):
                if not filled:
                    continue
                board_x = self.piece_x + col
                board_y = self.piece_y + row
                if board_y < 0:
                    self.game_over = True
                    continue
                self.board[board_y][board_x] = self.color

        cleared = self.clear_lines()
        if cleared:
            self.score += (0, 100, 300, 500, 800)[cleared] * self.level
            self.lines += cleared
            self.level = self.lines // 10 + 1
            self.audio.play("clear")
        elif play_sound:
            self.audio.play("lock")

        if not self.game_over:
            self.spawn_piece()
        if self.game_over and self._tick_event is not None:
            self._tick_event.cancel()
            self._tick_event = None
        self.on_change()

    def toggle_pause(self) -> None:
        if not self.started or self.game_over:
            return
        self.paused = not self.paused
        self.audio.pause_music(self.paused)
        if self.paused and self._tick_event is not None:
            self._tick_event.cancel()
            self._tick_event = None
        elif not self.paused:
            self.schedule_tick()
        self.on_change()

    def schedule_tick(self) -> None:
        if self.started and not self.paused and not self.game_over:
            delay = max(0.08, (700 - (self.level - 1) * 55) / 1000)
            self._tick_event = Clock.schedule_once(self.tick, delay)

    def tick(self, _dt) -> None:
        self._tick_event = None
        if not self.started or self.paused or self.game_over:
            return
        if not self.collides(self.piece_x, self.piece_y + 1, self.matrix):
            self.piece_y += 1
        else:
            self.lock_piece()
        self.on_change()
        self.schedule_tick()


class RoundedPanel(BoxLayout):
    def __init__(self, color=PANEL, radius=dp(14), **kwargs):
        super().__init__(**kwargs)
        self._panel_color = Color(*get_color_from_hex(color))
        self._panel_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.before:
            self.canvas.before.add(self._panel_color)
            self.canvas.before.add(self._panel_bg)
        self.bind(pos=self._sync_panel, size=self._sync_panel)

    def _sync_panel(self, *_args):
        self._panel_bg.pos = self.pos
        self._panel_bg.size = self.size


class StatCard(RoundedPanel):
    def __init__(self, title: str, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=(dp(5), dp(6)),
            spacing=dp(1),
            **kwargs,
        )
        self.title_label = Label(
            text=title,
            color=get_color_from_hex(MUTED),
            font_size=sp(10),
            bold=True,
            size_hint_y=0.42,
        )
        self.value_label = Label(
            text="0",
            color=get_color_from_hex(TEXT),
            font_size=sp(17),
            bold=True,
            size_hint_y=0.58,
        )
        self.add_widget(self.title_label)
        self.add_widget(self.value_label)


class BoardWidget(Widget):
    def __init__(self, model: GameModel, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.bind(pos=self.redraw, size=self.redraw)

    def redraw(self, *_args):
        self.canvas.clear()
        if self.width <= 0 or self.height <= 0:
            return

        with self.canvas:
            Color(*get_color_from_hex(PANEL))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18)])

            cell = min(
                (self.width - dp(26)) / BOARD_WIDTH,
                (self.height - dp(26)) / BOARD_HEIGHT,
            )
            cell = max(dp(1), cell)
            board_w = cell * BOARD_WIDTH
            board_h = cell * BOARD_HEIGHT
            left = self.center_x - board_w / 2
            bottom = self.center_y - board_h / 2

            Color(*get_color_from_hex("#111522"))
            RoundedRectangle(
                pos=(left - dp(4), bottom - dp(4)),
                size=(board_w + dp(8), board_h + dp(8)),
                radius=[dp(8)],
            )
            Color(*get_color_from_hex(GRID))
            for column in range(BOARD_WIDTH + 1):
                x = left + column * cell
                Line(points=(x, bottom, x, bottom + board_h), width=dp(0.7))
            for row in range(BOARD_HEIGHT + 1):
                y = bottom + row * cell
                Line(points=(left, y, left + board_w, y), width=dp(0.7))

            model = self.model
            for row, values in enumerate(model.board):
                for col, color in enumerate(values):
                    if color:
                        self.draw_cell(left, bottom, cell, col, row, color)

            if not model.game_over:
                ghost_y = model.piece_y
                while not model.collides(model.piece_x, ghost_y + 1, model.matrix):
                    ghost_y += 1
                for row, values in enumerate(model.matrix):
                    for col, filled in enumerate(values):
                        board_y = ghost_y + row
                        if filled and board_y >= 0:
                            self.draw_cell(
                                left,
                                bottom,
                                cell,
                                model.piece_x + col,
                                board_y,
                                model.color,
                                ghost=True,
                            )
                for row, values in enumerate(model.matrix):
                    for col, filled in enumerate(values):
                        board_y = model.piece_y + row
                        if filled and board_y >= 0:
                            self.draw_cell(
                                left,
                                bottom,
                                cell,
                                model.piece_x + col,
                                board_y,
                                model.color,
                            )

    @staticmethod
    def draw_cell(left, bottom, cell, col, row, color, ghost=False):
        inset = max(dp(1), cell * 0.055)
        x = left + col * cell + inset
        y = bottom + (BOARD_HEIGHT - 1 - row) * cell + inset
        size = cell - 2 * inset
        rgba = get_color_from_hex(color)
        if ghost:
            rgba = (rgba[0], rgba[1], rgba[2], 0.20)
        Color(*rgba)
        RoundedRectangle(pos=(x, y), size=(size, size), radius=[max(dp(2), cell * 0.12)])
        if not ghost:
            Color(1, 1, 1, 0.20)
            Line(
                points=(x + inset, y + size - inset, x + size - inset, y + size - inset),
                width=max(1, dp(1)),
            )


class TetrisScreen(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*get_color_from_hex(BACKGROUND))
            self._background = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_background, size=self._sync_background)

        self.audio = MobileAudio()
        self.model = GameModel(self.refresh, self.audio)
        self._repeat_event = None
        self.stats = {}

        content = BoxLayout(
            orientation="vertical",
            padding=(dp(12), dp(9), dp(12), dp(10)),
            spacing=dp(8),
        )
        self.add_widget(content)

        header = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        title = Label(
            text="Gabby's Tetris",
            color=get_color_from_hex(TEXT),
            font_size=sp(21),
            bold=True,
            halign="left",
            valign="middle",
        )
        title.bind(size=lambda label, value: setattr(label, "text_size", value))
        header.add_widget(title)
        self.sound_button = self.make_button("♫", ACCENT, font_size=sp(22))
        self.sound_button.size_hint_x = None
        self.sound_button.width = dp(54)
        self.sound_button.bind(on_release=lambda *_: self.toggle_sound())
        header.add_widget(self.sound_button)
        content.add_widget(header)

        stats_row = GridLayout(cols=3, spacing=dp(8), size_hint_y=None, height=dp(58))
        for key, heading in (("score", "PUNTAJE"), ("lines", "LÍNEAS"), ("level", "NIVEL")):
            card = StatCard(heading)
            self.stats[key] = card
            stats_row.add_widget(card)
        content.add_widget(stats_row)

        self.board = BoardWidget(self.model, size_hint=(1, 1))
        content.add_widget(self.board)

        movement = GridLayout(cols=5, spacing=dp(6), size_hint_y=None, height=dp(58))
        button_specs = (
            ("◀", lambda: self.model.move(-1, 0), True),
            ("▼", lambda: self.model.move(0, 1), True),
            ("↺", lambda: self.model.rotate_piece(False), False),
            ("↻", lambda: self.model.rotate_piece(True), False),
            ("⤓", self.model.hard_drop, False),
        )
        for text, action, repeat in button_specs:
            button = self.make_button(text, GRID, font_size=sp(23))
            if repeat:
                button.bind(
                    on_press=lambda _button, callback=action: self.begin_repeat(callback),
                    on_release=lambda *_: self.stop_repeat(),
                )
            else:
                button.bind(on_release=lambda _button, callback=action: callback())
            movement.add_widget(button)
        content.add_widget(movement)

        actions = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(48))
        pause = self.make_button("PAUSA", "#252b3d", font_size=sp(13))
        pause.bind(on_release=lambda *_: self.model.toggle_pause())
        restart = self.make_button("REINICIAR", "#252b3d", font_size=sp(13))
        restart.bind(on_release=lambda *_: self.model.reset(start_game=True))
        actions.add_widget(pause)
        actions.add_widget(restart)
        content.add_widget(actions)

        self.overlay = RoundedPanel(
            orientation="vertical",
            padding=(dp(22), dp(18)),
            spacing=dp(9),
            size_hint=(0.86, None),
            height=dp(286),
            pos_hint={"center_x": 0.5, "center_y": 0.50},
            color="#1b2032",
        )
        self.overlay.opacity = 0
        self.overlay.disabled = True
        self.add_widget(self.overlay)
        self.overlay_icon = Image(
            source=str(Path(__file__).parent / "icon.png"),
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={"center_x": 0.5},
        )
        self.overlay.add_widget(self.overlay_icon)
        self.overlay_title = Label(
            text="Gabby's Tetris",
            color=get_color_from_hex(TEXT),
            font_size=sp(24),
            bold=True,
            size_hint_y=None,
            height=dp(38),
        )
        self.overlay.add_widget(self.overlay_title)
        self.overlay_message = Label(
            text="Un clásico de bloques, hecho para vos",
            color=get_color_from_hex(MUTED),
            font_size=sp(13),
            halign="center",
            valign="middle",
        )
        self.overlay_message.bind(
            size=lambda label, value: setattr(label, "text_size", value)
        )
        self.overlay.add_widget(self.overlay_message)
        self.overlay_button = self.make_button("JUGAR", ACCENT, font_size=sp(15))
        self.overlay_button.size_hint_y = None
        self.overlay_button.height = dp(50)
        self.overlay_button.bind(on_release=lambda *_: self.overlay_action())
        self.overlay.add_widget(self.overlay_button)

        self.refresh()

    def _sync_background(self, *_args):
        self._background.pos = self.pos
        self._background.size = self.size

    @staticmethod
    def make_button(text, color, font_size):
        button = Button(
            text=text,
            color=get_color_from_hex(TEXT),
            font_size=font_size,
            bold=True,
            background_normal="",
            background_down="",
            background_color=get_color_from_hex(color),
        )
        return button

    def begin_repeat(self, callback):
        self.stop_repeat()
        callback()
        self._repeat_event = Clock.schedule_interval(lambda _dt: callback(), 0.12)

    def stop_repeat(self):
        if self._repeat_event is not None:
            self._repeat_event.cancel()
            self._repeat_event = None

    def overlay_action(self):
        if self.model.game_over:
            self.model.reset(start_game=True)
        elif self.model.paused:
            self.model.toggle_pause()
        else:
            self.model.start()

    def toggle_sound(self):
        self.audio.toggle()
        self.sound_button.text = "♫" if self.audio.enabled else "♪̸"
        self.refresh()

    def refresh(self):
        if not hasattr(self, "stats"):
            return
        self.stats["score"].value_label.text = f"{self.model.score:,}".replace(",", ".")
        self.stats["lines"].value_label.text = str(self.model.lines)
        self.stats["level"].value_label.text = str(self.model.level)
        if hasattr(self, "board"):
            self.board.redraw()
        self.update_overlay()

    def update_overlay(self):
        if self.model.game_over:
            title, message, button = "FIN DEL JUEGO", "¡Buen intento! Puedes volver a jugar.", "VOLVER A JUGAR"
        elif self.model.paused:
            title, message, button = "PAUSA", "Cuando quieras, seguimos la partida.", "CONTINUAR"
        elif not self.model.started:
            title, message, button = "Gabby's Tetris", "Un clásico de bloques, hecho para vos.", "JUGAR"
        else:
            self.overlay.opacity = 0
            self.overlay.disabled = True
            return
        self.overlay_title.text = title
        self.overlay_message.text = message
        self.overlay_button.text = button
        self.overlay.opacity = 1
        self.overlay.disabled = False

    def on_pause(self):
        if self.model.started and not self.model.game_over and not self.model.paused:
            self.model.toggle_pause()
        return True

    def close(self):
        self.stop_repeat()
        self.model.reset(start_game=False, notify=False)
        self.audio.close()


class GabbysTetrisAndroidApp(App):
    title = "Gabby's Tetris"

    def build(self):
        self.screen = TetrisScreen()
        self.screen.audio.start_music()
        return self.screen

    def on_pause(self):
        if hasattr(self, "screen"):
            return self.screen.on_pause()
        return True

    def on_stop(self):
        if hasattr(self, "screen"):
            self.screen.close()


if __name__ == "__main__":
    GabbysTetrisAndroidApp().run()
