#!/bin/bash
if [ "$USER" = "root" ]; then
	sudo apt-get update
	sudo apt-get -y dist-upgrade
	sudo apt-get -y autoremove --purge rsyslog
	sudo apt-get -y install dropbear openssh-client inetutils-syslogd
	sudo apt-get clean
	sed -i "/[3-6]:23:respawn:\/sbin\/getty 38400 tty[3-6]/s%^%#%g" /etc/inittab
	dpkg-reconfigure dash
	/etc/init.d/ssh stop
	sed -i "s/NO_START=1/NO_START=0/g" /etc/default/dropbear
	/etc/init.d/dropbear start
	update-rc.d ssh disable
	sed -i "s/defaults,noatime/defaults,noatime,nodiratime/g" /etc/fstab
	sed -i "s/deadline/noop/g" /boot/cmdline.txt
	service inetutils-syslogd stop
	for file in /var/log/*.log /var/log/mail.* /var/log/debug /var/log/syslog; do [ -f "$file" ] && rm -f "$file"; done
	for dir in fsck news; do [ -d "/var/log/$dir" ] && rm -rf "/var/log/$dir"; done
	service inetutils-syslogd start
	sudo rpi-update
	shutdown -r now
else
	echo "Run as root"
fi