# Pickles and Exceptions
## Introduction
This python program captures user inputs and loads them into a binary file via pickling. The program then shows the user all of the data currently stored in the file. 
## Building The Script
**Step 1:** Gather user input data and place in list format.
```
import pickle

# Gathering user inputs
name = str(input("Enter a friend's name: "))
age = int(input("Enter a friend's age: "))
lstAge = [name, age]
```
