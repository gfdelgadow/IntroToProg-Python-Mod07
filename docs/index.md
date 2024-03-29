# Pickles and Exceptions
## Introduction
This python program captures user inputs and loads them into a binary file via pickling. The program then shows the user all of the data currently stored in the file. 
## Building The Script
**Step 1:** Gather user input data and place in list format.
```python
import pickle

# Gathering user inputs
name = str(input("Enter a friend's name: "))
age = int(input("Enter a friend's age: "))
lstAge = [name, age]
```

**Step 2:** Store data into binary file using pickle.dump method.
```python
# Storing data into binary file
objFile = open("Assignment07.dat", "ab")
pickle.dump(lstAge, objFile)
objFile.close()
```

**Step 3:** Read back pickled data in file via a list. Use try-except clause to pass end-of-file error.
```python
# Reading back pickled data in file
objFile = open("Assignment07.dat", "rb")
with objFile as f:
    unpickled = []
    while True:
        try:
            unpickled.append(pickle.load(f))
        except EOFError:  # use try-except clause to bypass end-of-file error
            break
print("Here are all of your inputs so far: ")
for row in unpickled:
    print(row)
```
***Program running in Pycharm***
![Program running in PyCharm](/../main/PyCharm.png)
***Program running in Terminal***
![Program running in Terminal](/../main/Terminal.png)

## Summary
In this assignment, I learned how to use pickling to reduce file size, and how to use try-except clauses to handle errors.
