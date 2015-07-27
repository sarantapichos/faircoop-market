# faircoop-market
Faircoop market project

## How to participate
### Setup Git and generate your ssh keys
```
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR EMAIL ADDRESS"
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
eval "$(ssh-agent -s)"
```
Look at https://help.github.com/articles/set-up-git/ for more info

### Create a Github account
Create a github account and upload your public key (~/.ssh/id_rsa.pub)
For more info: https://help.github.com/articles/generating-ssh-keys/

###  Fork and commit ypur changes to your local repository
```
git clone git@github.com:<your name>/faircoop-market.git
#TODO: Database setup etc ...
vi ...
git status
git add
git commit
git push origin master
```


