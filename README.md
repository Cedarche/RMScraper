Step 1 - Download the code as zip file (top right where it says <> Code)

Step 2 - Unzip the folder, right click and select 'New terminal at folder' 

Step 3 - In the terminal type ```python -V``` if it's 3.10 or above you should be fine, then type ```pip -V``` to make sure you have both python and pip installed (if those don't work try python3 and pip3 in the commands instead).

Step 4 - In the terminal type the command ```python -m venv venv```. Once that finished type ```source venv/bin/activate``` to activate a virtual environment. 

Step 5 - Type the command ```pip install -r requirements.txt``` to install all the required libraries (try pip3 if that doesnt work).

Step 6 - Run the command ```python app.py```. In the terminal you should get a url that looks like http://127.0.0.1:5500

Step 7 - Paste the url into your browser, click the button and wait for the file to download. Any issues will appear in the terminal.
