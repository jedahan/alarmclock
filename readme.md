if you have one of those ALARMclock's from fig design, the service died years ago.

Here are some nice animations instead

displays - pins ??
  button - pins 12 & 14 (GPIO 18 + GND)
 speaker - pins ?? & ??

Install with:


    git clone github.com/jedahan/alarmclock
    cd alarmclock
    sudo pip3 install --requirement requirements.txt
    sudo cp blinkenlights.server /lib/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable blinkenlights
    sudo systemctl start blinkenlights
