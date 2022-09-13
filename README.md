# cashu

**The author is NOT a cryptographer and has not tested the libraries used or the code nor has anyone reviewed the work. This means it's very likely a fatal flaw somewhere. This is meant only as educational and is not production ready.**

Ecash implementation based on David Wagner's variant of Chaumian blinding. Token logic based on [minicash](https://github.com/phyro/minicash) ([description](https://gist.github.com/phyro/935badc682057f418842c72961cf096c)) which implements a [Blind Diffie-Hellman Key Exchange](https://cypherpunks.venona.com/date/1996/03/msg01848.html) scheme written down by Ruben Somsen [here](https://gist.github.com/RubenSomsen/be7a4760dd4596d06963d67baf140406). The database mechanics and the Lightning backend is inspired by [LNbits](https://github.com/lnbits/lnbits-legend).

Big thanks to [phyro](https://github.com/phyro) for their work and further discussions and improvements.

## Install

```bash
git clone https://github.com/callebtc/cashu.git
sudo apt install -y build-essential pkg-config libffi-dev libpq-dev zlib1g-dev libssl-dev python3-dev
# on mac: brew install postgres

# install python using pyenv
curl https://pyenv.run | bash

    # put this in your ~/.bashrc
    export PYENV_ROOT="$HOME/.pyenv"
    command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"


source ~/.bashrc
pyenv install 3.9.13

# install poetry
curl -sSL https://install.python-poetry.org | python3 -

    # put this in your ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"

source ~/.bashrc

# install cashu
cd cashu
pyenv local 3.9.13
poetry install
```

## Run mint
```bash
poetry run uvicorn mint.app:app --port 3338
```
## Run wallet

```bash
poetry run ./cashu --wallet=wallet --mint=420
```

## Screenshot
![screenshot](https://user-images.githubusercontent.com/93376500/189533335-68a863e2-bacd-47c1-aecc-e4fb09883d11.jpg)
