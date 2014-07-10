#!/bin/bash
sudo apt-get update
sudo apt-get -y dist-upgrade
sudo apt-get -y autoremove --purge rsyslog
sudo apt-get -y install dropbear openssh-client inetutils-syslogd
sudo apt-get clean
sed -i '/[3-6]:23:respawn:\/sbin\/getty 38400 tty[2-6]/s%^%#%g' /etc/inittab #Dsable getty
dpkg-reconfigure dash #Replace Bash with Dash
/etc/init.d/ssh stop #Stop SSH
sed -i 's/NO_START=1/NO_START=0/g' /etc/default/dropbear #Enable dropbear on boot
/etc/init.d/dropbear start #Start dropbear
update-rc.d ssh disable #Stop SSH on boot
sed -i 's/defaults,noatime/defaults,noatime,nodiratime/g' /etc/fstab #Optimize mounting
sed -i 's/deadline/noop/g' /boot/cmdline.txt #Switch to better scheduler
service inetutils-syslogd stop #Stop the logging daemon
##Delete old logs##
for file in /var/log/*.log /var/log/mail.* /var/log/debug /var/log/syslog; do [ -f "$file" ] && rm -f "$file"; done
for dir in fsck news; do [ -d "/var/log/$dir" ] && rm -rf "/var/log/$dir"; done
####
echo -e "*.*;mail.none;cron.none\t -/var/log/messages\ncron.*\t -/var/log/cron\nmail.*\t -/var/log/mail" > /etc/syslog.conf #Create a basic config
mkdir -p /etc/logrotate.d
echo -e "/var/log/cron\n/var/log/mail\n/var/log/messages {\n\trotate 4\n\tweekly\n\tmissingok\n\tnotifempty\n\tcompress\n\tsharedscripts\n\tpostrotate\n\t/etc/init.d/inetutils-syslogd reload >/dev/null\n\tendscript\n}" > /etc/logrotate.d/inetutils-syslogd #Create a basic logrotate config
service inetutils-syslogd start #Start the new daemon
sudo rpi-update
shutdown -r now
