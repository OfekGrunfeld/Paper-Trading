import os

relative_path = r"emails\sign_up\sign_up.html"
script_dir = os.path.dirname(__file__)
absolute_path = os.path.join(script_dir, relative_path)

text = None

with open(absolute_path, 'r') as file:
    text = file.read()

try:
    with open(absolute_path, 'w') as write_file:
        text1 = text.replace("linkadress", "botgabot")
        print(text1)
        write_file = text1
except Exception as error:
    print("Error: %s" % error)