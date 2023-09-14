# NOVA Clippy (BETA)
by Afonso Brás Sousa

[![](https://img.shields.io/github/stars/abtsousa/nova-clippy)](https://github.com/abtsousa/nova-clippy/stargazers) [![](https://img.shields.io/github/license/abtsousa/nova-clippy)](https://github.com/abtsousa/nova-clippy/blob/master/LICENSE)

A simple web scraper and downloader for NOVA School of Science and Technology's internal e-learning platform, CLIP.

The program scrapes a user's courses for available downloads and syncs them with a local folder.

CLIP's files are organized in subcategories for each academic course like this:
Academic year >> Course documents >> Document subcategory >> Files list

Clippy successfully navigates the site in order to scrape it, and compares it to a local folder with a similar structure, keeping it in sync with the server.

```text
 __                 
/  \        _______________________ 
|  |       /                       \
@  @       | It looks like you     |
|| ||      | are downloading files |
|| ||   <--| from CLIP. Do you     |
|\_/|      | need assistance?      |
\___/      \_______________________/
```

## Install

**NOTE:** This program is in beta. [Star this repository](https://github.com/abtsousa/nova-clippy/stargazers) to support the project and be notified of updates!

[Python](https://www.python.org/downloads/) ≥ v3.8 must be installed.

Install with pip:

```pip install https://github.com/abtsousa/nova-clippy/archive/v0.9b2.zip```

**Report any bugs here or to `ab.sousa@campus.fct[...etc]`**. You can use the `--debug` option to generate a debug.log file that you can attach in the email.

## Usage

Usage: nova-clippy [OPTIONS] [PATH]

### Arguments

[PATH]  The folder where CLIP files will be stored. Will use current working directory if empty.

### Options

```text
--username        The user's username in CLIP.
--force-relogin   Ignores saved login credentials. [default: no-force-relogin]                                                                        │
--auto            Automatically chooses the latest year available. [default: auto]                                                                            │
--help            Show this message and exit.
```

## License and Copyright

GPL v3.

Clippy (c) 2023 Afonso Brás Sousa.

CLIP (c) 2023 FCT NOVA - Faculdade de Ciências e Tecnologia, 2829-516 Caparica, Portugal
