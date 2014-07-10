sudo apt-get -y autoremove wolfram-engine lxsession lxterminal lightdm scratch sonic-pi rsync #Remove uneeded programs 
sudo apt-get -y install chromium
sed -i "s/exit 0\/sudo \/usr\/bin\/ideserver &\nnetpd -gqx &\nexit 0/" /etc/rc.local #Start IDE server and set time on boot
update-rc.d -f ntp disable #Disable the time daemon, it's pointless on the Pi
update-rc.d -f lightdm disable #Lightdm was removed, but the service remains
update-rc.d -f plymouth disable #Plymouth is uneeded
update-rc.d -f cron disable #Cron is uneeded
update-rc.d -f rsync disable #Rsync is uneeded
sed -i "s/1:2345:respawn:\/sbin\/getty --noclear 38400 tty1/1:2345:respawn:\/bin\/login -f root tty1 <\/dev\/tty1 >\/dev\/tty1 2>&1/" #Have TTY1 auto login to root
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
