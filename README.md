# Fairmarket
Fairmarket: the key project in the new global economic ecosystem we want to build

FairCoop is an open global cooperative, self-organized via the Internet and remaining outside nation-state control.
Its aim is to make the transition to a new world by reducing the  economic and social inequalities among human beings as much as possible,  and at the same time gradually contribute to a new global wealth,  accessible to all humankind as commons.
 
FairCoop understands that the transformation to a fairer monetary system is a key element. Therefore, Faircoin was proposed as the  cryptocurrency upon which to base its resource-redistribution actions  and building of a new global economic system.
To read more about FairCoop: https://fair.coop/


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

### Setup for running FairMarket which runs on Odoo

First, make sure sudo is installed. Our work user will need it. If logged in as  root :
apt-get update && apt-get upgrade  # Install system updates
apt-get install sudo  # Make sure 'sudo' is installed
The following commands will create an  odoo  user:
useradd -m -g sudo -s /bin/bash odoo  # Create an 'Odoo' user with sudo 
powers
passwd odoo  # Ask and set a password for the new user
You can change  odoo  to whatever username you want. The  -m  option has its home
directory created. The  -g sudo  adds it to the sudoers list, so it can run commands as root,
and the  -s /bin/bash  sets the default shell to  bash , which is nicer to use than the default
sh .
Ready-to-install Odoo packages can be found at nightly.odoo.com, available as Windows
( .exe ), Debian ( .deb ), CentOS ( .rpm ), and source code tarballs ( .tar.gz ).
As developers, we will prefer installing directly from the GitHub repository. This will end
up giving us more control over versions and updates.
To keep things tidy, let’s work in an  /odoo-dev  directory inside your home directory.
Throughout the book, we will assume this is where your Odoo server is installed.
First, make sure you are logged in as the user created above, or during the installation
process, and not as root. Assuming your user is  odoo , you can confirm this with the
following command:
whoami
odoo
echo $HOME
/home/odoo
Now we can use this script. It shows us how to install Odoo from source in a Debian
system:
sudo apt-get update && sudo apt-get upgrade  # Install system updates
sudo apt-get install git  # Install Git
mkdir ~/odoo-dev  # Create a directory to work in
cd ~/odoo-dev  # Go into our work directory

###  Fork fairmarket and clone
git clone git@github.com:<your name>/faircoop-market.git  # Get Fairmarket source code
./odoo/odoo.py setup_deps  # Installs Odoo system dependencies
./odoo/odoo.py setup_pg  # Installs PostgreSQL & db superuser for unix 
user
At the end, Odoo should be ready to be used. The  ~  symbol is a shortcut for your home
directory (for example,  /home/odoo ).

### Set up Odoo for Fairmarket

Now we can log in as the new user and set up Odoo.
1) Command line:
1. createdb odoodb (To make a database in postgresql).
2. Createdb odootestdb
3. Download from here: https://doc-10-30-docs.googleusercontent.com/docs/securesc/ha0ro937gcuc7l7deffksulhg5h7mbp1/4ff98gmgpu0cooclqcitsg0qp3234j73/1437040800000/01881337457757338427/*/0B7KSDUOJa1RjaWw1azFjaDE5d28?e=download
4. psql -f pg_dumpall_FairMarket odoodb (To restore the database to postgresql). The dump is attached in the zip.

2) This is the route where you install odoo if you followed the odoo development essentials cap 1 1. Getting Started with Odoo Development /home/odoo/odoo-dev/odoo/, extract the addons.zip inside the addons folder.

Now you can work with the local FairMarket. 

http://127.0.0.1:8069

You can login with the following users:

admin (administrator).

FairMarket@fairmarket.net (owner of the company FairMarketDocumenter for testing).

Password for the users: Fair.

```
