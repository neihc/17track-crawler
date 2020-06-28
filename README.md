# Prerequisites:
- Python3.7
- pipenv
- Google chrome
- chromedriver (Find suitable version [here](https://chromedriver.chromium.org/))

# Installation
## 1. Install TOR

For MAC OS X, install it via brew
```bash
brew update
brew install tor
```

For Linux, install via APT
```bash
sudo apt-get update
sudo apt-get install tor
sudo /etc/init.d/tor restart
```

*Notice that the socks listener is on port 9050.*

Next, do the following:
- Enable the ControlPort listener for Tor to listen on port 9051, as this is the port to which Tor will listen for any communication from applications talking to the Tor controller.
- Hash a new password that prevents random access to the port by outside agents.
- Implement cookie authentication as well.

You can create a hashed password out of your password using:
```shell
tor --hash-password my_password
```

Then, update the `/usr/local/etc/tor/torrc` (`/etc/tor/torrc` if linux) with the port, hashed password, and cookie authentication.
```shell
# content of torrc
ControlPort 9051
# hashed password below is obtained via `tor --hash-password my_password`
HashedControlPassword 16:E600ADC1B52C80BB6022A0E999A7734571A451EB6AE50FED489B72E3DF
CookieAuthentication 1
```

Restart Tor again to the configuration changes are applied.	
```shell
# mac os
brew services restart tor
# linux
sudo /etc/init.d/tor restart
```

## 2. Install dependencies
Install all dependency packages by running:
```
pipenv install
```

After that, create a .env file for your own:
```
cp .env.example .env
```

Edit .env file to suitable with your environment.

# Usage
```
pipenv run cli_runner --input_path=data/tracking_number.txt --output_path=data/result.json
```
