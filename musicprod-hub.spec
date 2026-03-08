# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for MusicProd Hub — produces a single-file Windows exe.
#
# Build:
#   pip install pyinstaller
#   pyinstaller musicprod-hub.spec
#
# The resulting binary is written to dist/musicprod-hub.exe.

block_cipher = None

a = Analysis(
    ["musicprod/hub.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Core package
        "musicprod",
        "musicprod.cli",
        "musicprod.hub",
        "musicprod.tools",
        "musicprod.tools.updater",
        # All tool modules (imported lazily inside the hub)
        "musicprod.tools.audio_compressor",
        "musicprod.tools.audio_merger",
        "musicprod.tools.audio_normalizer",
        "musicprod.tools.audio_splitter",
        "musicprod.tools.audio_trimmer",
        "musicprod.tools.bpm_detector",
        "musicprod.tools.channel_converter",
        "musicprod.tools.chord_detector",
        "musicprod.tools.fade_effect",
        "musicprod.tools.format_converter",
        "musicprod.tools.key_detector",
        "musicprod.tools.loop_creator",
        "musicprod.tools.metadata_editor",
        "musicprod.tools.noise_reducer",
        "musicprod.tools.pitch_shifter",
        "musicprod.tools.reverb_effect",
        "musicprod.tools.silence_remover",
        "musicprod.tools.tempo_changer",
        "musicprod.tools.vocal_autotune",
        "musicprod.tools.volume_adjuster",
        "musicprod.tools.waveform_plotter",
        "musicprod.tools.youtube_to_mp3",
        # GUI toolkit
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.scrolledtext",
        # Runtime stdlib modules used by the updater
        "json",
        "tempfile",
        "urllib.request",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="musicprod-hub",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # Windowed GUI — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
