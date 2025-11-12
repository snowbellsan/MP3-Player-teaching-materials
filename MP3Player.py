# -*- coding: utf-8 -*-
"""
学習用にコメントを丁寧に付けた簡易MP3プレイヤー（tkinter + pygame.mixer）
機能：
 - MP3ファイルを選んでロード
 - 再生 / 一時停止 / 再開 / 停止
 - ループ（連続再生）のトグル
 - 音量調整（スライダー）
 - 先頭へシーク、5秒位置へシーク（簡易）
注：このスクリプトは学習目的で詳しい説明コメントを多めに入れています。
"""

import tkinter as tk
from tkinter import filedialog     # ファイル選択ダイアログを使うため
from tkinter import ttk           # ttk.Scale（見た目の良いスライダー）
import pygame as pg               # 音声再生用。事前に `pip install pygame` が必要

# -------------------------
# 初期設定（モジュールの初期化）
# -------------------------
pg.mixer.init()               # pygame のミキサー（音声部分）を初期化する
# 注意: init が例外を出す場合は、サウンドデバイスの状態を確認してね

# 再生中のファイルパスを保存するための変数
current_file = None

# 状態フラグ（GUIの表示や処理の分岐で使う）
is_playing = False           # 再生中か（一時停止中は False）
is_looping = False           # ループ（連続再生）ON/OFF を管理するフラグ

# -------------------------
# ファイル操作・再生制御関数
# -------------------------

def open_file():
    """
    MP3ファイルをユーザーに選ばせてロードする関数。
    - filedialog.askopenfilename で選択させる
    - 選択があれば pygame.mixer.music.load() でファイルを読み込む
    - 音量を現在のスライダー位置に合わせる
    """
    global current_file
    file_path = filedialog.askopenfilename(
        defaultextension=".mp3",
        filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
    )
    # ファイルが選択された場合のみ処理する
    if file_path:
        current_file = file_path
        # pygame にファイルをロード（実際の再生は pg.mixer.music.play() で行う）
        pg.mixer.music.load(current_file)
        # UI にロードしたファイル名を表示（フルパスは長いので末尾だけ）
        file_label.config(text=f"ロード中: {current_file.split('/')[-1]}")
        # 読み込み時にスライダーの値を音量に反映しておく
        pg.mixer.music.set_volume(volume_scale.get() / 100.0)


def toggle_loop():
    """
    ループ（連続再生）の ON/OFF を切り替えるトグル関数。
    - is_looping フラグを反転
    - ボタンの表示（テキスト・見た目）を切り替える
    - 現在再生中なら、再生方法をループ / 非ループで切り替える（簡易対応）
    """
    global is_looping
    is_looping = not is_looping  # フラグをトグル

    # ループONの見た目にする
    if is_looping:
        loop_button.config(text="🔁 ループ: ON", relief=tk.SUNKEN, bg='lightblue')
        # もし現在再生中なら再生モードをループに切り替える（stop→playでやり直し）
        # 注意：現在の再生位置を安全に取得できないため、ここでは単純に再生をやり直す
        if pg.mixer.music.get_busy():
            pg.mixer.music.play(-1)  # -1 で無限ループ再生
    else:
        # ループOFFの見た目に戻す
        loop_button.config(text="▶️ ループ: OFF", relief=tk.RAISED, bg='SystemButtonFace')
        if pg.mixer.music.get_busy():
            # ループを解除するために一旦 play(0) で1回再生に切り替える
            # （実際は再生中の位置を正確に維持できない点に注意）
            pg.mixer.music.play(0)


def play_pause():
    """
    再生／一時停止を切り替える関数。
    - current_file が未選択なら警告を表示して何もしない
    - 再生していない→再生（ループ設定に応じて -1 または 0 を指定）
    - 再生中で is_playing True → 一時停止（pg.mixer.music.pause()）
    - pause 中で is_playing False → 再開（pg.mixer.music.unpause()）
    """
    global is_playing

    # ファイルがロードされていない場合は処理せず、UIに注意を出す
    if not current_file:
        file_label.config(text="⚠️ まずMP3ファイルを開いてください")
        return

    # 再生していない（かつ is_playing False）なら新規再生
    if not pg.mixer.music.get_busy() and not is_playing:
        # ループ設定に応じて play の loops 引数を設定する
        loops = -1 if is_looping else 0
        # 実際の再生開始
        pg.mixer.music.play(loops=loops)
        play_pause_button.config(text="一時停止")
        is_playing = True

    elif is_playing:
        # 再生中 -> 一時停止させる
        pg.mixer.music.pause()
        play_pause_button.config(text="再開")
        is_playing = False

    else:
        # 一時停止状態 -> 再開する
        pg.mixer.music.unpause()
        play_pause_button.config(text="一時停止")
        is_playing = True


