from rstem.button import Button

buttons = [Button(14), Button(15), Button(24), Button(23)]

while True:
    for button in buttons:
        if button.is_pressed():
            print("Button was pressed: ", button.pin)
        else:
            print("Button was released: ", button.pin)
