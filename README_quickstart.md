# R2D Vocab Quickstart (Text Only)

## 1) Import JSON from GPT/Gemini (paste the JSON and finish with EOF)
```powershell
python vocab_cli.py import
```

## 2) Export a driving script (TXT)
```powershell
python vocab_cli.py export --out script.txt
```

## 3) Export + mark as reviewed (so next export only shows new words)
```powershell
python vocab_cli.py export --out script.txt --mark-reviewed
```

### Optional
- See new words: `python vocab_cli.py list`
- See due (SRS): `python vocab_cli.py list --due`
- Stats: `python vocab_cli.py stats`
