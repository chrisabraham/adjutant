# Contributing

Adjutant is an example more than a product, so the bar is: small, readable, tested.

- **Open an issue first** for anything bigger than a fix, so nobody writes a feature that won't fit.
- **A new phrasing?** Add it to `tests/phrases.tsv`, watch the replay test fail, then make it pass.
- **Keep the core on the standard library.** New dependencies need a very good reason.
- **Follow the rules in `AGENTS.md`.** They apply to people too.
- **Run both checks** before you open a pull request:
  ```sh
  python3 -m unittest discover -s tests
  python3 tools/release_check.py
  ```
- **Never include real people, clients, tokens or paths** in code, tests or issues. Use Dana, Sam, Lee and example.com.

By contributing you agree your work is released under the MIT license.
