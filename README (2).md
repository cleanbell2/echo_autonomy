
Quickstart
1) Add one word
   python vocab_cli.py add

2) Import JSON from ChatGPT
   python vocab_cli.py import
   (paste JSON array) -> EOF
   - PowerShell/CMD: Ctrl+Z then Enter
   - mac/Linux: Ctrl+D

3) Export driving script (text)
   python vocab_cli.py export --max 20 --mark-reviewed
   -> commute_vocab.txt

4) Listen in the car
- Open commute_vocab.txt on your phone
- Use the system 'Read Aloud' / 'Speak Screen' feature

Tip
- Keep prompts short with PROMPT_TEMPLATES.txt
