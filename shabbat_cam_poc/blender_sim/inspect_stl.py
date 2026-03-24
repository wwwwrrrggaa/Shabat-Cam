import os, binascii
base = os.path.join(os.path.dirname(__file__), "M795 155mm shell with M782 fuze - 5428784", "files")
files = ['shell.stl', 'fuze.stl', 'shell_base.stl', 'shell_top.stl']
for f in files:
    p = os.path.join(base, f)
    print('FILE:', p)
    if not os.path.exists(p):
        print('  MISSING')
        continue
    s = os.stat(p).st_size
    print('  size=', s)
    with open(p, 'rb') as fh:
        head = fh.read(256)
    print('  first64_hex=', binascii.hexlify(head[:64]))
    # ASCII check
    try:
        txt = head.decode('utf-8', errors='ignore')
        preview = txt.strip()[:64]
        print('  head_text_preview=', repr(preview))
        if preview.lower().startswith('solid'):
            print('  detected ASCII STL (starts with solid)')
        else:
            print('  not ASCII header (likely binary STL)')
    except Exception as e:
        print('  decode error', e)

