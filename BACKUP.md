# BACKUP MY Apps


## Homebrew

```bash
# backup
brew bundle dump --file=~/Brewfile --force

# restore
brew bundle install --file=~/Brewfile
```


## Visual Studio Code

```bash
# backup
code --list-extensions > vscode-extensions.txt

# restore
cat vscode-extensions.txt | xargs -n 1 code --install-extension 
```

