if [ "$USER" = "root" ]; then
	apt-get update
	apt-get -y dist-upgrade
	apt-get -y autoremove wolfram-engine pistore dillo lxsession lxterminal lightdm scratch sonic-pi rsync cron triggerhappy #Remove uneeded programs 
	apt-get -y install chromium
	update-rc.d ssh enable
	echo "spi-dev\ni2c-dev" >> /etc/modules
	sed -i "s/^exit 0/sudo \/usr\/bin\/ideserver \&\nnetpd -gqx \&\nexit 0/" /etc/rc.local #Start IDE server and set time on boot
	update-rc.d -f ntp disable #Disable the time daemon, it's pointless on the Pi
	sed -i "s/1:2345:respawn:\/sbin\/getty --noclear 38400 tty1/1:2345:respawn:\/bin\/login -f root tty1 <\/dev\/tty1 >\/dev\/tty1 2>\&1/" /etc/inittab #Have TTY1 auto login to root
	echo '#!/bin/bash
if [[ -z $DISPLAY && $(tty) = /dev/tty1 ]]; then
        whiptail --title "IDE" --yesno "Launch the IDE?" 7 20
        if [ "$?" = "0" ]; then
                echo "chromium --disable-extensions --use-spdy=off --disable-pnacl --user-data-dir=.chromedata --kiosk 127.0.0.1 &" > .config/openbox/autostart
                startx
		exit 0
        fi
	cat /etc/null > .config/openbox/autostart
fi' > /root/.profile #Ask to boot into the IDE if there is no X server and they are in TTY1
	cat /dev/null > /etc/X11/default-display-manager #default-display-manager is lightdm, which was removed
	sed -i "s/^#disable_overscan/disable_overscan/" /boot/config.txt
	echo "gpu_mem=16" >> /boot/config.txt
	echo "en_US.UTF-8 UTF-8" > /etc/locale.gen
	export LANG="en_US.UTF-8"
	echo 'export LANG=en_US.UTF-8' >> /root/.bashrc
	echo 'export LANG=en_US.UTF-8' >> .bashrc
	sed -i 's/XKBLAYOUT="gb"/XKBLAYOUT="us"/' /etc/default/keyboard
	locale-gen
else
	echo "Run as root"
fi
