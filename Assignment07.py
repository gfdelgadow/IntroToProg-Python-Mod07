# ------------------------------------------------------------------------ #
# Title: Assignment 07
# Description: Pickling and Exceptions
# ChangeLog (Who,When,What):
# GDW,8.24.2021, Created script
# ------------------------------------------------------------------------ #
import pickle

# Gathering user inputs
name = str(input("Enter a friend's name: "))
age = int(input("Enter a friend's age: "))
lstAge = [name, age]

# Storing data into binary file
objFile = open("Assignment07.dat", "ab")
pickle.dump(lstAge, objFile)
objFile.close()

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
