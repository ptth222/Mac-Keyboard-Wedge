# -*- mode: python -*-

block_cipher = None


a = Analysis(['Keyboard_Wedge.py'],
             pathex=['/Users/higashi/Keyboard_Wedge'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='Keyboard_Wedge',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )
app = BUNDLE(exe,
             name='Keyboard_Wedge.app',
             icon=None,
             bundle_identifier=None,
             info_plist={
		'NSHighResolutionCapable': 'True'
		},
	     )