def stop_music():
    """
    再生を完全に停止して曲を先頭に戻す処理。
    - pg.mixer.music.stop() は再生を止め、次回 play() で先頭からになる
    - is_playing フラグを False にする
    """
    global is_playing
    if pg.mixer.music.get_busy() or is_playing:
        pg.mixer.music.stop()
        play_pause_button.config(text="再生")
        is_playing = False


# -------------------------
# 音量・シーク操作
# -------------------------

def set_volume(val):
    """
    音量スライダーのコールバック。
    - ttk.Scale の command にセットされ、ユーザーがスライダーを動かしたときに呼ばれる
    - val は文字列で渡されることがあるので float に変換して 0.0-1.0 にする
    """
    volume = float(val) / 100.0
    pg.mixer.music.set_volume(volume)


def seek_forward_5():
    """
    曲の先頭から "5秒" の位置へシークして再生する簡易実装。
    - pygame.mixer.music には直接の「現在位置を+5秒」の簡単なAPIが無いことがあるので、
      この実装では一度 rewind() で先頭に戻し、start=5.0 で再生し直す手法を使っている。
    - 注意点：
      * start 引数はすべての環境/ファイル形式で動作する保証はない（デコーダ依存）。
      * より正確なシークをしたければ pydub や別のライブラリを検討する。
    """
    if current_file:
        pg.mixer.music.rewind()  # まず先頭に戻す（安全策）
        loops = -1 if is_looping else 0
        # start を指定して再生。失敗する環境もある点に注意。
        try:
            pg.mixer.music.play(loops=loops, start=5.0)
        except TypeError:
            # 古い pygame では start 引数がサポートされないことがあるため例外処理
            # その場合は単純に play() しておく（5秒シークは行われない）
            pg.mixer.music.play(loops=loops)
        play_pause_button.config(text="一時停止")
        global is_playing
        is_playing = True
        file_label.config(text=f"5秒へシーク: {current_file.split('/')[-1]}")


def seek_to_start():
    """
    曲の先頭（0秒）にシークする簡易実装。
    - rewind() で先頭に戻すだけ。再生中なら再生を続ける（先頭から）。
    """
    if current_file:
        pg.mixer.music.rewind()
        file_label.config(text=f"先頭に戻る: {current_file.split('/')[-1]}")
        # 再生中なら先頭から再生を続ける（ループ設定に応じてplay）
        if is_playing:
            loops = -1 if is_looping else 0
            try:
                pg.mixer.music.play(loops=loops, start=0.0)
            except TypeError:
                pg.mixer.music.play(loops=loops)


# -------------------------
# GUI（tkinter）構築
# -------------------------

# メインウィンドウの初期化
root = tk.Tk()
root.title("簡易MP3プレイヤー (Python) - 学習用")
root.geometry("400x320")   # ウィンドウサイズを指定（幅x高さ）

# ファイル名表示用ラベル（wraplength で長いテキストの折返しを指定）
file_label = tk.Label(root, text="MP3ファイルを開いてください", wraplength=350, justify='center')
file_label.pack(pady=10)

# ボタン類をまとめるフレーム（レイアウト整理）
control_frame = tk.Frame(root)
control_frame.pack(pady=10)

# 「ファイルを開く」ボタン：open_file() を呼ぶ
open_button = tk.Button(control_frame, text="ファイルを開く", command=open_file)
open_button.pack(side=tk.LEFT, padx=5)

# 「再生 / 一時停止」ボタン：play_pause() を呼ぶ
play_pause_button = tk.Button(control_frame, text="再生", command=play_pause)
play_pause_button.pack(side=tk.LEFT, padx=5)

# 「停止」ボタン：stop_music() を呼ぶ
stop_button = tk.Button(control_frame, text="停止", command=stop_music)
stop_button.pack(side=tk.LEFT, padx=5)

# ループトグルボタン（単体で配置）
loop_button = tk.Button(root, text="▶️ ループ: OFF", command=toggle_loop, relief=tk.RAISED)
loop_button.pack(pady=10)

# --- 音量調整関連 ---
volume_label = tk.Label(root, text="音量:")
volume_label.pack(pady=(10, 0))

# ttk.Scale を使ったスライダー（from_=0 to=100）
volume_scale = ttk.Scale(
    root,
    from_=0,
    to=100,
    orient='horizontal',
    command=set_volume,
    length=300
)
volume_scale.set(50)  # 初期音量を 50% に設定
volume_scale.pack(pady=5)

# --- シーク関連ボタン（先頭へ、5秒へ） ---
seek_frame = tk.Frame(root)
seek_frame.pack(pady=10)

seek_start_button = tk.Button(seek_frame, text="⏪ 先頭へ", command=seek_to_start)
seek_start_button.pack(side=tk.LEFT, padx=10)

seek_5s_button = tk.Button(seek_frame, text="⏩ 5秒へシーク", command=seek_forward_5)
seek_5s_button.pack(side=tk.LEFT, padx=10)

# メインループを開始（GUIの実行）
# tkinter のイベントループが終了するまでここで待機する
root.mainloop()

# アプリ終了時に pygame のミキサーもクリーンアップする
pg.mixer.quit()
