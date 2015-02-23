from rstem.button import Button

buttons = [Button(14), Button(15), Button(24), Button(23)]

button = button[2]
if button.is_pressed():
    print("Button was pressed: ", button.pin)
else:
    print("Button was released: ", button.pin)
