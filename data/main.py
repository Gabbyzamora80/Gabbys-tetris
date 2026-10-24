# SPDX-License-Identifier: GPL-3.0-only
"""Gabby's Tetris: a small cross-platform Tetris game built with Tkinter."""

from __future__ import annotations

import math
import random
from array import array
import tkinter as tk
from tkinter import font as tkfont


CELL = 30
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
BOARD_X = 24
BOARD_Y = 24
PANEL_X = BOARD_X + BOARD_WIDTH * CELL + 24
WINDOW_WIDTH = 510
WINDOW_HEIGHT = 680

BACKGROUND = "#10131f"
BOARD_BACKGROUND = "#171b2b"
GRID = "#252b3d"
TEXT = "#f4f6ff"
MUTED = "#8992ad"
ACCENT = "#8b7cff"

# The 4x4 matrices make rotation predictable and keep the rules easy to follow.
PIECES: dict[str, tuple[str, tuple[tuple[int, ...], ...]]] = {
    "I": ("#50d8e8", ((0, 0, 0, 0), (1, 1, 1, 1), (0, 0, 0, 0), (0, 0, 0, 0))),
    "O": ("#ffd45a", ((0, 1, 1, 0), (0, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
    "T": ("#b879ff", ((0, 1, 0, 0), (1, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
    "S": ("#61dc91", ((0, 1, 1, 0), (1, 1, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
    "Z": ("#ff6b79", ((1, 1, 0, 0), (0, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
    "J": ("#6b9bff", ((1, 0, 0, 0), (1, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
    "L": ("#ffa05d", ((0, 0, 1, 0), (1, 1, 1, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
}


class AudioManager:
    """Optional pygame audio with short, procedurally generated chiptune sounds."""

    SAMPLE_RATE = 22050
    MELODY = (
        659, 494, 523, 587, 523, 494, 440, 440,
        523, 659, 587, 523, 494, 494, 523, 587,
        659, 523, 440, 440, 523, 587, 659, 587,
        523, 494, 523, 587, 659, 523, 440, 440,
    )

    def __init__(self) -> None:
        self.pygame = None
        self.available = False
        self.music_enabled = True
        self.music_channel = None
        self.music_sound = None
        self.sounds: dict[str, object] = {}
        try:
            import pygame

            pygame.mixer.init(
                frequency=self.SAMPLE_RATE, size=-16, channels=1, buffer=512
            )
            pygame.mixer.set_num_channels(12)
            pygame.mixer.set_reserved(1)
            self.pygame = pygame
            self.available = True
            self.music_channel = pygame.mixer.Channel(0)
            self.music_sound = self._make_music()
            self.sounds = {
                "rotate": self._make_tone((660, 880), 0.055, 0.16),
                "drop": self._make_tone((420, 300, 190), 0.055, 0.20),
                "lock": self._make_tone((250,), 0.075, 0.13),
                "clear": self._make_tone((660, 830, 990, 1320), 0.075, 0.18),
            }
            self.music_channel.set_volume(0.28)
        except Exception:
            # Audio devices and pygame may be unavailable; the game itself still works.
            if self.pygame:
                try:
                    self.pygame.mixer.quit()
                except Exception:
                    pass
            self.pygame = None
            self.available = False
            self.music_channel = None
            self.music_sound = None
            self.sounds = {}

    def _make_tone(self, notes: tuple[int, ...], duration: float, volume: float):
        samples = array("h")
        note_length = int(self.SAMPLE_RATE * duration)
        for frequency in notes:
            for index in range(note_length):
                fade_in = min(1.0, index / (self.SAMPLE_RATE * 0.004))
                fade_out = min(1.0, (note_length - index) / (self.SAMPLE_RATE * 0.018))
                envelope = min(fade_in, fade_out)
                phase = 2 * math.pi * frequency * index / self.SAMPLE_RATE
                wave = 1.0 if math.sin(phase) >= 0 else -1.0
                samples.append(int(wave * volume * envelope * 32767))
        return self.pygame.mixer.Sound(buffer=samples)

    def _make_music(self):
        samples = array("h")
        beat_length = int(self.SAMPLE_RATE * 0.17)
        bass_notes = (220, 196, 174, 196, 220, 262, 196, 174)
        for beat, frequency in enumerate(self.MELODY):
            bass = bass_notes[(beat // 4) % len(bass_notes)]
            for index in range(beat_length):
                fade = min(
                    1.0,
                    index / (self.SAMPLE_RATE * 0.006),
                    (beat_length - index) / (self.SAMPLE_RATE * 0.012),
                )
                time = index / self.SAMPLE_RATE
                lead = 1.0 if math.sin(2 * math.pi * frequency * time) >= 0 else -1.0
                low = 1.0 if math.sin(2 * math.pi * bass * time) >= 0 else -1.0
                samples.append(int((lead * 0.72 + low * 0.28) * 0.10 * fade * 32767))
        return self.pygame.mixer.Sound(buffer=samples)

    def start_music(self) -> None:
        if self.pygame and self.music_enabled and self.music_channel:
            self.music_channel.play(self.music_sound, loops=-1)

    def toggle_music(self) -> None:
        self.music_enabled = not self.music_enabled
        if not self.pygame or not self.music_channel:
            return
        if self.music_enabled:
            self.start_music()
        else:
            self.music_channel.stop()

    def pause_music(self, paused: bool) -> None:
        if not self.music_channel:
            return
        if paused:
            self.music_channel.pause()
        elif self.music_enabled:
            self.music_channel.unpause()

    def play(self, effect: str) -> None:
        sound = self.sounds.get(effect)
        if sound is not None:
            sound.play()

    def close(self) -> None:
        if self.pygame:
            self.pygame.mixer.quit()


class GabbysTetris:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Gabby's Tetris")
        self.root.configure(bg=BACKGROUND)
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.pack(padx=12, pady=12)

        self.font_title = tkfont.Font(family="Arial", size=21, weight="bold")
        self.font_welcome = tkfont.Font(family="Arial", size=34, weight="bold")
        self.font_heading = tkfont.Font(family="Arial", size=10, weight="bold")
        self.font_value = tkfont.Font(family="Arial", size=19, weight="bold")
        self.font_small = tkfont.Font(family="Arial", size=9)
        self.font_button = tkfont.Font(family="Arial", size=12, weight="bold")

        self.audio = AudioManager()
        self.audio.start_music()

        self.root.bind_all("<Left>", lambda event: self.move(-1, 0))
        self.root.bind_all("<Right>", lambda event: self.move(1, 0))
        self.root.bind_all("<Down>", lambda event: self.soft_drop())
        self.root.bind_all("<Up>", lambda event: self.rotate_clockwise())
        self.root.bind_all("x", lambda event: self.rotate_clockwise())
        self.root.bind_all("X", lambda event: self.rotate_clockwise())
        self.root.bind_all("z", lambda event: self.rotate_counterclockwise())
        self.root.bind_all("Z", lambda event: self.rotate_counterclockwise())
        self.root.bind_all("<space>", lambda event: self.hard_drop())
        self.root.bind_all("p", lambda event: self.toggle_pause())
        self.root.bind_all("P", lambda event: self.toggle_pause())
        self.root.bind_all("r", lambda event: self.restart())
        self.root.bind_all("R", lambda event: self.restart())
        self.root.bind_all("<Return>", lambda event: self.start_game())
        self.root.bind_all("m", lambda event: self.toggle_music())
        self.root.bind_all("M", lambda event: self.toggle_music())
        self.canvas.bind("<Button-1>", self.handle_click)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.after_id: str | None = None
        self.restart(start_game=False)

    def restart(self, start_game: bool = True) -> None:
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.board: list[list[str | None]] = [
            [None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)
        ]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.started = start_game
        self.paused = False
        self.game_over = False
        self.audio.pause_music(False)
        self.next_kind = self.random_kind()
        self.spawn_piece()
        self.draw()
        if self.started:
            self.schedule_tick()

    def start_game(self) -> None:
        if self.started:
            return
        self.started = True
        self.draw()
        self.schedule_tick()

    def toggle_music(self) -> None:
        self.audio.toggle_music()
        if self.paused and self.audio.music_enabled:
            self.audio.pause_music(True)
        self.draw()

    def handle_click(self, event: tk.Event) -> None:
        if not self.started:
            if 155 <= event.x <= 355 and 326 <= event.y <= 390:
                self.start_game()
            elif 155 <= event.x <= 355 and 412 <= event.y <= 452:
                self.toggle_music()
        elif PANEL_X <= event.x <= PANEL_X + 132 and 630 <= event.y <= 666:
            self.toggle_music()

    def close(self) -> None:
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        self.audio.close()
        self.root.destroy()

    @staticmethod
    def random_kind() -> str:
        return random.choice(tuple(PIECES))

    def spawn_piece(self) -> None:
        self.kind = self.next_kind
        self.color, self.matrix = PIECES[self.kind]
        self.next_kind = self.random_kind()
        self.piece_x = 3
        self.piece_y = -1
        if self.collides(self.piece_x, self.piece_y, self.matrix):
            self.game_over = True

    def collides(
        self, x: int, y: int, matrix: tuple[tuple[int, ...], ...]
    ) -> bool:
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

    @staticmethod
    def rotate(matrix: tuple[tuple[int, ...], ...], clockwise: bool):
        if clockwise:
            return tuple(tuple(row) for row in zip(*matrix[::-1]))
        return tuple(tuple(row) for row in zip(*matrix))[::-1]

    def move(self, dx: int, dy: int) -> None:
        if not self.started or self.paused or self.game_over:
            return
        if not self.collides(self.piece_x + dx, self.piece_y + dy, self.matrix):
            self.piece_x += dx
            self.piece_y += dy
            if dy > 0:
                self.score += 1
            self.draw()
        elif dy > 0:
            self.lock_piece()

    def soft_drop(self) -> None:
        self.move(0, 1)

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
        # Small horizontal kicks let pieces rotate beside walls and stacks.
        for kick in (0, -1, 1, -2, 2):
            if not self.collides(self.piece_x + kick, self.piece_y, rotated):
                self.matrix = rotated
                self.piece_x += kick
                self.audio.play("rotate")
                self.draw()
                return

    def rotate_clockwise(self) -> None:
        self.rotate_piece(True)

    def rotate_counterclockwise(self) -> None:
        self.rotate_piece(False)

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
        self.draw()
        if self.game_over and self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def clear_lines(self) -> int:
        remaining = [row for row in self.board if any(cell is None for cell in row)]
        cleared = BOARD_HEIGHT - len(remaining)
        self.board = [[None] * BOARD_WIDTH for _ in range(cleared)] + remaining
        return cleared

    def toggle_pause(self) -> None:
        if not self.started or self.game_over:
            return
        self.paused = not self.paused
        if self.paused and self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.audio.pause_music(self.paused)
        self.draw()
        if not self.paused:
            self.schedule_tick()

    def schedule_tick(self) -> None:
        if not self.paused and not self.game_over:
            delay = max(80, 700 - (self.level - 1) * 55)
            self.after_id = self.root.after(delay, self.tick)

    def tick(self) -> None:
        self.after_id = None
        if not self.paused and not self.game_over:
            if not self.collides(self.piece_x, self.piece_y + 1, self.matrix):
                self.piece_y += 1
            else:
                self.lock_piece()
            self.draw()
            self.schedule_tick()

    def draw_cell(self, x: int, y: int, color: str, size: int = CELL) -> None:
        inset = 2 if size >= 20 else 1
        self.canvas.create_rectangle(
            x + inset,
            y + inset,
            x + size - inset,
            y + size - inset,
            fill=color,
            outline="",
        )
        if size >= 20:
            self.canvas.create_line(
                x + 5, y + 4, x + size - 5, y + 4, fill="#ffffff", width=1
            )

    def draw(self) -> None:
        canvas = self.canvas
        canvas.delete("all")
        if not self.started:
            self.draw_welcome()
            return

        canvas.create_text(
            BOARD_X,
            5,
            anchor="nw",
            text="Gabby's Tetris",
            fill=TEXT,
            font=self.font_title,
        )

        board_top = BOARD_Y + 39
        board_bottom = board_top + BOARD_HEIGHT * CELL
        canvas.create_rectangle(
            BOARD_X,
            board_top,
            BOARD_X + BOARD_WIDTH * CELL,
            board_bottom,
            fill=BOARD_BACKGROUND,
            outline="#343b52",
            width=2,
        )
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                color = self.board[row][col]
                x = BOARD_X + col * CELL
                y = board_top + row * CELL
                if color:
                    self.draw_cell(x, y, color)
                else:
                    canvas.create_rectangle(
                        x,
                        y,
                        x + CELL,
                        y + CELL,
                        outline=GRID,
                        width=1,
                    )

        if not self.game_over:
            for row, values in enumerate(self.matrix):
                for col, filled in enumerate(values):
                    if not filled:
                        continue
                    board_y = self.piece_y + row
                    if board_y >= 0:
                        self.draw_cell(
                            BOARD_X + (self.piece_x + col) * CELL,
                            board_top + board_y * CELL,
                            self.color,
                        )

        canvas.create_text(
            PANEL_X,
            43,
            anchor="nw",
            text="SIGUIENTE",
            fill=MUTED,
            font=self.font_heading,
        )
        preview_x, preview_y, preview_size = PANEL_X, 66, 24
        canvas.create_rectangle(
            preview_x,
            preview_y,
            preview_x + 132,
            preview_y + 112,
            fill=BOARD_BACKGROUND,
            outline="#343b52",
        )
        next_color, next_matrix = PIECES[self.next_kind]
        for row, values in enumerate(next_matrix):
            for col, filled in enumerate(values):
                if filled:
                    self.draw_cell(
                        preview_x + 18 + col * preview_size,
                        preview_y + 8 + row * preview_size,
                        next_color,
                        preview_size,
                    )

        self.draw_stat("PUNTAJE", f"{self.score:,}".replace(",", "."), 210)
        self.draw_stat("LÍNEAS", str(self.lines), 292)
        self.draw_stat("NIVEL", str(self.level), 374)

        controls_y = 470
        canvas.create_text(
            PANEL_X,
            controls_y,
            anchor="nw",
            text="CONTROLES",
            fill=MUTED,
            font=self.font_heading,
        )
        controls = (
            "← →   Mover",
            "↓       Bajar",
            "↑ / X   Girar",
            "Z       Girar al otro lado",
            "ESPACIO  Caída rápida",
            "P       Pausa",
            "R       Reiniciar",
        )
        for index, line in enumerate(controls):
            canvas.create_text(
                PANEL_X,
                controls_y + 24 + index * 19,
                anchor="nw",
                text=line,
                fill=TEXT,
                font=self.font_small,
            )

        music_label = "MÚSICA: ON" if self.audio.music_enabled else "MÚSICA: OFF"
        canvas.create_rectangle(
            PANEL_X,
            630,
            PANEL_X + 132,
            662,
            fill="#252b3d",
            outline=ACCENT,
            width=1,
        )
        canvas.create_text(
            PANEL_X + 66,
            646,
            text=music_label,
            fill=TEXT,
            font=self.font_small,
        )

        if self.paused or self.game_over:
            canvas.create_rectangle(
                BOARD_X + 18,
                board_top + 225,
                BOARD_X + BOARD_WIDTH * CELL - 18,
                board_top + 350,
                fill="#10131f",
                outline=ACCENT,
                width=2,
            )
            heading = "FIN DEL JUEGO" if self.game_over else "PAUSA"
            subheading = "Presiona R para volver a jugar" if self.game_over else "Presiona P para continuar"
            canvas.create_text(
                BOARD_X + BOARD_WIDTH * CELL // 2,
                board_top + 270,
                text=heading,
                fill=TEXT,
                font=self.font_heading,
            )
            canvas.create_text(
                BOARD_X + BOARD_WIDTH * CELL // 2,
                board_top + 302,
                text=subheading,
                fill=MUTED,
                font=self.font_small,
            )

    def draw_welcome(self) -> None:
        canvas = self.canvas
        center_x = WINDOW_WIDTH // 2
        canvas.create_text(
            center_x,
            104,
            text="Gabby's Tetris",
            fill=TEXT,
            font=self.font_welcome,
        )
        canvas.create_text(
            center_x,
            151,
            text="Un clásico de bloques, hecho para vos",
            fill=MUTED,
            font=self.font_small,
        )

        # Small falling-block motif for the welcome screen.
        motif = ((0, 1, "#50d8e8"), (1, 1, "#50d8e8"), (2, 1, "#50d8e8"),
                 (1, 0, "#50d8e8"), (4, 1, "#ffd45a"), (4, 2, "#ffd45a"),
                 (5, 1, "#ffd45a"), (5, 2, "#ffd45a"), (7, 2, "#b879ff"),
                 (6, 3, "#b879ff"), (7, 3, "#b879ff"), (8, 3, "#b879ff"))
        motif_x, motif_y, motif_size = 153, 209, 26
        for col, row, color in motif:
            self.draw_cell(
                motif_x + col * motif_size,
                motif_y + row * motif_size,
                color,
                motif_size,
            )

        canvas.create_rectangle(
            155,
            326,
            355,
            390,
            fill=ACCENT,
            outline="",
        )
        canvas.create_text(
            center_x,
            358,
            text="JUGAR",
            fill=TEXT,
            font=self.font_button,
        )

        canvas.create_rectangle(
            155,
            412,
            355,
            452,
            fill="#252b3d",
            outline=ACCENT,
            width=1,
        )
        if self.audio.available:
            music_label = "Música: ACTIVADA" if self.audio.music_enabled else "Música: DESACTIVADA"
        else:
            music_label = "Audio requiere pygame"
        canvas.create_text(
            center_x,
            432,
            text=music_label,
            fill=TEXT if self.audio.available else MUTED,
            font=self.font_small,
        )

        canvas.create_text(
            center_x,
            495,
            text="← → mover     ↓ bajar     ↑ / X / Z girar",
            fill=TEXT,
            font=self.font_small,
        )
        canvas.create_text(
            center_x,
            521,
            text="ESPACIO caída rápida     P pausa     M música",
            fill=TEXT,
            font=self.font_small,
        )
        canvas.create_text(
            center_x,
            613,
            text="Pulsa JUGAR o ENTER para comenzar",
            fill=MUTED,
            font=self.font_small,
        )

    def draw_stat(self, label: str, value: str, y: int) -> None:
        self.canvas.create_text(
            PANEL_X,
            y,
            anchor="nw",
            text=label,
            fill=MUTED,
            font=self.font_heading,
        )
        self.canvas.create_text(
            PANEL_X,
            y + 20,
            anchor="nw",
            text=value,
            fill=TEXT,
            font=self.font_value,
        )


def main() -> None:
    root = tk.Tk()
    GabbysTetris(root)
    root.mainloop()


if __name__ == "__main__":
    main()
