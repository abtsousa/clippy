#  Clippy
## Um gestor de downloads para a plataforma CLIP da FCT-NOVA (BETA)
por Afonso Brás Sousa

[![](https://img.shields.io/github/stars/abtsousa/clippy)](https://github.com/abtsousa/clippy/stargazers) [![](https://img.shields.io/github/license/abtsousa/clippy)](https://github.com/abtsousa/clippy/blob/master/LICENSE)

<p align="center">
    <img src="clippy.png" style="width: 100px" alt="NOVA Clippy logo">
</p>

### 🇬🇧 [English version here / Clica aqui para ler a descrição em Inglês](README.md) 🇬🇧

O Clippy é um simples web scrapper e gestor de downloads para a plataforma interna de e-learning da FCT-NOVA, o CLIP.

O programa navega o CLIP à procura de ficheiros nas páginas das cadeiras de um utilizador e sincroniza-os com uma pasta local.

O CLIP está organizado em subcategorias para cada cadeira assim:
Ano >> Documentos da cadeira >> Subcategoria >> Ficheiros

O Clippy navega o site e compara os ficheiros disponíveis com uma pasta local, sincronizando-a com o servidor.

## Funcionalidades
- Extremamente rápido graças à sua execução assíncrona (permite verificar até 8 cadeiras ao mesmo tempo).
- Transfere múltiplos ficheiros (até 4 ficheiros em simultâneo).
- Sincronização automática de ficheiros entre o CLIP e a pasta do utilizador.
- Suporte para escolher qual o ano lectivo que pretende descarregar.
- Totalmente privado, gratuito e livre.

## Como instalar

**NOTA:** O programa está em beta. [Deixa uma estrela](https://github.com/abtsousa/clippy/stargazers) para apoiares o projecto e seres notificado de actualizações.

É necessário instalar o [Python](https://www.python.org/downloads/) ≥ v3.8.

Instala com o comando pip:

```pip install https://github.com/abtsousa/clippy/archive/v0.9b2.zip```

**Se encontrares *bugs* envia-os por aqui ou para o email académico `ab.sousa@campus.fct[...etc]`**. Usa a opção `--debug` para gerar um ficheiro debug.log que deves anexar ao email.

## Como usar

Na consola: `clippy [OPÇÕES] [CAMINHO]`

### Exemplos

- `clippy` Guarda os ficheiros numa subpasta CLIP no caminho actual.
- `clippy --force-relogin C:\CLIP` Ignora as credenciais guardadas e guarda os ficheiros na pasta C:\CLIP.
- `clippy --no-auto ~/CLIP` Deixa o utilizador escolher o ano que quer descarregar e guarda os ficheiros na pasta ~/CLIP.

### Argumentos

[PATH]  A pasta onde os ficheiros do CLIP serão guardados. Se estiver em branco usa a directoria actual.

### Opções

```text
 --username         O nome de utilizador no CLIP.
 --force-relogin    Ignora as credenciais guardadas em sistema.
 --auto             Escolhe automaticamente o ano lectivo mais recente.
 --help             Mostra esta mensagem de ajuda.
```

## Privacidade

As credenciais fornecidas são transmitidas apenas aos servidores do CLIP e podem opcionalmente ser guardadas no sistema local para facilitar o acesso futuro. O programa não estabelece ligação com servidores terceiros.

O autor do programa não obtém qualquer informação relativa ao utilizador ou a forma como usa o programa, nem mesmo para telemetria.

Este programa é fornecido "tal como está" e destina-se estritamente ao uso privado, limitado às suas funcionalidades de transferência de arquivos. Ao utilizar este programa, o utilizador concorda em isentar o autor de qualquer responsabilidade por danos ou consequências decorrentes de uso inadequado, incluindo, mas não se limitando a, bugs, erros de servidor ou uso indevido de funcionalidades não previstas inicialmente.

## Licença e Copyright

Clippy foi criado em 2023 por Afonso Brás Sousa, um estudante de Eng. Informática do 1º ano da FCT da Universidade NOVA de Lisboa.

Licenciado sob a GPL v3.

CLIP (c) 2023 FCT NOVA - Faculdade de Ciências e Tecnologia, 2829-516 Caparica, Portugal
